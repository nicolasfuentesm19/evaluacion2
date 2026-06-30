from sqlalchemy import create_engine, text
from passlib.context import CryptContext

DB_URL = 'postgresql://postgres:Ecommerce1234!@ecommerce-db-evaluacion.cqj4ase2sivc.us-east-1.rds.amazonaws.com:5432/postgres'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_hash = pwd_context.hash("Test1234!")

engine = create_engine(DB_URL)
with engine.connect() as conn:
    # Insert new test user
    try:
        conn.execute(text("""
            INSERT INTO users (email, hashed_password, is_active, is_verified, verification_code)
            VALUES ('admin@test.com', :h, true, true, '000000')
            ON CONFLICT (email) DO UPDATE SET hashed_password=:h, is_verified=true
        """), {"h": new_hash})
        conn.commit()
        print("Usuario admin@test.com creado/actualizado con contraseña: Test1234!")
    except Exception as e:
        print(f"Error: {e}")
