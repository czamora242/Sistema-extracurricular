"""
models/inscripcion.py
EP-02 Gestión de Inscripciones
Mapea la tabla `inscripciones`.
"""

from datetime import date, datetime

from sqlalchemy import (Date,DateTime,Enum,ForeignKey,Integer,UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

EstadoInscripcion = ("Activo", "Retirado")



class Inscripcion(Base):
    __tablename__ = "inscripciones"

    id:                Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    taller_id:         Mapped[int]  = mapped_column(Integer, ForeignKey("talleres.id"),     nullable=False)
    estudiante_id:     Mapped[int]  = mapped_column(Integer, ForeignKey("estudiantes.id"),  nullable=False)
    fecha_inscripcion: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    estado:            Mapped[str]  = mapped_column(Enum("Activo", "Retirado"), nullable=False, default="Activo")
    created_at:        Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by:        Mapped[int|None] = mapped_column(Integer, ForeignKey("usuarios.id"))

    __table_args__ = (
        # Un estudiante solo puede inscribirse una vez al mismo taller
        UniqueConstraint("taller_id", "estudiante_id", name="uq_taller_estudiante"),
    )

    # Relaciones
    taller:      Mapped["Taller"]          = relationship("Taller",     back_populates="inscripciones")
    estudiante:  Mapped["Estudiante"]      = relationship("Estudiante", back_populates="inscripciones")
    asistencias: Mapped[list["Asistencia"]]= relationship("Asistencia", back_populates="inscripcion")

    def __repr__(self) -> str:
        return f"<Inscripcion taller={self.taller_id} estudiante={self.estudiante_id} estado='{self.estado}'>"
