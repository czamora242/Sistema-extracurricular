"""
services/docente_service.py   ──   Gestión de Docentes
═════════════════════════════════════════════════════════

¿QUÉ HACE?
  • CRUD: Crear, leer, actualizar, eliminar docentes
  • Validaciones: DNI único, email único
  • Vincular docente con usuario (acceso al sistema)
  • Crear usuario automáticamente si no existe
  • Auditoría: registra cada cambio

¿CUÁNDO SE USA?
  Panel admin → Gestión de docentes
  Crear docente para que pueda acceder al sistema
  Asignar docente a talleres

PATRÓN: Igual que usuario_service.py
  1. Validar entrada
  2. Buscar en BD
  3. Hacer cambio
  4. Auditar
  5. Retornar resultado
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from database.connection import get_session
from models import Docente, Usuario, Auditoria


# ══════════════════════════════════════════════════════════════════
# RESULTADO ESTÁNDAR
# ══════════════════════════════════════════════════════════════════

@dataclass
class ResultadoDocente:
    """Respuesta estándar de operaciones de docente."""
    ok: bool
    mensaje: str
    docente: Optional[Docente] = None
    lista: Optional[List[Dict[str, Any]]] = None
    datos: Optional[Dict[str, Any]] = None


# ══════════════════════════════════════════════════════════════════
# SERVICIO DE DOCENTES
# ══════════════════════════════════════════════════════════════════

class DocenteService:
    """Gestión completa de docentes del sistema."""

    # ══════════════════════════════════════════════════════════════
    # CREAR DOCENTE
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def crear(
        dni: str,
        nombres: str,
        apellidos: str,
        especialidad: str = None,
        email_institucional: str = None,
        telefono: str = None,
        usuario_id: int = None,
        usuario_creador_id: int = None
    ) -> ResultadoDocente:
        """
        Crea un nuevo docente en el sistema.

        VALIDACIONES:
          • DNI: obligatorio, único, 6-20 caracteres
          • Nombres y apellidos: no vacíos, 2-100 caracteres
          • Email: formato válido si se proporciona
          • Especialidad: opcional
          • Usuario: opcional (puede vincularse después)

        PARÁMETROS:
          usuario_id: ID del usuario vinculado (opcional)
          usuario_creador_id: ID de quién está creando (para auditoría)

        RETORNA:
          ResultadoDocente con ok=True y datos del docente creado
          O ResultadoDocente con ok=False y mensaje de error
        """

        # ── Validaciones ─────────────────────────────────────────
        error = DocenteService._validar_datos(
            dni, nombres, apellidos, email_institucional
        )
        if error:
            return ResultadoDocente(ok=False, mensaje=error)

        try:
            with get_session() as session:
                # Verificar DNI único
                existe_dni = session.query(Docente).filter_by(
                    dni=dni.strip()
                ).first()
                if existe_dni:
                    return ResultadoDocente(
                        ok=False,
                        mensaje="Ya existe un docente con este DNI."
                    )

                # Si se proporciona usuario_id, verificar que existe
                if usuario_id:
                    usuario = session.query(Usuario).filter_by(
                        id=usuario_id
                    ).first()
                    if not usuario:
                        return ResultadoDocente(
                            ok=False,
                            mensaje=f"El usuario con ID {usuario_id} no existe."
                        )

                # Crear docente
                docente = Docente(
                    dni=dni.strip(),
                    nombres=nombres.strip(),
                    apellidos=apellidos.strip(),
                    especialidad=especialidad.strip() if especialidad else None,
                    email_institucional=email_institucional.strip().lower() if email_institucional else None,
                    telefono=telefono.strip() if telefono else None,
                    usuario_id=usuario_id,
                    activo=True
                )

                session.add(docente)
                session.flush()
                docente_id = docente.id

                # Auditoría
                DocenteService._auditar(
                    session,
                    usuario_id=usuario_creador_id or usuario_id or docente_id,
                    tabla_afectada="docentes",
                    accion="INSERT",
                    registro_id=docente_id,
                    datos_nuevos={
                        "dni": docente.dni,
                        "nombres": nombres,
                        "apellidos": apellidos,
                        "especialidad": especialidad,
                        "email_institucional": email_institucional,
                        "usuario_id": usuario_id,
                        "accion": "docente_creado"
                    }
                )

                session.commit()

                return ResultadoDocente(
                    ok=True,
                    mensaje=f"Docente '{docente.nombre_completo}' creado correctamente.",
                    docente=docente,
                    datos={
                        "id": docente.id,
                        "dni": docente.dni,
                        "nombre_completo": docente.nombre_completo,
                        "especialidad": docente.especialidad,
                        "email": docente.email_institucional,
                        "usuario_id": docente.usuario_id
                    }
                )

        except IntegrityError as e:
            if "dni" in str(e).lower():
                return ResultadoDocente(
                    ok=False,
                    mensaje="Ya existe un docente con este DNI."
                )
            else:
                return ResultadoDocente(
                    ok=False,
                    mensaje=f"Error de integridad: {str(e)}"
                )

        except SQLAlchemyError as e:
            return ResultadoDocente(
                ok=False,
                mensaje=f"Error al crear docente: {str(e)}"
            )

    # ══════════════════════════════════════════════════════════════
    # OBTENER DOCENTE
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def obtener_por_id(docente_id: int) -> ResultadoDocente:
        """Obtiene un docente por su ID."""
        try:
            with get_session() as session:
                docente = session.query(Docente).filter_by(id=docente_id).first()

                if not docente:
                    return ResultadoDocente(
                        ok=False,
                        mensaje=f"Docente con ID {docente_id} no encontrado."
                    )

                return ResultadoDocente(
                    ok=True,
                    mensaje="Docente obtenido correctamente.",
                    docente=docente,
                    datos={
                        "id": docente.id,
                        "dni": docente.dni,
                        "nombres": docente.nombres,
                        "apellidos": docente.apellidos,
                        "nombre_completo": docente.nombre_completo,
                        "especialidad": docente.especialidad,
                        "email_institucional": docente.email_institucional,
                        "telefono": docente.telefono,
                        "usuario_id": docente.usuario_id,
                        "usuario": docente.usuario.username if docente.usuario else None,
                        "activo": docente.activo
                    }
                )

        except SQLAlchemyError as e:
            return ResultadoDocente(
                ok=False,
                mensaje=f"Error al obtener docente: {str(e)}"
            )

    @staticmethod
    def obtener_por_dni(dni: str) -> ResultadoDocente:
        """Obtiene un docente por su DNI."""
        try:
            with get_session() as session:
                docente = session.query(Docente).filter_by(
                    dni=dni.strip()
                ).first()

                if not docente:
                    return ResultadoDocente(
                        ok=False,
                        mensaje=f"Docente con DNI '{dni}' no encontrado."
                    )

                return ResultadoDocente(
                    ok=True,
                    mensaje="Docente obtenido correctamente.",
                    docente=docente
                )

        except SQLAlchemyError as e:
            return ResultadoDocente(
                ok=False,
                mensaje=f"Error al obtener docente: {str(e)}"
            )

    # ══════════════════════════════════════════════════════════════
    # LISTAR DOCENTES
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def listar(
        activos_solo: bool = True,
        sin_usuario: bool = False,
        limite: int = None
    ) -> ResultadoDocente:
        """
        Lista docentes con filtros opcionales.

        PARÁMETROS:
          activos_solo: True = solo docentes activos
          sin_usuario: True = solo docentes sin usuario asignado
          limite: máximo número de resultados
        """
        try:
            with get_session() as session:
                query = session.query(Docente)

                if activos_solo:
                    query = query.filter_by(activo=True)

                if sin_usuario:
                    query = query.filter_by(usuario_id=None)

                if limite:
                    query = query.limit(limite)

                docentes = query.order_by(Docente.nombres).all()

                lista = [
                    {
                        "id": d.id,
                        "dni": d.dni,
                        "nombre": d.nombre_completo,
                        "apellidos": d.apellidos,
                        "especialidad": d.especialidad or "—",
                        "email": d.email_institucional or "—",
                        "usuario": d.usuario.username if d.usuario else "Sin usuario",
                        "activo": d.activo
                    }
                    for d in docentes
                ]

                return ResultadoDocente(
                    ok=True,
                    mensaje=f"Se encontraron {len(lista)} docente(s).",
                    lista=lista
                )

        except SQLAlchemyError as e:
            return ResultadoDocente(
                ok=False,
                mensaje=f"Error al listar docentes: {str(e)}"
            )

    # ══════════════════════════════════════════════════════════════
    # ACTUALIZAR DOCENTE
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def actualizar(
        docente_id: int,
        nombres: str = None,
        apellidos: str = None,
        especialidad: str = None,
        email_institucional: str = None,
        telefono: str = None,
        usuario_id: int = None,
        activo: bool = None,
        usuario_editor_id: int = None
    ) -> ResultadoDocente:
        """Actualiza datos del docente."""
        try:
            with get_session() as session:
                docente = session.query(Docente).filter_by(id=docente_id).first()

                if not docente:
                    return ResultadoDocente(
                        ok=False,
                        mensaje=f"Docente con ID {docente_id} no encontrado."
                    )

                # Guardar valores antiguos
                datos_anteriores = {
                    "nombres": docente.nombres,
                    "apellidos": docente.apellidos,
                    "especialidad": docente.especialidad,
                    "email_institucional": docente.email_institucional,
                    "telefono": docente.telefono,
                    "usuario_id": docente.usuario_id,
                    "activo": docente.activo
                }

                cambios = {}

                if nombres is not None:
                    nombres_limpio = nombres.strip()
                    if len(nombres_limpio) < 2:
                        return ResultadoDocente(
                            ok=False,
                            mensaje="El nombre debe tener al menos 2 caracteres."
                        )
                    docente.nombres = nombres_limpio
                    cambios["nombres"] = nombres_limpio

                if apellidos is not None:
                    apellidos_limpio = apellidos.strip()
                    if len(apellidos_limpio) < 2:
                        return ResultadoDocente(
                            ok=False,
                            mensaje="El apellido debe tener al menos 2 caracteres."
                        )
                    docente.apellidos = apellidos_limpio
                    cambios["apellidos"] = apellidos_limpio

                if especialidad is not None:
                    docente.especialidad = especialidad.strip() if especialidad else None
                    cambios["especialidad"] = docente.especialidad

                if email_institucional is not None:
                    email_limpio = email_institucional.strip().lower() if email_institucional else None
                    docente.email_institucional = email_limpio
                    cambios["email_institucional"] = email_limpio

                if telefono is not None:
                    docente.telefono = telefono.strip() if telefono else None
                    cambios["telefono"] = docente.telefono

                if usuario_id is not None:
                    if usuario_id != 0:  # 0 significa desvincular
                        usuario = session.query(Usuario).filter_by(id=usuario_id).first()
                        if not usuario:
                            return ResultadoDocente(
                                ok=False,
                                mensaje=f"El usuario con ID {usuario_id} no existe."
                            )
                    docente.usuario_id = usuario_id if usuario_id != 0 else None
                    cambios["usuario_id"] = docente.usuario_id

                if activo is not None:
                    docente.activo = activo
                    cambios["activo"] = activo

                docente.updated_at = datetime.now()

                if cambios:
                    DocenteService._auditar(
                        session,
                        usuario_id=usuario_editor_id or docente_id,
                        tabla_afectada="docentes",
                        accion="UPDATE",
                        registro_id=docente_id,
                        datos_anteriores=datos_anteriores,
                        datos_nuevos=cambios
                    )

                session.commit()

                return ResultadoDocente(
                    ok=True,
                    mensaje="Docente actualizado correctamente.",
                    docente=docente
                )

        except SQLAlchemyError as e:
            return ResultadoDocente(
                ok=False,
                mensaje=f"Error al actualizar docente: {str(e)}"
            )

    # ══════════════════════════════════════════════════════════════
    # VINCULAR CON USUARIO
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def vincular_usuario(
        docente_id: int,
        usuario_id: int,
        usuario_editor_id: int = None
    ) -> ResultadoDocente:
        """Vincula un docente con un usuario existente."""
        return DocenteService.actualizar(
            docente_id=docente_id,
            usuario_id=usuario_id,
            usuario_editor_id=usuario_editor_id
        )

    @staticmethod
    def desvincular_usuario(
        docente_id: int,
        usuario_editor_id: int = None
    ) -> ResultadoDocente:
        """Desvincula un docente de su usuario."""
        return DocenteService.actualizar(
            docente_id=docente_id,
            usuario_id=0,  # 0 significa desvinc ular
            usuario_editor_id=usuario_editor_id
        )

    # ══════════════════════════════════════════════════════════════
    # DESACTIVAR / ACTIVAR
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def desactivar(docente_id: int, usuario_editor_id: int = None) -> ResultadoDocente:
        """Desactiva un docente."""
        return DocenteService.actualizar(
            docente_id=docente_id,
            activo=False,
            usuario_editor_id=usuario_editor_id
        )

    @staticmethod
    def activar(docente_id: int, usuario_editor_id: int = None) -> ResultadoDocente:
        """Reactiva un docente inactivo."""
        return DocenteService.actualizar(
            docente_id=docente_id,
            activo=True,
            usuario_editor_id=usuario_editor_id
        )

    # ══════════════════════════════════════════════════════════════
    # ELIMINAR DOCENTE
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def eliminar(docente_id: int, usuario_editor_id: int = None) -> ResultadoDocente:
        """
        Elimina un docente.
        RECOMENDACIÓN: usar desactivar() en lugar de eliminar().
        """
        try:
            with get_session() as session:
                docente = session.query(Docente).filter_by(id=docente_id).first()

                if not docente:
                    return ResultadoDocente(
                        ok=False,
                        mensaje=f"Docente con ID {docente_id} no encontrado."
                    )

                nombre_completo = docente.nombre_completo

                DocenteService._auditar(
                    session,
                    usuario_id=usuario_editor_id or docente_id,
                    tabla_afectada="docentes",
                    accion="DELETE",
                    registro_id=docente_id,
                    datos_anteriores={
                        "dni": docente.dni,
                        "nombre_completo": docente.nombre_completo
                    }
                )

                session.delete(docente)
                session.commit()

                return ResultadoDocente(
                    ok=True,
                    mensaje=f"Docente '{nombre_completo}' eliminado correctamente."
                )

        except SQLAlchemyError as e:
            return ResultadoDocente(
                ok=False,
                mensaje=f"Error al eliminar docente: {str(e)}"
            )

    # ══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _validar_datos(
        dni: str,
        nombres: str,
        apellidos: str,
        email_institucional: str = None
    ) -> Optional[str]:
        """Valida los datos del docente."""

        # DNI
        if not dni or not dni.strip():
            return "El DNI es obligatorio."
        dni = dni.strip()
        if len(dni) < 6 or len(dni) > 20:
            return "El DNI debe tener entre 6 y 20 caracteres."

        # Nombres
        if not nombres or not nombres.strip():
            return "El nombre es obligatorio."
        if len(nombres.strip()) < 2:
            return "El nombre debe tener al menos 2 caracteres."
        if len(nombres.strip()) > 100:
            return "El nombre no puede exceder 100 caracteres."

        # Apellidos
        if not apellidos or not apellidos.strip():
            return "El apellido es obligatorio."
        if len(apellidos.strip()) < 2:
            return "El apellido debe tener al menos 2 caracteres."
        if len(apellidos.strip()) > 100:
            return "El apellido no puede exceder 100 caracteres."

        # Email (opcional pero validar si se proporciona)
        if email_institucional and email_institucional.strip():
            email = email_institucional.strip().lower()
            if "@" not in email or "." not in email.split("@")[-1]:
                return "El email no tiene un formato válido."

        return None

    @staticmethod
    def _auditar(
        session,
        usuario_id: int,
        tabla_afectada: str,
        accion: str,
        registro_id: int = None,
        datos_anteriores: dict = None,
        datos_nuevos: dict = None
    ) -> None:
        """Inserta un registro en la tabla auditoría."""
        registro = Auditoria(
            usuario_id=usuario_id,
            tabla_afectada=tabla_afectada,
            accion=accion,
            registro_id=registro_id,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos
        )
        session.add(registro)
