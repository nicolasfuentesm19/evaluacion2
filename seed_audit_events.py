from sqlalchemy import create_engine, text
from datetime import datetime

DB_URL = 'postgresql://postgres:Ecommerce1234!@ecommerce-db-evaluacion.cqj4ase2sivc.us-east-1.rds.amazonaws.com:5432/postgres'
engine = create_engine(DB_URL)

eventos = [
    ("admin@test.com", "Login", "Inicio de sesion exitoso", "200.1.1.1"),
    ("admin@test.com", "Archivo", "Archivo test.pdf subido a S3", "200.1.1.1"),
    ("admin@test.com", "Compra", "Orden #1 creada por 1200.0", "200.1.1.1"),
    ("admin@test.com", "Error Login", "Intento de inicio de sesion fallido", "200.1.1.1"),
    ("admin@test.com", "Registro", "Usuario registrado exitosamente", "200.1.1.1"),
    ("admin@test.com", "Pago Procesado", "Pago de la orden #1 aprobado", "200.1.1.1"),
    ("admin@test.com", "Validacion", "Cuenta validada exitosamente", "200.1.1.1"),
]

with engine.connect() as conn:
    for email, tipo, desc, ip in eventos:
        conn.execute(text("""
            INSERT INTO audit_events (timestamp, user_email, event_type, description, ip_address)
            VALUES (:ts, :email, :tipo, :desc, :ip)
        """), {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "email": email,
            "tipo": tipo,
            "desc": desc,
            "ip": ip
        })
    conn.commit()
    result = conn.execute(text("SELECT COUNT(*) FROM audit_events"))
    print(f"Total eventos insertados: {result.fetchone()[0]}")
