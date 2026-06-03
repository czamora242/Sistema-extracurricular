"""
models/estudiante.py   ──   EP-02 Gestión de Estudiantes
Mapea la tabla `estudiantes`.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

# Estados posibles del estudiante — mismo ENUM que en MySQL
EstadoEstudiante = ("Activo", "Inactivo", "Egresado")


class Estudiante(Base):
    __tablename__ = "estudiantes"

    id:                 Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    carrera_id:         Mapped[int]            = mapped_column(Integer, ForeignKey("carreras.id"), nullable=False)
    dni:                Mapped[str]            = mapped_column(String(20),  nullable=False, unique=True)
    codigo_estudiantil: Mapped[str]            = mapped_column(String(20),  nullable=False, unique=True)
    nombres:            Mapped[str]            = mapped_column(String(100), nullable=False)
    apellidos:          Mapped[str]            = mapped_column(String(100), nullable=False)
    fecha_nacimiento:   Mapped[date|None]      = mapped_column(Date)
    ciclo_actual:       Mapped[int|None]       = mapped_column(SmallInteger)
    email:              Mapped[str|None]       = mapped_column(String(150))
    telefono:           Mapped[str|None]       = mapped_column(String(20))
    foto_ruta:          Mapped[str|None]       = mapped_column(String(500))   # ruta relativa en disco
    estado:             Mapped[str]            = mapped_column(
                            Enum(*EstadoEstudiante), nullable=False, default="Activo"
                        )
    created_at:         Mapped[datetime]       = mapped_column(DateTime, default=datetime.now)
    updated_at:         Mapped[datetime]       = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by:         Mapped[int|None]       = mapped_column(Integer, ForeignKey("usuarios.id"))

    # ── Relaciones ──────────────────────────────────────────────
    carrera:       Mapped["Carrera"]              = relationship("Carrera",      back_populates="estudiantes")
    inscripciones: Mapped[list["Inscripcion"]]    = relationship("Inscripcion",  back_populates="estudiante")
    lista_detalles:Mapped[list["ListaAptoDetalle"]]= relationship("ListaAptoDetalle", back_populates="estudiante")

    # ── Propiedades calculadas ───────────────────────────────────
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @property
    def tiene_foto(self) -> bool:
        return bool(self.foto_ruta)

    def __repr__(self) -> str:
        return f"<Estudiante id={self.id} codigo='{self.codigo_estudiantil}' dni='{self.dni}'>"
