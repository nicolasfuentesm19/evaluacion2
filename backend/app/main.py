import os
import logging
import random
import string
from datetime import datetime
import boto3
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import httpx

from pydantic import BaseModel
from . import models, schemas, database, auth

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Ecommerce Backend API")

@app.get("/api/health")
def read_root():
    return {"message": "Ecommerce Backend API is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://pagos:8002")

NOTIFICACIONES_URL = os.getenv("NOTIFICACIONES_URL", "http://notificaciones:8003")
AUDITORIA_URL = os.getenv("AUDITORIA_URL", "http://auditoria:8004")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "evaluacion2-archivos-app")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

import threading

def log_audit_event(user_email: str, event_type: str, description: str, ip_address: str = None):
    """Fire-and-forget audit log using a background thread (works in both sync and async endpoints)"""
    def _send():
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.post(
                    f"{AUDITORIA_URL}/events/",
                    json={
                        "user_email": user_email,
                        "event_type": event_type,
                        "description": description,
                        "ip_address": ip_address
                    }
                )
                response.raise_for_status()
        except Exception as e:
            logging.error(f"Error logging audit event via HTTP (fallback to DB): {e}")
            try:
                from sqlalchemy import create_engine, text
                from datetime import datetime
                engine = create_engine(os.getenv("DATABASE_URL"))
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO audit_events (timestamp, user_email, event_type, description, ip_address)
                        VALUES (:ts, :email, :tipo, :desc, :ip)
                    """), {
                        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "email": user_email,
                        "tipo": event_type,
                        "desc": description,
                        "ip": ip_address or "0.0.0.0"
                    })
                    conn.commit()
            except Exception as db_e:
                logging.error(f"Error logging audit event via DB fallback: {db_e}")
    threading.Thread(target=_send, daemon=True).start()

def get_s3_client():
    return boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

# --- User Auth ---

@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, request: Request, db: Session = Depends(database.get_db)):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    db_user = auth.get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    verification_code = ''.join(random.choices(string.digits, k=6))
    
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        is_verified=False,
        verification_code=verification_code
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create empty cart for user
    db_cart = models.Cart(user_id=db_user.id)
    db.add(db_cart)
    db.commit()
    
    # Send verification email via Notificaciones service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICACIONES_URL}/email/verify",
                json={"email": db_user.email, "code": verification_code}
            )
            logging.info(f"Notification service response: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending verification email: {e}")
        # We don't block registration if email fails, but in production we should handle this
    
    log_audit_event(db_user.email, "Registro", "Usuario registrado exitosamente", client_ip)
    
    return db_user

@app.post("/users/verify")
def verify_user(req: schemas.UserVerify, request: Request, db: Session = Depends(database.get_db)):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    db_user = auth.get_user(db, email=req.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.is_verified:
        return {"message": "User already verified"}
    if db_user.verification_code != req.code:
        log_audit_event(req.email, "Error Validacion", "Intento de validacion fallido por codigo incorrecto", client_ip)
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    db_user.is_verified = True
    db.commit()
    log_audit_event(req.email, "Validacion", "Cuenta validada exitosamente", client_ip)
    return {"message": "User successfully verified"}

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    user = auth.get_user(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        log_audit_event(form_data.username, "Error Login", "Intento de inicio de sesion fallido", client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        log_audit_event(form_data.username, "Error Login", "Intento de inicio de sesion de cuenta no verificada", client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please check your email for the verification code.",
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    log_audit_event(user.email, "Login", "Inicio de sesion exitoso", client_ip)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- Products ---

@app.get("/products/", response_model=list[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    # Auto-populate some products if empty for demo purposes
    if not products:
        demo_products = [
            models.Product(title="Laptop Pro", description="Computadora portátil de alta gama", price=1200.0, image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&q=80&w=400"),
            models.Product(title="Smartphone X", description="Teléfono inteligente de última generación", price=800.0, image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&q=80&w=400"),
            models.Product(title="Audífonos Inalámbricos", description="Cancelación de ruido activa", price=250.0, image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&q=80&w=400")
        ]
        db.add_all(demo_products)
        db.commit()
        products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- Cart ---

@app.get("/cart/", response_model=schemas.Cart)
def get_cart(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id, models.Cart.is_active == True).first()
    if not cart:
        cart = models.Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@app.post("/cart/items/", response_model=schemas.Cart)
def add_to_cart(item: schemas.CartItemCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id, models.Cart.is_active == True).first()
    if not cart:
        cart = models.Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        
    db_item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == item.product_id).first()
    if db_item:
        db_item.quantity += item.quantity
    else:
        db_item = models.CartItem(cart_id=cart.id, product_id=item.product_id, quantity=item.quantity)
        db.add(db_item)
    db.commit()
    db.refresh(cart)
    return cart

@app.delete("/cart/items/{product_id}", response_model=schemas.Cart)
def remove_from_cart(product_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id, models.Cart.is_active == True).first()
    if cart:
        db_item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == product_id).first()
        if db_item:
            db.delete(db_item)
            db.commit()
            db.refresh(cart)
    return cart

# --- Checkout / Payment Integration ---

@app.post("/checkout/", response_model=schemas.CheckoutResponse)
async def checkout(request: Request, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id, models.Cart.is_active == True).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    total_amount = sum(item.product.price * item.quantity for item in cart.items)
    
    # 1. Create order as pending
    order = models.Order(user_id=current_user.id, total_amount=total_amount, status="pending")
    db.add(order)
    db.commit()
    db.refresh(order)
    
    url_pago = None
    
    # 2. Call Payment Microservice
    try:
        # Use S3 Frontend URL for success redirection
        # We MUST use the HTTPS S3 URL here because MercadoPago rejects HTTP urls for back_urls
        success_url = "https://evaluacion2-archivos-app.s3.amazonaws.com/index.html"
        
        payment_payload = {
            "id_usuario": current_user.id,
            "descripcion": f"Order #{order.id}",
            "monto": float(total_amount),
            "email_pagador": current_user.email,
            "success_url": success_url
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{PAYMENT_SERVICE_URL}/pagos/crear", json=payment_payload)
            response.raise_for_status()
            payment_data = response.json()
            
            # The payment service will return data with init_point and preference_id
            # Save the preference_id so we can look it up later when MP redirects the user back
            order.payment_id = str(payment_data.get("data", {}).get("preference_id"))
            order.status = "processing"
            url_pago = payment_data.get("data", {}).get("url_pago")
            
    except Exception as e:
        logging.error(f"Error calling payment service: {e}")
        raise HTTPException(status_code=502, detail="Error con Mercado Pago. Probablemente el MP_ACCESS_TOKEN es inválido o de prueba.")
        
    # In a full flow: we clear the cart
    cart.is_active = False
    db.commit()
    db.refresh(order)
    
    log_audit_event(current_user.email, "Compra", f"Orden #{order.id} creada por {total_amount}", client_ip)
    
    return schemas.CheckoutResponse(order=order, url_pago=url_pago)

class CheckoutConfirmRequest(BaseModel):
    preference_id: str
    collection_id: str
    status: str

@app.post("/checkout/confirm")
async def checkout_confirm(
    payload: CheckoutConfirmRequest,
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    if payload.preference_id:
        order = db.query(models.Order).filter(
            models.Order.user_id == current_user.id,
            models.Order.payment_id == payload.preference_id
        ).first()
    else:
        # Fallback to the latest pending order if preference_id is missing
        order = db.query(models.Order).filter(
            models.Order.user_id == current_user.id,
            models.Order.status == 'pending'
        ).order_by(models.Order.id.desc()).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for confirmation")
        
    if payload.status == "approved" and order.status != "paid":
        order.status = "paid"
        order.payment_id = payload.collection_id # Update to real transaction ID
        db.commit()
        db.refresh(order)
        
        # Now send the confirmation email containing the rubric details
        # The email template in Notificaciones expects products, we can reconstruct or fetch them
        # Wait, the order doesn't have an items relationship in this simple model, 
        # so we'll just send a generic summary for now, or find the inactive cart.
        cart = db.query(models.Cart).filter(
            models.Cart.user_id == current_user.id, 
            models.Cart.is_active == False
        ).order_by(models.Cart.id.desc()).first()
        
        products_data = []
        if cart and cart.items:
            products_data = [{"title": item.product.title, "quantity": item.quantity, "price": item.product.price} for item in cart.items]
        else:
            products_data = [{"title": "Productos de E-Commerce", "quantity": 1, "price": order.total_amount}]

        log_audit_event(current_user.email, "Pago Procesado", f"Pago de la orden #{order.id} aprobado por {order.total_amount}", client_ip)

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{NOTIFICACIONES_URL}/email/purchase",
                    json={
                        "email": current_user.email,
                        "name": current_user.email.split("@")[0],
                        "order_id": order.id,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "products": products_data,
                        "total": float(order.total_amount)
                    }
                )
        except Exception as e:
            logging.error(f"Error sending purchase email: {e}")
            
    return {"message": "Order confirmed", "status": order.status}

# --- File Management (S3) ---

MAX_SPACE_BYTES = 2 * 1024 * 1024 * 1024 # 2 GB

@app.get("/files/", response_model=list[schemas.UserFile])
def get_user_files(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    files = db.query(models.UserFile).filter(models.UserFile.user_id == current_user.id).all()
    return files

@app.get("/files/space", response_model=schemas.SpaceResponse)
def get_user_space(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    files = db.query(models.UserFile).filter(models.UserFile.user_id == current_user.id).all()
    used_bytes = sum(f.size_bytes for f in files)
    available_bytes = MAX_SPACE_BYTES - used_bytes
    return {
        "used_bytes": used_bytes,
        "available_bytes": available_bytes,
        "used_mb": round(used_bytes / (1024 * 1024), 2),
        "available_mb": round(available_bytes / (1024 * 1024), 2)
    }

@app.post("/files/upload", response_model=schemas.UserFile)
async def upload_file(
    request: Request,
    file: UploadFile = File(...), 
    phone_number: str = Form(None), # Option for SMS
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    # Check space
    files = db.query(models.UserFile).filter(models.UserFile.user_id == current_user.id).all()
    used_bytes = sum(f.size_bytes for f in files)
    
    file_content = await file.read()
    file_size = len(file_content)
    
    if used_bytes + file_size > MAX_SPACE_BYTES:
        raise HTTPException(status_code=400, detail="Not enough space. 2GB limit reached.")
        
    s3_key = f"user_{current_user.id}/{file.filename}"
    
    # Upload to S3
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content
        )
    except Exception as e:
        logging.error(f"Error uploading to S3: {e}")
        raise HTTPException(status_code=500, detail="Error uploading file to storage")
        
    # Save to DB
    db_file = models.UserFile(
        user_id=current_user.id,
        filename=file.filename,
        s3_key=s3_key,
        size_bytes=file_size,
        upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Call notificaciones for SMS if phone_number is provided
    if phone_number:
        new_used = used_bytes + file_size
        new_avail = MAX_SPACE_BYTES - new_used
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{NOTIFICACIONES_URL}/sms/upload",
                    json={
                        "phone_number": phone_number,
                        "filename": file.filename,
                        "date": db_file.upload_date,
                        "used_space": f"{round(new_used / (1024*1024), 2)} MB",
                        "available_space": f"{round(new_avail / (1024*1024), 2)} MB"
                    }
                )
        except Exception as e:
            logging.error(f"Error sending SMS: {e}")
            
    log_audit_event(current_user.email, "Archivo", f"Archivo {file.filename} subido a S3", client_ip)
            
    return db_file

@app.get("/audit-events")
def get_audit_events(
    event_type: str = None,
    user_email: str = None,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    # Query the audit_events table directly (shared RDS with auditoria microservice)
    try:
        from sqlalchemy import text
        query = "SELECT id, timestamp, user_email, event_type, description, ip_address FROM audit_events"
        conditions = []
        params = {}
        if event_type:
            conditions.append("event_type = :event_type")
            params["event_type"] = event_type
        if user_email:
            conditions.append("user_email ILIKE :user_email")
            params["user_email"] = f"%{user_email}%"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC LIMIT :limit"
        params["limit"] = limit
        result = db.execute(text(query), params)
        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "user_email": row[2],
                "event_type": row[3],
                "description": row[4],
                "ip_address": row[5]
            }
            for row in rows
        ]
    except Exception as e:
        logging.error(f"Error fetching audit events from DB: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando auditoría: {str(e)}")

# --- Serve Frontend SPA ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check if static directory exists (it will be created by CI/CD)
if not os.path.exists("static"):
    os.makedirs("static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Ignore API paths if they somehow fall through
    if full_path.startswith("users") or full_path.startswith("products") or full_path.startswith("cart") or full_path.startswith("checkout") or full_path.startswith("files") or full_path.startswith("audit-events") or full_path.startswith("token"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    static_path = os.path.join("static", full_path)
    if os.path.isfile(static_path):
        return FileResponse(static_path)
    
    # Fallback to index.html for Angular routing
    index_path = os.path.join("static", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
        
    return {"message": "Frontend not yet built or copied"}
