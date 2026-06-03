"""
database/connection.py
──────────────────────
Motor de conexión a MySQL y fábrica de sesiones.

USO en cualquier service:
    from database.connection import get_session

    with get_session() as session:
        resultado = session.query(MiModelo).all()
        # Al salir del bloque 'with': commit automático si no hay error,
        # rollback automático si hay excepción.

MIGRACIÓN A WEB (futuro):
    Solo cambia DB_HOST en el .env apuntando al servidor UNAB.
    Nada más cambia en el código.
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

# Carga las variables del archivo .env
load_dotenv()


def _build_url() -> str:
    """Construye la URL de conexión desde las variables de entorno."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "unab_talleres")
    user = os.getenv("DB_USER", "root")
    pwd  = os.getenv("DB_PASS", "")
    # pymysql es el driver que habla con MySQL desde Python
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}?charset=utf8mb4"


# ── Motor principal ──────────────────────────────────────────────
# pool_pre_ping=True: verifica la conexión antes de usarla.
# Evita errores si MySQL cerró la conexión por inactividad.
engine = create_engine(
    _build_url(),
    pool_pre_ping=True,
    pool_recycle=3600,   # recicla conexiones cada 1 hora
    echo=False,          # True → imprime todo el SQL generado (útil para debug)
)

# ── Fábrica de sesiones ──────────────────────────────────────────
_SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Session:
    """
    Context manager que abre y cierra sesiones de forma segura.

    Ejemplo:
        with get_session() as session:
            session.add(nuevo_objeto)
        # commit automático aquí

        with get_session() as session:
            raise ValueError("algo falló")
        # rollback automático aquí
    """
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def probar_conexion() -> tuple[bool, str]:
    """
    Verifica que la conexión a MySQL funciona.
    Úsala al iniciar la aplicación para mostrar error amigable al usuario.

    Retorna:
        (True, "Conexión exitosa")  → todo bien
        (False, "mensaje de error") → mostrar al usuario
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Conexión exitosa"
    except OperationalError as e:
        return False, f"No se pudo conectar a MySQL: {e.orig}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"
