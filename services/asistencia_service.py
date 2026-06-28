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
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
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
    def registrar(sesion_id: int, inscripcion_id: int, estado: str,
                  usuario_id: int, observacion: str = "") -> ResultadoAsistencia:
        """
        ✅ Registra asistencia de un estudiante en una sesión.
        
        PARÁMETROS:
          sesion_id: ID de la sesión
          inscripcion_id: ID de la inscripción (NO estudiante_id)
          estado: "P" (Presente) | "A" (Ausente) | "J" (Justificado)
          observacion: Obligatorio si estado == "J"
        """
        if estado not in ("P", "A", "J"):
            return ResultadoAsistencia(False, f"Estado inválido: {estado}")
        
        if estado == "J" and not observacion.strip():
            return ResultadoAsistencia(False,
                "La observación es obligatoria para justificaciones.")
 
        try:
            with get_session() as session:
                # Verificar que inscripción existe
                insc = session.get(Inscripcion, inscripcion_id)
                if not insc:
                    return ResultadoAsistencia(False, "Inscripción no encontrada")
 
                # Verificar que sesión existe
                sesion = session.get(Sesion, sesion_id)
                if not sesion:
                    return ResultadoAsistencia(False, "Sesión no encontrada")
 
                # ¿Ya registrado?
                ya_registrado = session.query(Asistencia).filter(
                    Asistencia.inscripcion_id == inscripcion_id,
                    Asistencia.sesion_id == sesion_id
                ).first()
 
                if ya_registrado:
                    # Actualizar existente
                    ya_registrado.estado = estado
                    ya_registrado.observacion = observacion.strip() or None
                    ya_registrado.updated_at = datetime.now()
                else:
                    # Crear nuevo
                    session.add(Asistencia(
                        inscripcion_id=inscripcion_id,
                        sesion_id=sesion_id,
                        estado=estado,
                        observacion=observacion.strip() or None,
                        registrado_por=usuario_id,
                    ))
 
                session.commit()
                return ResultadoAsistencia(True, "Asistencia registrada correctamente")
 
        except SQLAlchemyError as e:
            return ResultadoAsistencia(False, f"Error al guardar: {e}")
 
        
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
    def obtener_por_sesion(sesion_id: int) -> list[dict]:
        """Obtiene todas las asistencias de una sesión."""
        try:
            with get_session() as session:
                asistencias = (session.query(Asistencia)
                              .filter(Asistencia.sesion_id == sesion_id)
                              .all())
                return [
                    {
                        "id": a.id,
                        "inscripcion_id": a.inscripcion_id,
                        "estado": a.estado,
                        "estado_legible": a.estado_legible,
                        "observacion": a.observacion or "",
                        "registrado_por": a.registrado_por,
                    }
                    for a in asistencias
                ]
        except SQLAlchemyError:
            return []
 
    @staticmethod
    def obtener_por_taller(taller_id: int) -> dict:
        """
        Obtiene resumen de asistencia por sesión para un taller.
        
        Retorna:
          {
            "sesion_1": {"presentes": 25, "ausentes": 3, ...},
            "sesion_2": {"presentes": 24, "ausentes": 4, ...},
            ...
          }
        """
        try:
            with get_session() as session:
                taller = session.get(Taller, taller_id)
                if not taller:
                    return {}
 
                resultado = {}
                for sesion in taller.sesiones:
                    resultado[f"sesion_{sesion.id}"] = {
                        "numero": sesion.numero_sesion,
                        "fecha": str(sesion.fecha),
                        **AsistenciaService.obtener_resumen_sesion(sesion.id)
                    }
 
                return resultado
        except SQLAlchemyError:
            return {}

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
    def listar_ciclos() -> list[dict]:
        """Lista ciclos académicos activos."""
        try:
            with get_session() as session:
                ciclos = (session.query(CicloAcademico)
                         .filter(CicloAcademico.activo == True)
                         .order_by(CicloAcademico.fecha_inicio.desc())
                         .all())
                return [
                    {"id": c.id, "nombre": c.nombre}
                    for c in ciclos
                ]
        except SQLAlchemyError:
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
                    Sesion.numero_sesion,
                    Sesion.fecha,
                    Sesion.hora_inicio,
                    Sesion.hora_fin
                ).filter(
                    Sesion.taller_id == taller_id
                ).order_by(
                    Sesion.numero_sesion
                ).all()

                return [
                    {
                        "id": s.id,
                        "numero": s.numero_sesion,
                        "fecha": s.fecha.strftime("%d/%m/%Y") if s.fecha else None,
                        "hora": f"{s.hora_inicio}-{s.hora_fin}" if s.hora_inicio else None
                    }
                    for s in sesiones
                ]

            except Exception as e:
                print(f"Error en obtener_resumen_sesion: {e}")
                return {"presentes": 0, "porcentaje": 0, "total": 0}

    @staticmethod
    def obtener_resumen_sesion(sesion_id: int) -> dict:
        """Obtiene resumen de asistencia de una sesión."""
        try:
            with get_session() as session:
                sesion = session.get(Sesion, sesion_id)
                if not sesion:
                    return {
                        "presentes": 0,
                        "ausentes": 0,
                        "justificados": 0,
                        "total": 0,
                        "porcentaje": 0
                    }
 
                presentes = sum(1 for a in sesion.asistencias if a.estado == "P")
                ausentes = sum(1 for a in sesion.asistencias if a.estado == "A")
                justificados = sum(1 for a in sesion.asistencias if a.estado == "J")
                total = len(sesion.asistencias)
                # Los que "cuentan" son P + J
                cuentan = presentes + justificados
                pct = (cuentan / total * 100) if total > 0 else 0
                return {
                    "presentes": presentes,
                    "ausentes": ausentes,
                    "justificados": justificados,
                    "total": total,
                    "cuentan_asistencia": cuentan,
                    "porcentaje": pct
                }
        except SQLAlchemyError:
            return {
                "presentes": 0,
                "ausentes": 0,
                "justificados": 0,
                "total": 0,
                "porcentaje": 0
            }

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
    
    @staticmethod
    def obtener_aprobacion_estudiante(inscripcion_id: int,umbral_asistencia: int) -> dict:
        """
        Evalúa si un estudiante cumple con el umbral de asistencia.
        
        Cuenta: P + J (Presente + Justificado)
        No cuenta: A (Ausente)
        """
        try:
            with get_session() as session:
                insc = session.get(Inscripcion, inscripcion_id)
                if not insc:
                    return {"apto": False, "razon": "Inscripción no encontrada"}
 
                asistencias = session.query(Asistencia).filter(
                    Asistencia.inscripcion_id == inscripcion_id
                ).all()
 
                if not asistencias:
                    return {
                        "apto": False,
                        "razon": "Sin sesiones registradas",
                        "presentes": 0,
                        "total": 0,
                        "porcentaje": 0
                    }
 
                cuentan = sum(1 for a in asistencias
                            if a.estado in ("P", "J"))
                total = len(asistencias)
                pct = (cuentan / total * 100)
 
                apto = pct >= umbral_asistencia
 
                return {
                    "apto": apto,
                    "presentes": cuentan,
                    "total": total,
                    "porcentaje": pct,
                    "umbral": umbral_asistencia,
                    "razon": f"{pct:.1f}% {'≥' if apto else '<'} {umbral_asistencia}%"
                }
        except SQLAlchemyError as e:
            return {"apto": False, "razon": f"Error: {e}"}
