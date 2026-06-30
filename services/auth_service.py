"""
services/auth_service.py   ──   EP-01 Autenticación
═══════════════════════════════════════════════════════

¿QUÉ HACE ESTE ARCHIVO?
  Contiene TODA la lógica de autenticación del sistema.
  La ventana Qt solo llama funciones de aquí — nunca toca
  la BD directamente.

¿POR QUÉ SEPARARLO DE LA UI?
  Mañana, cuando pases a web, el controlador FastAPI llamará
  exactamente las mismas funciones. Cero duplicación de código.

FLUJO DE LOGIN:
  1. Usuario escribe user/pass en la ventana Qt
  2. Qt llama → AuthService.login(username, password)
  3. AuthService busca el usuario en MySQL
  4. Verifica si está bloqueado
  5. Verifica la contraseña con bcrypt
  6. Si falla: suma intento fallido, bloquea si llegó a 5
  7. Si ok: crea una SesionUsuario en memoria (60 min)
  8. Retorna el resultado a Qt

SESIÓN EN MEMORIA (desktop):
  En una app de escritorio no hay "token JWT" como en web.
  La sesión es un objeto Python que vive mientras la app
  esté abierta. Cuando el usuario cierra sesión o pasan
  60 min sin actividad, el objeto se destruye.
"""

from dataclasses import dataclass, field
from datetime    import datetime, timedelta
from typing      import Optional

from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_session
from models              import Usuario, Auditoria


# ══════════════════════════════════════════════════════════════════
# CONSTANTES DE CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════

MAX_INTENTOS_FALLIDOS = 5
DURACION_BLOQUEO_MIN  = 30      # minutos bloqueado tras 5 intentos
DURACION_SESION_MIN   = 60      # minutos antes de cierre automático


# ══════════════════════════════════════════════════════════════════
# OBJETO DE SESIÓN EN MEMORIA
# ══════════════════════════════════════════════════════════════════

@dataclass
class SesionUsuario:
    """
    Representa al usuario que está logueado en este momento.
    Vive en memoria — no se guarda en BD.

    ¿POR QUÉ dataclass?
      Es una clase simple que solo guarda datos. @dataclass genera
      automáticamente __init__, __repr__, etc. sin escribirlos.

    USO:
        sesion = AuthService.login("juan", "clave123")
        if sesion:
            print(sesion.nombre_completo)  # "Juan Pérez"
            print(sesion.es_administrador) # True o False
    """
    usuario_id:     int
    username:       str
    nombre_completo: str
    email:          str
    rol_nombre:     str          # "Administrador", "Docente", "Operador"
    inicio_sesion:  datetime = field(default_factory=datetime.now)
    ultimo_uso:     datetime = field(default_factory=datetime.now)

    # ── Permisos por rol ─────────────────────────────────────────
    @property
    def es_administrador(self) -> bool:
        return self.rol_nombre == "Administrador"

    @property
    def es_docente(self) -> bool:
        return self.rol_nombre == "Docente"

    @property
    def es_operador(self) -> bool:
        return self.rol_nombre == "Operador"

    # ── Control de tiempo de sesión ──────────────────────────────
    def registrar_actividad(self) -> None:
        """
        Llamar cada vez que el usuario hace algo en la UI.
        Reinicia el contador de 60 minutos de inactividad.
        """
        self.ultimo_uso = datetime.now()

    @property
    def sesion_expirada(self) -> bool:
        """
        True si pasaron más de 60 min desde la última actividad.
        La MainWindow verifica esto periódicamente con un QTimer.
        """
        minutos_inactivo = (datetime.now() - self.ultimo_uso).seconds / 60
        return minutos_inactivo >= DURACION_SESION_MIN

    @property
    def minutos_restantes(self) -> int:
        """Minutos que quedan antes del cierre automático."""
        inactivo = (datetime.now() - self.ultimo_uso).seconds / 60
        return max(0, int(DURACION_SESION_MIN - inactivo))


# ══════════════════════════════════════════════════════════════════
# RESULTADO DE OPERACIONES
# ══════════════════════════════════════════════════════════════════

@dataclass
class ResultadoAuth:
    """
    Lo que retorna cada función del AuthService.

    ¿POR QUÉ no lanzar excepciones directamente?
      La UI Qt necesita mostrar mensajes en español al usuario.
      Con este objeto puede decidir QUÉ mensaje mostrar sin
      necesidad de capturar excepciones específicas.

    USO:
        resultado = AuthService.login(user, pwd)
        if resultado.ok:
            # abrir ventana principal
        else:
            QMessageBox.warning(self, "Error", resultado.mensaje)
    """
    ok:      bool
    mensaje: str
    sesion:  Optional[SesionUsuario] = None
    datos:   Optional[dict]          = None   # info extra si se necesita


# ══════════════════════════════════════════════════════════════════
# SERVICIO DE AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════

