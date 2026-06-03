"""
models/rol.py   ──   EP-01 Autenticación
Mapea la tabla `roles`.
"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Rol(Base):
    __tablename__ = "roles"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre:      Mapped[str]      = mapped_column(String(50),  nullable=False, unique=True)
    descripcion: Mapped[str|None] = mapped_column(String(200))
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relación inversa: un rol tiene muchos usuarios
    usuarios: Mapped[list["Usuario"]] = relationship("Usuario", back_populates="rol")

    def __repr__(self) -> str:
        return f"<Rol id={self.id} nombre='{self.nombre}'>"
