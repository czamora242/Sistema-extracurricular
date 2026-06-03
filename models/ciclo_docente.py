"""
models/ciclo_docente.py   ──   EP-03 Gestión de Talleres
Mapea las tablas `ciclos_academicos` y `docentes`.
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


# ── Ciclo Académico ──────────────────────────────────────────────

class CicloAcademico(Base):
    __tablename__ = "ciclos_academicos"

    id:           Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre:       Mapped[str]  = mapped_column(String(20), nullable=False, unique=True)  # ej: "2025-I"
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin:    Mapped[date] = mapped_column(Date, nullable=False)
    activo:       Mapped[bool] = mapped_column(Boolean, default=False)  # solo 1 activo
    created_at:   Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relaciones
    talleres:     Mapped[list["Taller"]]      = relationship("Taller",      back_populates="ciclo_academico")
    listas_aptos: Mapped[list["ListaAptos"]]  = relationship("ListaAptos",  back_populates="ciclo_academico")

    def __repr__(self) -> str:
        return f"<CicloAcademico id={self.id} nombre='{self.nombre}' activo={self.activo}>"


# ── Docente ──────────────────────────────────────────────────────

class Docente(Base):
    __tablename__ = "docentes"

    id:                   Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id:           Mapped[int|None] = mapped_column(Integer, ForeignKey("usuarios.id"))
    dni:                  Mapped[str]      = mapped_column(String(20),  nullable=False, unique=True)
    nombres:              Mapped[str]      = mapped_column(String(100), nullable=False)
    apellidos:            Mapped[str]      = mapped_column(String(100), nullable=False)
    especialidad:         Mapped[str|None] = mapped_column(String(150))
    email_institucional:  Mapped[str|None] = mapped_column(String(150))
    telefono:             Mapped[str|None] = mapped_column(String(20))
    activo:               Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:           Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at:           Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    usuario:           Mapped["Usuario|None"]          = relationship("Usuario",          back_populates="docente")
    talleres:          Mapped[list["Taller"]]           = relationship("Taller",           back_populates="docente")
    asignaciones_bien: Mapped[list["AsignacionBien"]]   = relationship("AsignacionBien",   back_populates="docente")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    def __repr__(self) -> str:
        return f"<Docente id={self.id} dni='{self.dni}'>"
