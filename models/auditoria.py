"""
models/auditoria.py   ──   EP-01 Auditoría Centralizada
Mapea la tabla `auditoria`.

¿Quién escribe en esta tabla?
  El service de cada módulo, justo antes o después de cada
  operación importante (INSERT, UPDATE, DELETE).
  Nunca se escribe directamente desde la UI Qt.

Los campos datos_anteriores y datos_nuevos guardan JSON:
  - datos_anteriores: dict con los valores ANTES del cambio (None en INSERT)
  - datos_nuevos:     dict con los valores DESPUÉS del cambio (None en DELETE)

Ejemplo de registro de auditoría:
  tabla_afectada = "estudiantes"
  accion         = "UPDATE"
  registro_id    = 42
  datos_anteriores = {"estado": "Activo", "email": "juan@unab.edu.pe"}
  datos_nuevos     = {"estado": "Inactivo", "email": "juan@unab.edu.pe"}
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

AccionAuditoria = ("INSERT", "UPDATE", "DELETE")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id:                Mapped[int]       = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id:        Mapped[int|None]  = mapped_column(Integer, ForeignKey("usuarios.id"))
    tabla_afectada:    Mapped[str]       = mapped_column(String(100), nullable=False)
    accion:            Mapped[str]       = mapped_column(Enum(*AccionAuditoria), nullable=False)
    registro_id:       Mapped[int|None]  = mapped_column(Integer)          # ID del registro afectado
    datos_anteriores:  Mapped[dict|None] = mapped_column(JSON)             # snapshot antes
    datos_nuevos:      Mapped[dict|None] = mapped_column(JSON)             # snapshot después
    ip_address:        Mapped[str|None]  = mapped_column(String(45))       # IPv4 o IPv6
    created_at:        Mapped[datetime]  = mapped_column(DateTime, default=datetime.now)

    # Relación (solo lectura — no se modifica desde aquí)
    usuario: Mapped["Usuario|None"] = relationship("Usuario")

    def __repr__(self) -> str:
        return (f"<Auditoria id={self.id} tabla='{self.tabla_afectada}' "
                f"accion='{self.accion}' usuario={self.usuario_id}>")
