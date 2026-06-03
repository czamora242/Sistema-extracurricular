"""
models/bienes.py   ──   EP-06 Gestión de Bienes Patrimoniales
Mapea las tablas `bienes_patrimoniales` y `asignaciones_bien`.

Flujo de estados del bien:
  Disponible → Asignado (al crear AsignacionBien)
  Asignado   → Disponible (al registrar devolución)
  Disponible → Mantenimiento (cuando requiere reparación)
  Cualquiera → DeBaja (baja definitiva)
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (Date, DateTime, Enum, ForeignKey, Integer,
                        Numeric, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

EstadoBien         = ("Disponible", "Asignado", "Mantenimiento", "DeBaja")
EstadoConservacion = ("Excelente", "Bueno", "Regular", "Malo", "Inservible")
EstadoAsignacion   = ("Activo", "Devuelto")


# ── Bien Patrimonial ─────────────────────────────────────────────

class BienPatrimonial(Base):
    __tablename__ = "bienes_patrimoniales"

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_patrimonial: Mapped[str]           = mapped_column(String(50), nullable=False, unique=True)
    descripcion:        Mapped[str]           = mapped_column(String(300), nullable=False)
    categoria:          Mapped[str|None]      = mapped_column(String(100))
    valor_adquisicion:  Mapped[Decimal|None]  = mapped_column(Numeric(10, 2))
    fecha_adquisicion:  Mapped[date|None]     = mapped_column(Date)
    estado:             Mapped[str]           = mapped_column(
                            Enum(*EstadoBien), nullable=False, default="Disponible"
                        )
    observaciones:      Mapped[str|None]      = mapped_column(Text)
    created_at:         Mapped[datetime]      = mapped_column(DateTime, default=datetime.now)
    updated_at:         Mapped[datetime]      = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    asignaciones: Mapped[list["AsignacionBien"]] = relationship(
        "AsignacionBien", back_populates="bien", order_by="AsignacionBien.created_at"
    )

    @property
    def asignacion_activa(self) -> "AsignacionBien | None":
        """Retorna la asignación vigente, o None si está disponible."""
        for a in self.asignaciones:
            if a.estado_asignacion == "Activo":
                return a
        return None

    @property
    def esta_disponible(self) -> bool:
        return self.estado == "Disponible"

    def __repr__(self) -> str:
        return f"<BienPatrimonial id={self.id} codigo='{self.codigo_patrimonial}' estado='{self.estado}'>"


# ── Asignación de Bien (Formato N°03) ───────────────────────────

class AsignacionBien(Base):
    __tablename__ = "asignaciones_bien"

    id:                        Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    bien_id:                   Mapped[int]      = mapped_column(Integer, ForeignKey("bienes_patrimoniales.id"), nullable=False)
    docente_id:                Mapped[int|None] = mapped_column(Integer, ForeignKey("docentes.id"))
    taller_id:                 Mapped[int|None] = mapped_column(Integer, ForeignKey("talleres.id"))
    fecha_asignacion:          Mapped[date]     = mapped_column(Date, nullable=False)
    fecha_devolucion_esperada: Mapped[date|None]= mapped_column(Date)
    fecha_devolucion_real:     Mapped[date|None]= mapped_column(Date)
    estado_conservacion:       Mapped[str|None] = mapped_column(Enum(*EstadoConservacion))
    observaciones_asignacion:  Mapped[str|None] = mapped_column(Text)
    observaciones_devolucion:  Mapped[str|None] = mapped_column(Text)
    recibido_por_nombre:       Mapped[str|None] = mapped_column(String(200))  # firma de recepción
    estado_asignacion:         Mapped[str]      = mapped_column(
                                   Enum(*EstadoAsignacion), nullable=False, default="Activo"
                               )
    asignado_por:              Mapped[int|None] = mapped_column(Integer, ForeignKey("usuarios.id"))
    created_at:                Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at:                Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    bien:    Mapped["BienPatrimonial"] = relationship("BienPatrimonial", back_populates="asignaciones")
    docente: Mapped["Docente|None"]    = relationship("Docente",         back_populates="asignaciones_bien")
    taller:  Mapped["Taller|None"]     = relationship("Taller",          back_populates="asignaciones_bien")

    @property
    def esta_vencida(self) -> bool:
        """True si pasó la fecha esperada de devolución y aún está activa."""
        if self.fecha_devolucion_esperada is None or self.estado_asignacion != "Activo":
            return False
        return date.today() > self.fecha_devolucion_esperada

    @property
    def devolucion_con_dano(self) -> bool:
        """True si fue devuelta con estado de conservación preocupante."""
        return self.estado_conservacion in ("Regular", "Malo", "Inservible")

    def __repr__(self) -> str:
        return (f"<AsignacionBien id={self.id} bien={self.bien_id} "
                f"estado='{self.estado_asignacion}'>")
