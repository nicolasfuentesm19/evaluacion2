from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres:Ecommerce1234!@ecommerce-db-evaluacion.cqj4ase2sivc.us-east-1.rds.amazonaws.com:5432/postgres'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    # Check if table exists
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' ORDER BY table_name
    """))
    tables = [r[0] for r in result.fetchall()]
    print("Tablas en RDS:", tables)
    
    if 'audit_events' in tables:
        result = conn.execute(text("SELECT COUNT(*) FROM audit_events"))
        count = result.fetchone()[0]
        print(f"Registros en audit_events: {count}")
        if count > 0:
            result = conn.execute(text("SELECT * FROM audit_events ORDER BY id DESC LIMIT 5"))
            for row in result.fetchall():
                print(row)
    else:
        print("TABLA audit_events NO EXISTE - creándola ahora...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id SERIAL PRIMARY KEY,
                timestamp VARCHAR,
                user_email VARCHAR,
                event_type VARCHAR,
                description VARCHAR,
                ip_address VARCHAR
            )
        """))
        conn.commit()
        print("Tabla creada exitosamente.")
