from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres:Ecommerce1234!@ecommerce-db-evaluacion.cqj4ase2sivc.us-east-1.rds.amazonaws.com:5432/postgres'
EMAIL = 'nicolasfuentesm19@gmail.com'

engine = create_engine(DB_URL)
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT id, email, hashed_password, is_verified FROM users WHERE email=:e"),
        {"e": EMAIL}
    )
    row = result.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Email: {row[1]}")
        print(f"Hash: {row[2][:30]}...")
        print(f"Verificado: {row[3]}")
    else:
        print("Usuario NO encontrado en la base de datos de producción")
