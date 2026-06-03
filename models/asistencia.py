"""
models/asistencia.py   ──   EP-04 Registro de Asistencia
Mapea la tabla `asistencia`.

Regla de negocio clave:
  P (Presente)   → cuenta para el porcentaje
  J (Justificado)→ cuenta para el porcentaje (no perjudica al alumno)
  A (Ausente)    → NO cuenta para el porcentaje

La restricción UNIQUE(inscripcion_id, sesion_id) garantiza que
solo exista UN registro por alumno por sesión, tanto en MySQL
como en SQLAlchemy.
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

# Enum de estados de asistencia
EstadoAsistencia = ("P", "A", "J")   # Presente / Ausente / Justificado


class Asistencia(Base):
    __tablename__ = "asistencia"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    inscripcion_id: Mapped[int]      = mapped_column(Integer, ForeignKey("inscripciones.id"), nullable=False)
    sesion_id:      Mapped[int]      = mapped_column(Integer, ForeignKey("sesiones.id"),      nullable=False)
    estado:         Mapped[str]      = mapped_column(Enum(*EstadoAsistencia), nullable=False, default="A")
    observacion:    Mapped[str|None] = mapped_column(Text)   # obligatorio si estado == "J"
    registrado_por: Mapped[int|None] = mapped_column(Integer, ForeignKey("usuarios.id"))
    created_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("inscripcion_id", "sesion_id", name="uq_inscripcion_sesion"),
    )

    # ── Relaciones ──────────────────────────────────────────────
    inscripcion: Mapped["Inscripcion"] = relationship("Inscripcion", back_populates="asistencias")
    sesion:      Mapped["Sesion"]      = relationship("Sesion",      back_populates="asistencias")

    # ── Propiedades ──────────────────────────────────────────────
    @property
    def cuenta_para_porcentaje(self) -> bool:
        """P y J cuentan; A no cuenta."""
        return self.estado in ("P", "J")

    @property
    def estado_legible(self) -> str:
        etiquetas = {"P": "Presente", "A": "Ausente", "J": "Justificado"}
        return etiquetas.get(self.estado, self.estado)

    def __repr__(self) -> str:
        return f"<Asistencia inscripcion={self.inscripcion_id} sesion={self.sesion_id} estado='{self.estado}'>"
