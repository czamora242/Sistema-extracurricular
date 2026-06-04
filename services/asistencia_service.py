"""
services/asistencia_service.py   ──   Sprint 4 / EP-04
═══════════════════════════════════════════════════════

Servicio de control de asistencia a sesiones de talleres.
MVC puro: sin dependencias de Qt, reutilizable para FastAPI.

FUNCIONALIDADES:
  • Registrar asistencia de estudiantes en sesiones
  • Editar registros de asistencia
  • Calcular porcentaje de asistencia
  • Generar reportes por sesión y estudiante
  • Marcar todos en masa
  • Auditoría automática

NOTAS:
  • Tabla `asistencia`: (id, sesion_id, estudiante_id, presente, ...)
  • Vista `v_asistencia_resumen`: porcentaje agregado por estudiante
  • Validaciones: sesión existe, estudiante inscrito, no duplicados
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func
from database.connection import get_session
from models.asistencia import Asistencia
from models.sesion import Sesion
from models.inscripcion import Inscripcion
from models.estudiante import Estudiante
from models.taller import Taller
from models.ciclo_docente import CicloAcademico, Docente
from models.auditoria import Auditoria


# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class ResultadoAsistencia:
    """Estructura de respuesta estándar para operaciones de asistencia."""
    ok: bool
    mensaje: str
    datos: Optional[Any] = None
    lista: Optional[List[Dict]] = None


# ══════════════════════════════════════════════════════════════════════════════
class AsistenciaService:
    """Servicio de gestión de asistencia a sesiones."""

    @staticmethod
    def registrar(sesion_id: int, estudiante_id: int, presente: bool,
                  usuario_id: int) -> ResultadoAsistencia:
        """
        Registra la asistencia de un estudiante en una sesión.

        VALIDACIONES:
          • Sesión existe y pertenece a un taller activo
          • Estudiante está inscrito y activo en el taller
          • No hay duplicado de registro en la misma sesión
          • Estudiante no está retirado

        PARÁMETROS:
          sesion_id (int): ID de la sesión
          estudiante_id (int): ID del estudiante
          presente (bool): True si asistió, False si faltó
          usuario_id (int): Usuario que registra (para auditoría)

        RETORNA:
          ResultadoAsistencia con id del registro si OK

        EJEMPLOS:
          res = AsistenciaService.registrar(5, 123, True, 1)
          if res.ok:
              print(f"Asistencia registrada: {res.datos}")
        """
        with get_session() as session:
            try:
                # 1. Validar sesión
                sesion = session.query(Sesion).filter_by(id=sesion_id).first()
                if not sesion:
                    return ResultadoAsistencia(
                        ok=False,
                        mensaje="Sesión no encontrada"
                    )

                # 2. Validar taller está activo
                taller = session.query(Taller).filter_by(id=sesion.taller_id).first()
                if not taller or taller.estado != "Activo":
                    return ResultadoAsistencia(
                        ok=False,
                        mensaje="Taller no está activo"
                    )

                # 3. Validar inscripción activa
                inscripcion = session.query(Inscripcion).filter(
                    and_(
                        Inscripcion.taller_id == taller.id,
                        Inscripcion.estudiante_id == estudiante_id,
                        Inscripcion.estado == "Activo"
                    )
                ).first()
                if not inscripcion:
                    return ResultadoAsistencia(
                        ok=False,
                        mensaje="Estudiante no está inscrito o fue retirado"
                    )

                # 4. Validar no hay duplicado
                existe = session.query(Asistencia).filter(
                    and_(
                        Asistencia.sesion_id == sesion_id,
                        Asistencia.estudiante_id == estudiante_id
                    )
                ).first()
                if existe:
                    return ResultadoAsistencia(
                        ok=False,
                        mensaje="Ya hay registro de asistencia para este estudiante"
                    )

                # 5. Crear registro
                asistencia = Asistencia(
                    sesion_id=sesion_id,
                    estudiante_id=estudiante_id,
                    presente=presente,
                    usuario_id=usuario_id
                )
                session.add(asistencia)
                session.flush()

                # 6. Auditar
                Auditoria.registrar(
                    session=session,
                    tabla="asistencia",
                    operacion="INSERT",
                    registro_id=asistencia.id,
                    datos_nuevos={
                        "sesion_id": sesion_id,
                        "estudiante_id": estudiante_id,
                        "presente": presente
                    },
                    usuario_id=usuario_id
                )

                session.commit()

                return ResultadoAsistencia(
                    ok=True,
                    mensaje="Asistencia registrada correctamente",
                    datos=asistencia.id
                )

            except Exception as e:
                session.rollback()
                return ResultadoAsistencia(
                    ok=False,
                    mensaje=f"Error al registrar asistencia: {str(e)}"
                )

    @staticmethod
    def editar(asistencia_id: int, presente: bool,
               usuario_id: int) -> ResultadoAsistencia:
        """
        Edita un registro de asistencia existente.

        PARÁMETROS:
          asistencia_id (int): ID del registro a editar
          presente (bool): Nuevo valor de asistencia
          usuario_id (int): Usuario que edita (para auditoría)

        RETORNA:
          ResultadoAsistencia con resultado de operación
        """
        with get_session() as session:
            try:
                asistencia = session.query(Asistencia).filter_by(
                    id=asistencia_id
                ).first()

                if not asistencia:
                    return ResultadoAsistencia(
                        ok=False,
                        mensaje="Registro de asistencia no encontrado"
                    )

                # Guardar valores anteriores para auditoría
                datos_anteriores = {"presente": asistencia.presente}

                # Actualizar
                asistencia.presente = presente
                session.flush()

                # Auditar
                Auditoria.registrar(
                    session=session,
                    tabla="asistencia",
                    operacion="UPDATE",
                    registro_id=asistencia.id,
                    datos_anteriores=datos_anteriores,
                    datos_nuevos={"presente": presente},
                    usuario_id=usuario_id
                )

                session.commit()

                return ResultadoAsistencia(
                    ok=True,
                    mensaje="Asistencia actualizada correctamente"
                )

            except Exception as e:
                session.rollback()
                return ResultadoAsistencia(
                    ok=False,
                    mensaje=f"Error al editar asistencia: {str(e)}"
                )

    @staticmethod
    def obtener_por_sesion(sesion_id: int) -> List[Dict]:
        """
        Retorna todos los registros de asistencia de una sesión.

        RETORNA:
          List[dict]: [{
              "id", "estudiante_id", "nombre_completo", "dni",
              "carrera", "presente", "fecha_registro"
          }]
        """
        with get_session() as session:
            try:
                resultados = session.query(
                    Asistencia.id,
                    Asistencia.estudiante_id,
                    Estudiante.nombres,
                    Estudiante.apellidos,
                    Estudiante.dni,
                    Estudiante.carrera_id,
                    Asistencia.presente,
                    Asistencia.fecha_registro
                ).join(
                    Estudiante, Asistencia.estudiante_id == Estudiante.id
                ).filter(
                    Asistencia.sesion_id == sesion_id
                ).order_by(
                    Estudiante.nombres, Estudiante.apellidos
                ).all()

                datos = []
                for r in resultados:
                    datos.append({
                        "id": r.id,
                        "estudiante_id": r.estudiante_id,
                        "nombre_completo": f"{r.nombres} {r.apellidos}".strip(),
                        "dni": r.dni,
                        "presente": r.presente,
                        "fecha_registro": r.fecha_registro.strftime(
                            "%d/%m/%Y %H:%M"
                        ) if r.fecha_registro else None
                    })

                return datos

            except Exception as e:
                print(f"Error al obtener asistencia: {str(e)}")
                return []

    @staticmethod
    def obtener_por_estudiante_taller(estudiante_id: int,
                                      taller_id: int) -> List[Dict]:
        """
        Retorna historial de asistencia de un estudiante en un taller.

        RETORNA:
          List[dict]: [{
              "sesion_id", "numero", "fecha", "presente"
          }]
        """
        with get_session() as session:
            try:
                resultados = session.query(
                    Sesion.id,
                    Sesion.numero,
                    Sesion.fecha,
                    Asistencia.presente
                ).join(
                    Asistencia,
                    (Asistencia.sesion_id == Sesion.id) &
                    (Asistencia.estudiante_id == estudiante_id),
                    isouter=True
                ).filter(
                    Sesion.taller_id == taller_id
                ).order_by(
                    Sesion.numero
                ).all()

                datos = []
                for r in resultados:
                    datos.append({
                        "sesion_id": r.id,
                        "numero": r.numero,
                        "fecha": r.fecha.strftime("%d/%m/%Y") if r.fecha else None,
                        "presente": r.presente if r.presente is not None else None
                    })

                return datos

            except Exception as e:
                print(f"Error al obtener historial: {str(e)}")
                return []

    @staticmethod
    def calcular_porcentaje(estudiante_id: int, taller_id: int) -> float:
        """
        Calcula el porcentaje de asistencia de un estudiante en un taller.

        RETORNA:
          float: Porcentaje 0.0-100.0 (o 0.0 si sin sesiones)

        EJEMPLO:
          pct = AsistenciaService.calcular_porcentaje(123, 5)
          print(f"Asistencia: {pct:.1f}%")
        """
        with get_session() as session:
            try:
                # Total de sesiones esperadas
                total_sesiones = session.query(func.count(Sesion.id)).filter(
                    Sesion.taller_id == taller_id
                ).scalar() or 0

                if total_sesiones == 0:
                    return 0.0

                # Total de presencias
                presencias = session.query(
                    func.count(Asistencia.id)
                ).filter(
                    and_(
                        Asistencia.estudiante_id == estudiante_id,
                        Asistencia.presente == True
                    )
                ).scalar() or 0

                porcentaje = (presencias / total_sesiones) * 100
                return round(porcentaje, 2)

            except Exception as e:
                print(f"Error al calcular porcentaje: {str(e)}")
                return 0.0

    @staticmethod
    def marcar_todos(sesion_id: int, presente: bool,
                     usuario_id: int) -> ResultadoAsistencia:
        """
        Registra asistencia para todos los estudiantes inscritos en una sesión.

        USO: Marcar todos presentes o todos ausentes en una sesión.

        VALIDACIONES:
          • No registra si ya hay registros previos
          • Usa transacción para atomicidad

        PARÁMETROS:
          sesion_id (int): ID de la sesión
          presente (bool): Presente/Ausente para todos
          usuario_id (int): Usuario que marca

        RETORNA:
          ResultadoAsistencia con cantidad registrada
        """
        with get_session() as session:
            try:
                # 1. Obtener sesión y taller
                sesion = session.query(Sesion).filter_by(id=sesion_id).first()
                if not sesion:
                    return ResultadoAsistencia(
                        ok=False,
                        mensaje="Sesión no encontrada"
                    )

                # 2. Obtener inscritos activos
                inscritos = session.query(Inscripcion.estudiante_id).filter(
                    and_(
                        Inscripcion.taller_id == sesion.taller_id,
                        Inscripcion.estado == "Activo"
                    )
                ).all()

                registrados = 0
                for insc in inscritos:
                    est_id = insc[0]

                    # Validar no hay duplicado
                    existe = session.query(Asistencia).filter(
                        and_(
                            Asistencia.sesion_id == sesion_id,
                            Asistencia.estudiante_id == est_id
                        )
                    ).first()

                    if existe:
                        continue

                    # Crear registro
                    asistencia = Asistencia(
                        sesion_id=sesion_id,
                        estudiante_id=est_id,
                        presente=presente,
                        usuario_id=usuario_id
                    )
                    session.add(asistencia)
                    session.flush()

                    # Auditar
                    Auditoria.registrar(
                        session=session,
                        tabla="asistencia",
                        operacion="INSERT",
                        registro_id=asistencia.id,
                        datos_nuevos={
                            "sesion_id": sesion_id,
                            "estudiante_id": est_id,
                            "presente": presente,
                            "marcado_en_masa": True
                        },
                        usuario_id=usuario_id
                    )

                    registrados += 1

                session.commit()

                return ResultadoAsistencia(
                    ok=True,
                    mensaje=f"Se registraron {registrados} asistencias",
                    datos=registrados
                )

            except Exception as e:
                session.rollback()
                return ResultadoAsistencia(
                    ok=False,
                    mensaje=f"Error al marcar en masa: {str(e)}"
                )

    @staticmethod
    def existe_registro(sesion_id: int, estudiante_id: int) -> bool:
        """Verifica si hay registro previo de asistencia."""
        with get_session() as session:
            try:
                existe = session.query(Asistencia).filter(
                    and_(
                        Asistencia.sesion_id == sesion_id,
                        Asistencia.estudiante_id == estudiante_id
                    )
                ).first()

                return existe is not None

            except Exception as e:
                print(f"Error al verificar registro: {str(e)}")
                return False

    @staticmethod
    def listar_ciclos() -> List[Dict]:
        """Retorna ciclos académicos para combos."""
        with get_session() as session:
            try:
                ciclos = session.query(
                    CicloAcademico.id,
                    CicloAcademico.nombre
                ).filter(
                    CicloAcademico.estado == "Activo"
                ).order_by(
                    CicloAcademico.nombre.desc()
                ).all()

                return [
                    {"id": c.id, "nombre": c.nombre}
                    for c in ciclos
                ]

            except Exception:
                return []

    @staticmethod
    def listar_talleres(ciclo_id: Optional[int] = None) -> List[Dict]:
        """Retorna talleres activos para combos."""
        with get_session() as session:
            try:
                query = session.query(
                    Taller.id,
                    Taller.codigo,
                    Taller.nombre
                ).filter(
                    Taller.estado == "Activo"
                )

                if ciclo_id:
                    query = query.filter(Taller.ciclo_academico_id == ciclo_id)

                talleres = query.order_by(Taller.nombre).all()

                return [
                    {"id": t.id, "nombre": f"{t.codigo} - {t.nombre}"}
                    for t in talleres
                ]

            except Exception:
                return []

    @staticmethod
    def listar_sesiones(taller_id: int) -> List[Dict]:
        """Retorna sesiones de un taller."""
        with get_session() as session:
            try:
                sesiones = session.query(
                    Sesion.id,
                    Sesion.numero,
                    Sesion.fecha,
                    Sesion.hora_inicio,
                    Sesion.hora_fin
                ).filter(
                    Sesion.taller_id == taller_id
                ).order_by(
                    Sesion.numero
                ).all()

                return [
                    {
                        "id": s.id,
                        "numero": s.numero,
                        "fecha": s.fecha.strftime("%d/%m/%Y") if s.fecha else None,
                        "hora": f"{s.hora_inicio}-{s.hora_fin}" if s.hora_inicio else None
                    }
                    for s in sesiones
                ]

            except Exception:
                return []

    @staticmethod
    def obtener_resumen_sesion(sesion_id: int) -> Dict:
        """
        Retorna resumen de asistencia de una sesión.

        RETORNA:
          dict: {
              "total_inscritos": int,
              "presentes": int,
              "ausentes": int,
              "sin_registro": int,
              "porcentaje": float
          }
        """
        with get_session() as session:
            try:
                # Obtener sesión
                sesion = session.query(Sesion).filter_by(id=sesion_id).first()
                if not sesion:
                    return {}

                # Total inscritos activos
                total_inscritos = session.query(func.count(Inscripcion.id)).filter(
                    and_(
                        Inscripcion.taller_id == sesion.taller_id,
                        Inscripcion.estado == "Activo"
                    )
                ).scalar() or 0

                # Presentes
                presentes = session.query(func.count(Asistencia.id)).filter(
                    and_(
                        Asistencia.sesion_id == sesion_id,
                        Asistencia.presente == True
                    )
                ).scalar() or 0

                # Ausentes
                ausentes = session.query(func.count(Asistencia.id)).filter(
                    and_(
                        Asistencia.sesion_id == sesion_id,
                        Asistencia.presente == False
                    )
                ).scalar() or 0

                sin_registro = total_inscritos - (presentes + ausentes)

                porcentaje = (presentes / total_inscritos * 100
                             if total_inscritos > 0 else 0.0)

                return {
                    "total_inscritos": total_inscritos,
                    "presentes": presentes,
                    "ausentes": ausentes,
                    "sin_registro": sin_registro,
                    "porcentaje": round(porcentaje, 2)
                }

            except Exception:
                return {}

    @staticmethod
    def obtener_resumen_estudiante(estudiante_id: int,
                                   taller_id: int) -> Dict:
        """
        Retorna resumen de asistencia de un estudiante en un taller.

        RETORNA:
          dict: {
              "sesiones_esperadas": int,
              "presencias": int,
              "ausencias": int,
              "sin_registro": int,
              "porcentaje": float,
              "apto": bool (según umbral del taller)
          }
        """
        with get_session() as session:
            try:
                # Obtener taller para umbral
                taller = session.query(Taller).filter_by(id=taller_id).first()
                if not taller:
                    return {}

                # Total sesiones esperadas
                sesiones_esperadas = session.query(
                    func.count(Sesion.id)
                ).filter(
                    Sesion.taller_id == taller_id
                ).scalar() or 0

                # Presencias
                presencias = session.query(func.count(Asistencia.id)).filter(
                    and_(
                        Asistencia.estudiante_id == estudiante_id,
                        Asistencia.presente == True
                    )
                ).scalar() or 0

                # Ausencias
                ausencias = session.query(func.count(Asistencia.id)).filter(
                    and_(
                        Asistencia.estudiante_id == estudiante_id,
                        Asistencia.presente == False
                    )
                ).scalar() or 0

                sin_registro = sesiones_esperadas - (presencias + ausencias)

                porcentaje = (presencias / sesiones_esperadas * 100
                             if sesiones_esperadas > 0 else 0.0)

                apto = porcentaje >= taller.umbral_asistencia

                return {
                    "sesiones_esperadas": sesiones_esperadas,
                    "presencias": presencias,
                    "ausencias": ausencias,
                    "sin_registro": sin_registro,
                    "porcentaje": round(porcentaje, 2),
                    "umbral_requerido": taller.umbral_asistencia,
                    "apto": apto
                }

            except Exception:
                return {}
