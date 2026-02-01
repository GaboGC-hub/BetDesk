#app/db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

def make_engine():
    url = os.environ.get("DATABASE_URL", "postgresql://betdesk:betdesk@localhost:5432/betdesk")
    return create_engine(url, pool_pre_ping=True)

ENGINE = make_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)


def create_tables():
    """
    Crea todas las tablas necesarias en la base de datos
    Lee los archivos SQL y los ejecuta
    """
    import logging
    logger = logging.getLogger("betdesk")
    
    sql_files = [
        "sql/odds_schema.sql",
        "sql/schema.sql"
    ]
    
    with ENGINE.connect() as conn:
        for sql_file in sql_files:
            try:
                logger.info(f"Ejecutando {sql_file}...")
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql = f.read()
                    # Ejecutar cada statement separadamente
                    for statement in sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(text(statement))
                conn.commit()
                logger.info(f"✅ {sql_file} ejecutado correctamente")
            except Exception as e:
                logger.error(f"❌ Error ejecutando {sql_file}: {e}")
                raise
    
    print("✅ Todas las tablas creadas correctamente")
