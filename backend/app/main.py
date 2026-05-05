from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import httpx
import os
import logging

from . import models, schemas, database, auth

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Ecommerce Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://pagos:8002")

# --- User Auth ---

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = auth.get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create empty cart for user
    db_cart = models.Cart(user_id=db_user.id)
    db.add(db_cart)
    db.commit()
    return db_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.get_user(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
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
            models.Product(title="Laptop Pro", description="High end laptop", price=1200.0, image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&q=80&w=400"),
            models.Product(title="Smartphone X", description="Latest smartphone", price=800.0, image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&q=80&w=400"),
            models.Product(title="Wireless Headphones", description="Noise cancelling", price=250.0, image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&q=80&w=400")
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
async def checkout(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
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
        payment_payload = {
            "id_usuario": current_user.id,
            "descripcion": f"Order #{order.id}",
            "monto": float(total_amount),
            "email_pagador": current_user.email
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{PAYMENT_SERVICE_URL}/pagos/crear", json=payment_payload)
            response.raise_for_status()
            payment_data = response.json()
            
            # The payment service will return data with init_point and preference_id
            order.payment_id = str(payment_data.get("data", {}).get("id_pago"))
            order.status = "processing"
            url_pago = payment_data.get("data", {}).get("url_pago")
            
    except Exception as e:
        logging.error(f"Error calling payment service: {e}")
        raise HTTPException(status_code=502, detail="Error con Mercado Pago. Probablemente el MP_ACCESS_TOKEN es inválido o de prueba.")
        
    # In a full flow: we clear the cart
    cart.is_active = False
    db.commit()
    db.refresh(order)
    
    return schemas.CheckoutResponse(order=order, url_pago=url_pago)
