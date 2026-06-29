"""
services/bienes_service.py   ──   EP-06 Bienes Patrimoniales
═══════════════════════════════════════════════════════════

Servicio de gestión de bienes patrimoniales y asignaciones.

FUNCIONALIDADES:
  • Registro de bienes patrimoniales
  • Asignación de bienes a espacios
  • Seguimiento de estado
  • Auditoría de movimientos
"""

from dataclasses import dataclass
from datetime import datetime,date
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.connection import get_session
from models import BienPatrimonial, AsignacionBien, Auditoria


@dataclass
class ResultadoBien:
    """Estructura de respuesta estándar."""
    ok: bool
    mensaje: str
    datos: Optional[Any] = None
    lista: Optional[List[Dict]] = None


class BienesService:
    """Servicio de gestión de bienes patrimoniales."""

    @staticmethod
    def registrar(datos: dict, usuario_id: int) -> ResultadoBien:
        """
        Registra un nuevo bien patrimonial.

        PARÁMETROS:
          {
            "codigo_patrimonial": "BP-2025-001",
            "descripcion": "Proyector Epson",
            "categoria": "Equipos",
            "valor_adquisicion": 5000.00,
            "fecha_adquisicion": "2024-01-15",
            "observaciones": "En buen estado"
          }
        """

        if datos["valor_adquisicion"] <= 0:
            return ResultadoBien(
                ok=False,
                mensaje="El valor de adquisición debe ser mayor que cero."
            )
        
        if datos["fecha_adquisicion"] > date.today():

            return ResultadoBien(
                ok=False,
                mensaje="La fecha de adquisición no puede ser posterior a la fecha actual."
            )

        obligatorios = ["codigo_patrimonial", "descripcion"]
        for campo in obligatorios:
            if not datos.get(campo):
                return ResultadoBien(
                    ok=False,
                    mensaje=f"El campo '{campo}' es obligatorio"
                )

        try:
            with get_session() as session:
                # Verificar código único
                existe = session.query(BienPatrimonial).filter_by(
                    codigo_patrimonial=datos["codigo_patrimonial"]
                ).first()

                if existe:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Este código de bien ya existe"
                    )

                bien = BienPatrimonial(
                    codigo_patrimonial=datos["codigo_patrimonial"].strip(),
                    descripcion=datos["descripcion"].strip(),
                    categoria=datos.get("categoria", "").strip() or None,
                    valor_adquisicion=float(datos["valor_adquisicion"]) if datos.get("valor_adquisicion") else None,
                    fecha_adquisicion=datos.get("fecha_adquisicion"),
                    estado="Disponible",
                    observaciones=datos.get("observaciones", "").strip() or None
                )

                session.add(bien)
                session.flush()

                # Registrar auditoría
                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla_afectada="bienes_patrimoniales",
                    accion="INSERT",
                    registro_id=bien.id,
                    datos_nuevos={
                        "codigo_patrimonial": bien.codigo_patrimonial,
                        "descripcion": bien.descripcion,
                        "categoria": bien.categoria
                    }
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien patrimonial registrado exitosamente",
                    datos={"bien_id": bien.id}
                )

        except IntegrityError:
            return ResultadoBien(
                ok=False,
                mensaje="Ya existe un bien con ese código patrimonial."
            )

        except ValueError:
            return ResultadoBien(
                ok=False,
                mensaje="El valor de adquisición ingresado es inválido."
            )

        except SQLAlchemyError:
            return ResultadoBien(
                ok=False,
                mensaje="No fue posible guardar la información en la base de datos."
            )

        except Exception:
            return ResultadoBien(
                ok=False,
                mensaje="Ocurrió un error inesperado. Intente nuevamente."
            )

    @staticmethod
    def editar(bien_id: int, datos: dict, usuario_id: int) -> ResultadoBien:
        """Edita un bien patrimonial existente."""
        try:
            with get_session() as session:
                bien = session.query(BienPatrimonial).filter_by(id=bien_id).first()

                if not bien:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Bien no encontrado"
                    )

                datos_anteriores = {
                    "descripcion": bien.descripcion,
                    "categoria": bien.categoria,
                    "valor_adquisicion": float(bien.valor_adquisicion) if bien.valor_adquisicion else None,
                    "observaciones": bien.observaciones
                }

                # Actualizar campos
                if "descripcion" in datos:
                    bien.descripcion = datos["descripcion"].strip()
                if "categoria" in datos:
                    bien.categoria = datos["categoria"].strip() or None
                if "valor_adquisicion" in datos:
                    bien.valor_adquisicion = float(datos["valor_adquisicion"]) if datos["valor_adquisicion"] else None
                if "observaciones" in datos:
                    bien.observaciones = datos["observaciones"].strip() or None

                bien.updated_at = datetime.now()
                session.commit()

                # Registrar auditoría
                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla_afectada="bienes_patrimoniales",
                    accion="UPDATE",
                    registro_id=bien.id,
                    datos_anteriores=datos_anteriores,
                    datos_nuevos={
                        "descripcion": bien.descripcion,
                        "categoria": bien.categoria,
                        "valor_adquisicion": float(bien.valor_adquisicion) if bien.valor_adquisicion else None,
                        "observaciones": bien.observaciones
                    }
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien actualizado exitosamente"
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )

    @staticmethod
    def cambiar_estado(bien_id: int, nuevo_estado: str, usuario_id: int) -> ResultadoBien:
        """Cambia el estado de un bien."""
        estados_validos = ["Disponible", "Asignado", "Mantenimiento", "DeBaja"]

        if nuevo_estado not in estados_validos:
            return ResultadoBien(
                ok=False,
                mensaje=f"Estado inválido. Válidos: {', '.join(estados_validos)}"
            )

        try:
            with get_session() as session:
                bien = session.query(BienPatrimonial).filter_by(id=bien_id).first()

                if not bien:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Bien no encontrado"
                    )

                estado_anterior = bien.estado
                bien.estado = nuevo_estado
                bien.updated_at = datetime.now()
                session.commit()

                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla_afectada="bienes_patrimoniales",
                    accion="UPDATE",
                    registro_id=bien.id,
                    datos_anteriores={"estado": estado_anterior},
                    datos_nuevos={"estado": nuevo_estado}
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje=f"Estado cambiado a {nuevo_estado}"
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )

    @staticmethod
    def asignar(
        bien_id: int,
        docente_id: int = None,
        taller_id: int = None,
        fecha_devolucion: date = None,
        observaciones: str = None,
        usuario_id: int = None
    ) -> ResultadoBien:
        """
        Asigna un bien a docente y/o taller.
        
        PARÁMETROS:
            bien_id: ID del bien
            docente_id: ID del docente (opcional)
            taller_id: ID del taller (opcional)
            fecha_devolucion: Fecha esperada de devolución
            observaciones: Observaciones de la asignación
            usuario_id: Usuario que realiza la asignación
        """
        try:
            with get_session() as session:
                bien = session.query(BienPatrimonial).filter_by(id=bien_id).first()

                if not bien:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Bien no encontrado"
                    )

                if not bien.esta_disponible:
                    return ResultadoBien(
                        ok=False,
                        mensaje=f"El bien no está disponible (estado: {bien.estado})"
                    )

                asignacion = AsignacionBien(
                    bien_id=bien.id,
                    docente_id=docente_id,
                    taller_id=taller_id,
                    fecha_asignacion=date.today(),
                    fecha_devolucion_esperada=fecha_devolucion,
                    observaciones_asignacion=observaciones,
                    asignado_por=usuario_id,
                    estado_asignacion="Activo"
                )

                bien.estado = "Asignado"
                session.add(asignacion)
                session.commit()

                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla_afectada="asignaciones_bien",
                    accion="INSERT",
                    registro_id=asignacion.id,
                    datos_nuevos={
                        "bien_id": bien.id,
                        "docente_id": docente_id,
                        "taller_id": taller_id,
                        "fecha_asignacion": str(date.today())
                    }
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien asignado exitosamente",
                    datos={"asignacion_id": asignacion.id}
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )

    @staticmethod
    def devolver(
        asignacion_id: int,
        estado_conservacion: str = None,
        observaciones_devolucion: str = None,
        usuario_id: int = None
    ) -> ResultadoBien:
        """
        Registra la devolución de un bien.
        
        PARÁMETROS:
            asignacion_id: ID de la asignación
            estado_conservacion: Estado en que se devuelve
            observaciones_devolucion: Observaciones
            usuario_id: Usuario que recibe la devolución
        """
        estados_validos = ["Excelente", "Bueno", "Regular", "Malo", "Inservible"]
        
        if estado_conservacion and estado_conservacion not in estados_validos:
            return ResultadoBien(
                ok=False,
                mensaje=f"Estado de conservación inválido. Válidos: {', '.join(estados_validos)}"
            )

        try:
            with get_session() as session:
                asignacion = session.query(AsignacionBien).filter_by(id=asignacion_id).first()

                if not asignacion:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Asignación no encontrada"
                    )

                if asignacion.estado_asignacion != "Activo":
                    return ResultadoBien(
                        ok=False,
                        mensaje="Esta asignación ya fue devuelta"
                    )

                asignacion.fecha_devolucion_real = date.today()
                asignacion.estado_conservacion = estado_conservacion
                asignacion.observaciones_devolucion = observaciones_devolucion
                asignacion.estado_asignacion = "Devuelto"
                asignacion.updated_at = datetime.now()

                bien = asignacion.bien
                bien.estado = "Disponible"

                session.commit()

                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla_afectada="asignaciones_bien",
                    accion="UPDATE",
                    registro_id=asignacion.id,
                    datos_anteriores={"estado_asignacion": "Activo"},
                    datos_nuevos={
                        "estado_asignacion": "Devuelto",
                        "fecha_devolucion_real": str(date.today()),
                        "estado_conservacion": estado_conservacion
                    }
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien devuelto exitosamente"
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )

    @staticmethod
    def listar(filtro: dict = None) -> ResultadoBien:
        """Lista bienes con filtros opcionales."""
        try:
            with get_session() as session:
                query = session.query(BienPatrimonial)

                if filtro:
                    if filtro.get("categoria"):
                        query = query.filter(
                            BienPatrimonial.categoria.ilike(f"%{filtro['categoria']}%")
                        )
                    if filtro.get("estado"):
                        query = query.filter_by(estado=filtro["estado"])
                    if filtro.get("codigo"):
                        query = query.filter(
                            BienPatrimonial.codigo_patrimonial.ilike(f"%{filtro['codigo']}%")
                        )
                    if filtro.get("descripcion"):
                        query = query.filter(
                            BienPatrimonial.descripcion.ilike(f"%{filtro['descripcion']}%")
                        )

                bienes = query.order_by(BienPatrimonial.codigo_patrimonial).all()

                lista = [
                    {
                        "id": b.id,
                        "codigo_patrimonial": b.codigo_patrimonial,
                        "descripcion": b.descripcion,
                        "categoria": b.categoria or "Sin categoría",
                        "estado": b.estado,
                        "valor": f"S/. {float(b.valor_adquisicion):,.2f}" if b.valor_adquisicion else "N/A",
                        "asignacion_activa": b.asignacion_activa is not None
                    }
                    for b in bienes
                ]

                return ResultadoBien(
                    ok=True,
                    mensaje=f"Se encontraron {len(lista)} bienes",
                    lista=lista
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )

    @staticmethod
    def obtener_por_id(bien_id: int) -> ResultadoBien:
        """Obtiene los detalles completos de un bien."""
        try:
            with get_session() as session:
                bien = session.query(BienPatrimonial).filter_by(id=bien_id).first()

                if not bien:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Bien no encontrado"
                    )

                datos = {
                    "id": bien.id,
                    "codigo_patrimonial": bien.codigo_patrimonial,
                    "descripcion": bien.descripcion,
                    "categoria": bien.categoria,
                    "valor_adquisicion": float(bien.valor_adquisicion) if bien.valor_adquisicion else None,
                    "fecha_adquisicion": bien.fecha_adquisicion.isoformat() if bien.fecha_adquisicion else None,
                    "estado": bien.estado,
                    "observaciones": bien.observaciones,
                    "asignacion_activa": bien.asignacion_activa.id if bien.asignacion_activa else None,
                    "created_at": bien.created_at.strftime("%d/%m/%Y") if bien.created_at else "",
                }

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien obtenido",
                    datos=datos
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )

    @staticmethod
    def obtener_asignaciones(bien_id: int) -> ResultadoBien:
        """Obtiene historial de asignaciones de un bien."""
        try:
            with get_session() as session:
                asignaciones = session.query(AsignacionBien).filter_by(bien_id=bien_id).all()

                lista = [
                    {
                        "id": a.id,
                        "docente": a.docente.nombre_completo if a.docente else "N/A",
                        "taller": a.taller.nombre if a.taller else "N/A",
                        "fecha_asignacion": a.fecha_asignacion.strftime("%d/%m/%Y") if a.fecha_asignacion else "N/A",
                        "fecha_devolucion_esperada": a.fecha_devolucion_esperada.strftime("%d/%m/%Y") if a.fecha_devolucion_esperada else "N/A",
                        "fecha_devolucion_real": a.fecha_devolucion_real.strftime("%d/%m/%Y") if a.fecha_devolucion_real else "Aún asignado",
                        "estado": a.estado_asignacion,
                        "conservacion": a.estado_conservacion or "N/A"
                    }
                    for a in asignaciones
                ]

                return ResultadoBien(
                    ok=True,
                    mensaje="Asignaciones obtenidas",
                    lista=lista
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error: {str(e)}"
            )