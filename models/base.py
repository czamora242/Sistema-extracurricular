# models/base.py
# ================================================================
# Base compartida para todos los modelos SQLAlchemy
# Todos los modelos importan desde aquí: from models.base import Base
# ================================================================

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos del sistema."""
    pass
