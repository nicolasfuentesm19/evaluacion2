import os
from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres:Ecommerce1234!@ecommerce-db-evaluacion.cqj4ase2sivc.us-east-1.rds.amazonaws.com:5432/postgres'
NEW_HASH = '$2b$12$gD7fgwNZbeQUEC7BZGiL0ePyAWST/u0PlT0jVqHARRefge49mGSe2'
EMAIL = 'nicolasfuentesm19@gmail.com'

engine = create_engine(DB_URL)
with engine.connect() as conn:
    result = conn.execute(
        text("UPDATE users SET hashed_password=:h, is_verified=true WHERE email=:e"),
        {"h": NEW_HASH, "e": EMAIL}
    )
    conn.commit()
    print(f'Filas actualizadas: {result.rowcount}')
