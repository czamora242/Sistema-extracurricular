"""
models/facultad.py y models/carrera.py se unifican aquí
por ser tablas auxiliares pequeñas y fuertemente ligadas.

EP-02 · Gestión de Estudiantes
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


# ── Facultad ─────────────────────────────────────────────────────

class Facultad(Base):
    __tablename__ = "facultades"

    id:        Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre:    Mapped[str]  = mapped_column(String(150), nullable=False)
    codigo:    Mapped[str]  = mapped_column(String(20),  nullable=False, unique=True)
    activo:    Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Una facultad tiene muchas carreras
    carreras: Mapped[list["Carrera"]] = relationship("Carrera", back_populates="facultad")

    def __repr__(self) -> str:
        return f"<Facultad id={self.id} codigo='{self.codigo}'>"


# ── Carrera ──────────────────────────────────────────────────────

class Carrera(Base):
    __tablename__ = "carreras"

    id:          Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    facultad_id: Mapped[int]  = mapped_column(Integer, ForeignKey("facultades.id"), nullable=False)
    nombre:      Mapped[str]  = mapped_column(String(150), nullable=False)
    codigo:      Mapped[str]  = mapped_column(String(20),  nullable=False, unique=True)
    activo:      Mapped[bool] = mapped_column(Boolean, default=True)
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relaciones
    facultad:    Mapped["Facultad"]          = relationship("Facultad",   back_populates="carreras")
    estudiantes: Mapped[list["Estudiante"]]  = relationship("Estudiante", back_populates="carrera")

    def __repr__(self) -> str:
        return f"<Carrera id={self.id} codigo='{self.codigo}'>"
