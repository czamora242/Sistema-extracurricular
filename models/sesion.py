"""
models/sesion.py
EP-03 Gestión de Sesiones de Talleres
Mapea la tabla `sesiones`.
"""

from datetime import date, time, datetime

from sqlalchemy import (Date,Time,DateTime,Enum,ForeignKey,Integer,Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


EstadoSesion = ("Programada", "Realizada", "Cancelada")


class Sesion(Base):
    __tablename__ = "sesiones"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    taller_id:      Mapped[int]      = mapped_column(Integer, ForeignKey("talleres.id"), nullable=False)
    numero_sesion:  Mapped[int]      = mapped_column(Integer, nullable=False)
    fecha:          Mapped[date]     = mapped_column(Date, nullable=False)
    hora_inicio:    Mapped[time]     = mapped_column(Time, nullable=False)
    hora_fin:       Mapped[time]     = mapped_column(Time, nullable=False)
    estado:         Mapped[str]      = mapped_column(Enum(*EstadoSesion), nullable=False, default="Programada")
    observaciones:  Mapped[str|None] = mapped_column(Text)
    created_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        # Un taller no puede tener dos sesiones con el mismo número
        UniqueConstraint("taller_id", "numero_sesion", name="uq_taller_sesion"),
    )

    # Relaciones
    taller:     Mapped["Taller"]          = relationship("Taller",     back_populates="sesiones")
    asistencias:Mapped[list["Asistencia"]]= relationship("Asistencia", back_populates="sesion")

    @property
    def es_futura(self) -> bool:
        return self.fecha > date.today()

    def __repr__(self) -> str:
        return f"<Sesion id={self.id} taller={self.taller_id} n°{self.numero_sesion} fecha={self.fecha}>"
