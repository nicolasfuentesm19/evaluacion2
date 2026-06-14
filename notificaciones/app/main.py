import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from twilio.rest import Client
from .schemas import EmailVerifyRequest, EmailPurchaseRequest, EmailPaymentRequest, SmsUploadRequest

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Microservicio de Notificaciones")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL", "nicolasfuentesm19@gmail.com")

def get_ses_client():
    return boto3.client(
        'ses',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

def get_sns_client():
    return boto3.client(
        'sns',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

def send_email(to_address: str, subject: str, body_html: str):
    client = get_ses_client()
    try:
        response = client.send_email(
            Destination={'ToAddresses': [to_address]},
            Message={
                'Body': {'Html': {'Charset': 'UTF-8', 'Data': body_html}},
                'Subject': {'Charset': 'UTF-8', 'Data': subject},
            },
            Source=SENDER_EMAIL,
        )
        return response
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/verify")
def send_verification_email(req: EmailVerifyRequest):
    subject = "Verifica tu cuenta - Evaluacion 2"
    body = f"""
    <html>
        <body>
            <h2>¡Hola!</h2>
            <p>Gracias por registrarte. Tu código de verificación es: <strong>{req.code}</strong></p>
            <p>Por favor, ingrésalo en la plataforma para activar tu cuenta.</p>
        </body>
    </html>
    """
    send_email(req.email, subject, body)
    return {"message": "Verification email sent"}

@app.post("/email/purchase")
def send_purchase_email(req: EmailPurchaseRequest):
    subject = f"Confirmación de compra #{req.order_id}"
    products_html = "".join([f"<li>{p['quantity']}x {p['title']} - ${p['price']}</li>" for p in req.products])
    body = f"""
    <html>
        <body>
            <h2>¡Hola {req.name}!</h2>
            <p>Tu compra #{req.order_id} realizada el {req.date} ha sido registrada.</p>
            <h3>Detalle:</h3>
            <ul>{products_html}</ul>
            <p><strong>Total pagado: ${req.total}</strong></p>
        </body>
    </html>
    """
    send_email(req.email, subject, body)
    return {"message": "Purchase email sent"}

@app.post("/email/payment")
def send_payment_email(req: EmailPaymentRequest):
    subject = f"Pago confirmado: {req.transaction_id}"
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #fafafa; color: #111827; padding: 40px 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; border: 1px solid #e4e4e7; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
            .header {{ text-align: center; border-bottom: 1px solid #e4e4e7; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ font-size: 24px; font-weight: 700; letter-spacing: -0.5px; color: #111827; margin: 0; }}
            h2 {{ color: #10b981; font-weight: 600; font-size: 20px; margin-top: 10px; }}
            .details {{ background: #f4f4f5; border-radius: 8px; padding: 20px; margin-bottom: 30px; }}
            .details-row {{ display: flex; justify-content: space-between; border-bottom: 1px dashed #d4d4d8; padding: 12px 0; font-size: 14px; }}
            .details-row:last-child {{ border-bottom: none; padding-bottom: 0; }}
            .label {{ color: #6b7280; }}
            .value {{ font-weight: 600; text-align: right; }}
            .total-row {{ font-size: 18px; font-weight: 700; padding-top: 15px; margin-top: 15px; border-top: 2px solid #e4e4e7; display: flex; justify-content: space-between; }}
            .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <p class="logo">E-COMMERCE</p>
                <h2>¡Pago Procesado Exitosamente!</h2>
                <p style="color: #6b7280; font-size: 14px;">Tu transacción ha sido aprobada por Mercado Pago.</p>
            </div>
            
            <div class="details">
                <div class="details-row">
                    <span class="label">ID de Transacción</span>
                    <span class="value">{req.transaction_id}</span>
                </div>
                <div class="details-row">
                    <span class="label">Fecha</span>
                    <span class="value">{req.date}</span>
                </div>
                <div class="details-row">
                    <span class="label">Estado</span>
                    <span class="value" style="color: #10b981;">{req.status.upper()}</span>
                </div>
                <div class="details-row">
                    <span class="label">Resumen</span>
                    <span class="value">{req.summary}</span>
                </div>
                <div class="total-row">
                    <span>Monto Total Pagado</span>
                    <span>${req.amount}</span>
                </div>
            </div>

            <div class="footer">
                <p>Este comprobante es generado automáticamente por el microservicio de notificaciones de AWS.</p>
                <p>&copy; 2026 E-Commerce Platform. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(req.email, subject, body)
    return {"message": "Payment email sent"}

@app.post("/sms/upload")
def send_upload_sms(req: SmsUploadRequest):
    # Usando Twilio WhatsApp Sandbox
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "+14155238886") # Default Twilio Sandbox
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials missing. WhatsApp skipped.")
        return {"message": "Simulated WhatsApp (credentials missing)"}

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = (
        f"✅ *Archivo S3 Subido*\n"
        f"📄 Nombre: {req.filename}\n"
        f"📅 Fecha: {req.date}\n"
        f"💾 Usado: {req.used_space}\n"
        f"🟢 Disponible: {req.available_space}"
    )
    
    try:
        # Twilio requires numbers to be prefixed with 'whatsapp:'
        to_number = req.phone_number if req.phone_number.startswith('+') else f"+{req.phone_number}"
        
        response = client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            body=message,
            to=f"whatsapp:{to_number}"
        )
        return {"message": "WhatsApp sent", "message_id": response.sid}
    except Exception as e:
        logger.error(f"Error sending WhatsApp via Twilio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
