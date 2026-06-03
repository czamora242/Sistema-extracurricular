"""
models/lista_aptos.py   ──   EP-05 Lista de Aptos
Mapea las tablas `listas_aptos` y `lista_aptos_detalle`.

Flujo:
  1. Coordinador abre la previsualización (vista v_estudiantes_aptos en MySQL)
  2. Puede excluir alumnos manualmente antes de confirmar
  3. Al confirmar → se crea un registro en ListaAptos
     y un ListaAptoDetalle por cada alumno (con snapshot de datos)
  4. El sistema genera el archivo .xlsx y guarda la ruta en `ruta_excel`

IMPORTANTE — por qué guardamos snapshots en lista_aptos_detalle:
  Los datos del alumno (nombre, carrera, porcentaje) se copian al momento
  de emitir la lista. Si después se corrigen datos del alumno o cambia
  el umbral del taller, las listas históricas quedan intactas.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (Boolean, Date, DateTime, ForeignKey, Integer,
                        Numeric, SmallInteger, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


# ── Lista de Aptos (cabecera) ────────────────────────────────────

class ListaAptos(Base):
    __tablename__ = "listas_aptos"

    id:                  Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    taller_id:           Mapped[int]      = mapped_column(Integer, ForeignKey("talleres.id"),          nullable=False)
    ciclo_academico_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("ciclos_academicos.id"), nullable=False)
    fecha_emision:       Mapped[date]     = mapped_column(Date, nullable=False, default=date.today)
    total_inscritos:     Mapped[int]      = mapped_column(SmallInteger, nullable=False, default=0)
    total_aptos:         Mapped[int]      = mapped_column(SmallInteger, nullable=False, default=0)
    umbral_aplicado:     Mapped[int]      = mapped_column(SmallInteger, nullable=False)  # snapshot del umbral
    generado_por:        Mapped[int|None] = mapped_column(Integer, ForeignKey("usuarios.id"))
    ruta_excel:          Mapped[str|None] = mapped_column(String(500))   # ruta relativa del .xlsx
    observaciones:       Mapped[str|None] = mapped_column(Text)
    created_at:          Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # ── Relaciones ──────────────────────────────────────────────
    taller:          Mapped["Taller"]               = relationship("Taller",          back_populates="listas_aptos")
    ciclo_academico: Mapped["CicloAcademico"]       = relationship("CicloAcademico",  back_populates="listas_aptos")
    detalle:         Mapped[list["ListaAptoDetalle"]]= relationship("ListaAptoDetalle",
                                                                     back_populates="lista",
                                                                     cascade="all, delete-orphan")

    @property
    def porcentaje_aprobacion(self) -> float:
        """% de alumnos aptos sobre el total de inscritos."""
        if self.total_inscritos == 0:
            return 0.0
        return round(self.total_aptos * 100 / self.total_inscritos, 1)

    def __repr__(self) -> str:
        return (f"<ListaAptos id={self.id} taller={self.taller_id} "
                f"fecha={self.fecha_emision} aptos={self.total_aptos}>")


# ── Detalle por alumno ───────────────────────────────────────────

class ListaAptoDetalle(Base):
    __tablename__ = "lista_aptos_detalle"

    id:                    Mapped[int]     = mapped_column(Integer, primary_key=True, autoincrement=True)
    lista_id:              Mapped[int]     = mapped_column(Integer, ForeignKey("listas_aptos.id"), nullable=False)
    estudiante_id:         Mapped[int]     = mapped_column(Integer, ForeignKey("estudiantes.id"),  nullable=False)

    # Snapshots: datos al momento de emitir la lista
    codigo_estudiantil:    Mapped[str]     = mapped_column(String(20),  nullable=False)
    nombres:               Mapped[str]     = mapped_column(String(200), nullable=False)
    carrera:               Mapped[str]     = mapped_column(String(150), nullable=False)

    # Estadísticas de asistencia al cierre
    sesiones_asistidas:    Mapped[int]     = mapped_column(SmallInteger, nullable=False, default=0)
    sesiones_totales:      Mapped[int]     = mapped_column(SmallInteger, nullable=False, default=0)
    porcentaje_asistencia: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    es_apto:               Mapped[bool]    = mapped_column(Boolean, nullable=False, default=False)

    # Exclusión manual por el coordinador
    excluido_manual:       Mapped[bool]    = mapped_column(Boolean, nullable=False, default=False)
    motivo_exclusion:      Mapped[str|None]= mapped_column(String(300))

    # ── Relaciones ──────────────────────────────────────────────
    lista:      Mapped["ListaAptos"]  = relationship("ListaAptos",  back_populates="detalle")
    estudiante: Mapped["Estudiante"]  = relationship("Estudiante",  back_populates="lista_detalles")

    @property
    def aparece_en_lista(self) -> bool:
        """True si el alumno es apto Y no fue excluido manualmente."""
        return self.es_apto and not self.excluido_manual

    def __repr__(self) -> str:
        return (f"<ListaAptoDetalle lista={self.lista_id} "
                f"estudiante={self.codigo_estudiantil} apto={self.es_apto}>")
