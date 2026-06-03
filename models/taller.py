"""
models/taller.py   ──   EP-03 Gestión de Talleres
Mapea las tablas `talleres`, `sesiones` e `inscripciones`.

Estas tres tablas son el corazón del sistema:
  Taller → tiene muchas Sesiones
  Taller → tiene muchas Inscripciones (estudiantes inscritos)
  Inscripcion → tiene muchos registros de Asistencia
"""

from datetime import date, datetime, time

from sqlalchemy import (Date, DateTime, Enum, ForeignKey, Integer,
                        SmallInteger, String, Text, Time, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


# ── Taller ───────────────────────────────────────────────────────

EstadoTaller = ("Activo", "Suspendido", "Finalizado", "EnRiesgo")


class Taller(Base):
    __tablename__ = "talleres"

    id:                  Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    ciclo_academico_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("ciclos_academicos.id"), nullable=False)
    docente_id:          Mapped[int]      = mapped_column(Integer, ForeignKey("docentes.id"),          nullable=False)
    codigo:              Mapped[str]      = mapped_column(String(20),  nullable=False, unique=True)
    nombre:              Mapped[str]      = mapped_column(String(200), nullable=False)
    descripcion:         Mapped[str|None] = mapped_column(Text)
    categoria:           Mapped[str|None] = mapped_column(String(100))
    sede:                Mapped[str|None] = mapped_column(String(200))
    cupo_maximo:         Mapped[int]      = mapped_column(SmallInteger, nullable=False, default=30)
    horas_totales:       Mapped[int|None] = mapped_column(SmallInteger)
    umbral_asistencia:   Mapped[int]      = mapped_column(SmallInteger, nullable=False, default=80)  # 50-100
    estado:              Mapped[str]      = mapped_column(
                             Enum(*EstadoTaller), nullable=False, default="Activo"
                         )
    created_at:          Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at:          Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by:          Mapped[int|None] = mapped_column(Integer, ForeignKey("usuarios.id"))

    # ── Relaciones ──────────────────────────────────────────────
    ciclo_academico:  Mapped["CicloAcademico"]       = relationship("CicloAcademico",  back_populates="talleres")
    docente:          Mapped["Docente"]               = relationship("Docente",         back_populates="talleres")
    sesiones:         Mapped[list["Sesion"]]          = relationship("Sesion",          back_populates="taller",
                                                                      order_by="Sesion.numero_sesion")
    inscripciones:    Mapped[list["Inscripcion"]]     = relationship("Inscripcion",     back_populates="taller")
    listas_aptos:     Mapped[list["ListaAptos"]]      = relationship("ListaAptos",      back_populates="taller")
    asignaciones_bien:Mapped[list["AsignacionBien"]]  = relationship("AsignacionBien",  back_populates="taller")

    # ── Propiedades calculadas ───────────────────────────────────
    @property
    def total_inscritos(self) -> int:
        """Estudiantes activos inscritos en este taller."""
        return sum(1 for i in self.inscripciones if i.estado == "Activo")

    @property
    def cupo_disponible(self) -> int:
        return self.cupo_maximo - self.total_inscritos

    @property
    def total_sesiones(self) -> int:
        return len(self.sesiones)

    @property
    def sesiones_realizadas(self) -> int:
        return sum(1 for s in self.sesiones if s.estado == "Realizada")

    def __repr__(self) -> str:
        return f"<Taller id={self.id} codigo='{self.codigo}' estado='{self.estado}'>"


# ── Sesion ───────────────────────────────────────────────────────

EstadoSesion = ("Programada", "Realizada", "Cancelada")


class Sesion(Base):
    __tablename__ = "sesiones"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    taller_id:      Mapped[int]      = mapped_column(Integer, ForeignKey("talleres.id"), nullable=False)
    numero_sesion:  Mapped[int]      = mapped_column(SmallInteger, nullable=False)
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


# ── Inscripcion ──────────────────────────────────────────────────

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