class AuthService:
    """
    Todas las funciones son @staticmethod:
    No necesitas crear una instancia (AuthService()),
    las llamas directamente: AuthService.login(...)

    ¿POR QUÉ staticmethod y no funciones sueltas?
      Agrupa todo lo relacionado con auth en un namespace claro.
      En web, el controlador FastAPI importa esta misma clase.
    """

    # ── LOGIN ────────────────────────────────────────────────────
    @staticmethod
    def login(username: str, password: str) -> ResultadoAuth:
        """
        Intenta autenticar al usuario.

        PASOS INTERNOS:
          1. Busca el usuario por username en MySQL
          2. Verifica si existe y está activo
          3. Verifica si está bloqueado (y si el bloqueo ya expiró)
          4. Verifica la contraseña con bcrypt
          5. Si falla: incrementa intentos, bloquea si llegó a 5
          6. Si ok: resetea intentos, crea SesionUsuario

        PARÁMETROS:
          username: lo que escribió en el campo "Usuario"
          password: lo que escribió en el campo "Contraseña"

        RETORNA:
          ResultadoAuth con ok=True y sesion=SesionUsuario si todo bien
          ResultadoAuth con ok=False y mensaje de error si algo falla
        """
        # Validación básica antes de ir a la BD
        if not username or not password:
            return ResultadoAuth(ok=False, mensaje="Ingresa usuario y contraseña.")

        try:
            with get_session() as session:

                # ── 1. Buscar usuario ────────────────────────────
                usuario: Optional[Usuario] = (
                    session.query(Usuario)
                    .filter(Usuario.username == username.strip())
                    .first()
                )

                # Mensaje genérico: no revelamos si el user existe o no
                if usuario is None or not usuario.activo:
                    return ResultadoAuth(
                        ok=False,
                        mensaje="Usuario o contraseña incorrectos."
                    )

                # ── 2. Verificar bloqueo ─────────────────────────
                if usuario.esta_bloqueado:
                    minutos = int(
                        (usuario.bloqueado_hasta - datetime.now()).seconds / 60
                    ) + 1
                    return ResultadoAuth(
                        ok=False,
                        mensaje=(f"Cuenta bloqueada por {MAX_INTENTOS_FALLIDOS} "
                                 f"intentos fallidos.\n"
                                 f"Intenta de nuevo en {minutos} minuto(s).")
                    )

                # ── 3. Verificar contraseña ──────────────────────
                if not usuario.verificar_password(password):
                    resultado = AuthService._registrar_intento_fallido(
                        session, usuario
                    )
                    return resultado

                # ── 4. Login exitoso ─────────────────────────────
                usuario.intentos_fallidos = 0
                usuario.bloqueado_hasta   = None
                usuario.ultimo_acceso     = datetime.now()
                # El commit lo hace automáticamente get_session()

                # Registrar en auditoría
                AuthService._auditar(
                    session,
                    usuario_id     = usuario.id,
                    tabla          = "usuarios",
                    accion         = "UPDATE",
                    registro_id    = usuario.id,
                    datos_nuevos   = {"accion": "login_exitoso",
                                      "username": username}
                )

                sesion = SesionUsuario(
                    usuario_id      = usuario.id,
                    username        = usuario.username,
                    nombre_completo = usuario.nombre_completo,
                    email           = usuario.email,
                    rol_nombre      = usuario.rol.nombre,
                )

                return ResultadoAuth(
                    ok=True,
                    mensaje=f"Bienvenido, {usuario.nombres}.",
                    sesion=sesion
                )

        except SQLAlchemyError as e:
            return ResultadoAuth(
                ok=False,
                mensaje=f"Error de base de datos. Contacta al administrador.\n({e})"
            )

    # ── CAMBIO DE CONTRASEÑA ─────────────────────────────────────
    @staticmethod
    def cambiar_password(
        sesion_activa: SesionUsuario,
        password_actual: str,
        password_nuevo: str,
        password_confirmacion: str
    ) -> ResultadoAuth:
        """
        Permite al usuario cambiar su propia contraseña.

        VALIDACIONES:
          - La contraseña actual debe ser correcta
          - La nueva debe tener al menos 8 caracteres
          - La nueva y la confirmación deben coincidir
          - La nueva no puede ser igual a la actual
        """
        # Validaciones antes de ir a la BD
        if not password_actual or not password_nuevo:
            return ResultadoAuth(ok=False, mensaje="Todos los campos son obligatorios.")

        if password_nuevo != password_confirmacion:
            return ResultadoAuth(ok=False, mensaje="La nueva contraseña no coincide con la confirmación.")

        if len(password_nuevo) < 8:
            return ResultadoAuth(ok=False, mensaje="La nueva contraseña debe tener al menos 8 caracteres.")

        try:
            with get_session() as session:
                usuario = session.get(Usuario, sesion_activa.usuario_id)

                if not usuario.verificar_password(password_actual):
                    return ResultadoAuth(ok=False, mensaje="La contraseña actual es incorrecta.")

                if usuario.verificar_password(password_nuevo):
                    return ResultadoAuth(ok=False, mensaje="La nueva contraseña no puede ser igual a la actual.")

                usuario.set_password(password_nuevo)
                usuario.updated_at = datetime.now()

                AuthService._auditar(
                    session,
                    usuario_id  = sesion_activa.usuario_id,
                    tabla       = "usuarios",
                    accion      = "UPDATE",
                    registro_id = usuario.id,
                    datos_nuevos= {"accion": "cambio_password"}
                )

            return ResultadoAuth(ok=True, mensaje="Contraseña actualizada correctamente.")

        except SQLAlchemyError as e:
            return ResultadoAuth(ok=False, mensaje=f"Error al actualizar contraseña: {e}")

    # ── RESTABLECER CONTRASEÑA (ADMINISTRADOR) ───────────────────
    @staticmethod
    def restablecer_password_admin(sesion_activa: SesionUsuario,usuario_id: int,password_nuevo: str,password_confirmacion: str) -> ResultadoAuth:

        if not sesion_activa.es_administrador:
            return ResultadoAuth(
                ok=False,
                mensaje="No tienes permisos para realizar esta operación."
            )

        if not password_nuevo:
            return ResultadoAuth(
                ok=False,
                mensaje="La nueva contraseña es obligatoria."
            )

        if len(password_nuevo) < 8:
            return ResultadoAuth(
                ok=False,
                mensaje="La contraseña debe tener al menos 8 caracteres."
            )

        if password_nuevo != password_confirmacion:
            return ResultadoAuth(
                ok=False,
                mensaje="Las contraseñas no coinciden."
            )

        try:
            with get_session() as session:

                usuario = session.get(Usuario, usuario_id)

                if usuario is None:
                    return ResultadoAuth(
                        ok=False,
                        mensaje="El usuario no existe."
                    )

                usuario.set_password(password_nuevo)
                usuario.updated_at = datetime.now()

                AuthService._auditar(
                    session,
                    usuario_id=sesion_activa.usuario_id,
                    tabla="usuarios",
                    accion="UPDATE",
                    registro_id=usuario.id,
                    datos_nuevos={
                        "accion": "restablecer_password",
                        "usuario_afectado": usuario.username
                    }
                )

                return ResultadoAuth(
                    ok=True,
                    mensaje=f"La contraseña de '{usuario.username}' fue actualizada correctamente."
                )

        except SQLAlchemyError as e:
            return ResultadoAuth(
                ok=False,
                mensaje=f"Error al actualizar la contraseña: {e}"
            )

    # ── VERIFICAR SESIÓN ACTIVA ──────────────────────────────────
    @staticmethod
    def verificar_sesion(sesion: Optional[SesionUsuario]) -> bool:
        """
        Verifica que la sesión existe y no ha expirado.
        La MainWindow llama esto cada vez que el usuario hace algo.

        USO:
            if not AuthService.verificar_sesion(self.sesion_actual):
                self.cerrar_sesion()
        """
        if sesion is None:
            return False
        return not sesion.sesion_expirada

    # ── LOGOUT ───────────────────────────────────────────────────
    @staticmethod
    def logout(sesion: SesionUsuario) -> None:
        """
        Registra el cierre de sesión en auditoría.
        La MainWindow debe destruir el objeto SesionUsuario después.

        USO:
            AuthService.logout(self.sesion_actual)
            self.sesion_actual = None
            self.show_login()
        """
        try:
            with get_session() as session:
                AuthService._auditar(
                    session,
                    usuario_id  = sesion.usuario_id,
                    tabla       = "usuarios",
                    accion      = "UPDATE",
                    registro_id = sesion.usuario_id,
                    datos_nuevos= {"accion": "logout",
                                   "username": sesion.username}
                )
        except SQLAlchemyError:
            pass  # El logout siempre debe completarse aunque falle la auditoría

    # ══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS (uso interno del servicio)
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _registrar_intento_fallido(session, usuario: Usuario) -> ResultadoAuth:
        """
        Suma 1 intento fallido. Si llega a MAX_INTENTOS_FALLIDOS,
        bloquea la cuenta por DURACION_BLOQUEO_MIN minutos.
        """
        usuario.intentos_fallidos += 1

        if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
            usuario.bloqueado_hasta = (
                datetime.now() + timedelta(minutes=DURACION_BLOQUEO_MIN)
            )
            return ResultadoAuth(
                ok=False,
                mensaje=(f"Has superado {MAX_INTENTOS_FALLIDOS} intentos fallidos.\n"
                         f"Tu cuenta se bloqueó por {DURACION_BLOQUEO_MIN} minutos.")
            )

        restantes = MAX_INTENTOS_FALLIDOS - usuario.intentos_fallidos
        return ResultadoAuth(
            ok=False,
            mensaje=(f"Usuario o contraseña incorrectos.\n"
                     f"Te quedan {restantes} intento(s) antes del bloqueo.")
        )

    @staticmethod
    def _auditar(session, usuario_id: int, tabla: str, accion: str,
                 registro_id: int = None, datos_nuevos: dict = None) -> None:
        """Inserta un registro en la tabla auditoria."""
        registro = Auditoria(
            usuario_id    = usuario_id,
            tabla_afectada= tabla,
            accion        = accion,
            registro_id   = registro_id,
            datos_nuevos  = datos_nuevos,
        )
        session.add(registro)
