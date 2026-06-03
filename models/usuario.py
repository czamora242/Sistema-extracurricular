
from datetime import datetime

import bcrypt
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    rol_id:            Mapped[int]           = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)
    nombres:           Mapped[str]           = mapped_column(String(100), nullable=False)
    apellidos:         Mapped[str]           = mapped_column(String(100), nullable=False)
    username:          Mapped[str]           = mapped_column(String(50),  nullable=False, unique=True)
    email:             Mapped[str]           = mapped_column(String(150), nullable=False, unique=True)
    password_hash:     Mapped[str]           = mapped_column(String(255), nullable=False)
    activo:            Mapped[bool]          = mapped_column(Boolean, default=True)
    ultimo_acceso:     Mapped[datetime|None] = mapped_column(DateTime)
    intentos_fallidos: Mapped[int]           = mapped_column(SmallInteger, default=0)
    bloqueado_hasta:   Mapped[datetime|None] = mapped_column(DateTime)
    created_at:        Mapped[datetime]      = mapped_column(DateTime, default=datetime.now)
    updated_at:        Mapped[datetime]      = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ── Relaciones ──────────────────────────────────────────────
    rol:     Mapped["Rol"]     = relationship("Rol",     back_populates="usuarios")
    docente: Mapped["Docente"] = relationship("Docente", back_populates="usuario", uselist=False)

    # ── Métodos de contraseña ────────────────────────────────────
    def set_password(self, password_plano: str) -> None:
        """
        Hashea y guarda la contraseña usando bcrypt.
        Llamar siempre este método, nunca asignar password_hash directamente.

        Ejemplo:
            usuario.set_password("MiClave123")
            session.commit()
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            password_plano.encode("utf-8"), salt
        ).decode("utf-8")

    def verificar_password(self, password_plano: str) -> bool:
        """
        Verifica si la contraseña ingresada coincide con el hash guardado.

        Ejemplo:
            if usuario.verificar_password(clave_ingresada):
                # acceso permitido
        """
        return bcrypt.checkpw(
            password_plano.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @property
    def esta_bloqueado(self) -> bool:
        """True si la cuenta está bloqueada por intentos fallidos."""
        if self.bloqueado_hasta is None:
            return False
        return datetime.now() < self.bloqueado_hasta

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} username='{self.username}' rol='{self.rol_id}'>"
