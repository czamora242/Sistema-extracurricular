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
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func
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

        PARÁMETRO datos (dict):
          {
            "codigo": "BP-2025-001",
            "descripcion": "Proyector Epson",
            "tipo": "Mueble",
            "valor_adquisicion": 5000.00,
            "fecha_adquisicion": "2024-01-15",
            "ubicacion": "Pabellón A",
            "estado": "Activo"
          }
        """
        obligatorios = ["codigo", "descripcion", "tipo", "valor_adquisicion"]
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
                    codigo=datos["codigo"]
                ).first()

                if existe:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Este código de bien ya existe"
                    )

                bien = BienPatrimonial(
                    codigo=datos["codigo"],
                    descripcion=datos["descripcion"],
                    tipo=datos["tipo"],
                    valor_adquisicion=float(datos["valor_adquisicion"]),
                    fecha_adquisicion=datos.get("fecha_adquisicion"),
                    ubicacion=datos.get("ubicacion", "No asignado"),
                    estado=datos.get("estado", "Activo"),
                    observaciones=datos.get("observaciones", "")
                )

                session.add(bien)
                session.flush()

                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla="bienes_patrimoniales",
                    operacion="INSERT",
                    registro_id=bien.id,
                    cambios=f"Bien registrado: {bien.codigo}"
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien patrimonial registrado exitosamente",
                    datos={"bien_id": bien.id}
                )

        except Exception as e:
            return ResultadoBien(
                ok=False,
                mensaje=f"Error al registrar bien: {str(e)}"
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

                # Registrar cambios para auditoría
                cambios = []
                campos_actualizables = [
                    "descripcion", "tipo", "valor_adquisicion",
                    "ubicacion", "estado", "observaciones"
                ]

                for campo in campos_actualizables:
                    if campo in datos and datos[campo] != getattr(bien, campo):
                        cambios.append(f"{campo}: {getattr(bien, campo)} → {datos[campo]}")
                        setattr(bien, campo, datos[campo])

                if not cambios:
                    return ResultadoBien(
                        ok=True,
                        mensaje="No hay cambios para guardar"
                    )

                bien.updated_at = datetime.now()
                session.commit()

                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla="bienes_patrimoniales",
                    operacion="UPDATE",
                    registro_id=bien.id,
                    cambios="; ".join(cambios)
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
        estados_validos = ["Activo", "Deprecado", "Perdido", "En Reparación"]

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
                    tabla="bienes_patrimoniales",
                    operacion="UPDATE",
                    registro_id=bien.id,
                    cambios=f"Estado: {estado_anterior} → {nuevo_estado}"
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
    def asignar(bien_id: int, ubicacion: str, usuario_id: int) -> ResultadoBien:
        """Asigna un bien a una ubicación."""
        try:
            with get_session() as session:
                bien = session.query(BienPatrimonial).filter_by(id=bien_id).first()

                if not bien:
                    return ResultadoBien(
                        ok=False,
                        mensaje="Bien no encontrado"
                    )

                asignacion = AsignacionBien(
                    bien_patrimonial_id=bien.id,
                    ubicacion=ubicacion,
                    fecha_asignacion=datetime.now()
                )

                bien.ubicacion = ubicacion
                session.add(asignacion)
                session.commit()

                auditoria = Auditoria(
                    usuario_id=usuario_id,
                    tabla="asignaciones_bienes",
                    operacion="INSERT",
                    registro_id=asignacion.id,
                    cambios=f"Bien {bien.codigo} asignado a {ubicacion}"
                )
                session.add(auditoria)
                session.commit()

                return ResultadoBien(
                    ok=True,
                    mensaje="Bien asignado exitosamente"
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
                    if filtro.get("tipo"):
                        query = query.filter_by(tipo=filtro["tipo"])
                    if filtro.get("estado"):
                        query = query.filter_by(estado=filtro["estado"])
                    if filtro.get("codigo"):
                        query = query.filter(
                            BienPatrimonial.codigo.ilike(f"%{filtro['codigo']}%")
                        )

                bienes = query.all()

                lista = [
                    {
                        "id": b.id,
                        "codigo": b.codigo,
                        "descripcion": b.descripcion,
                        "tipo": b.tipo,
                        "estado": b.estado,
                        "ubicacion": b.ubicacion,
                        "valor": f"S/. {b.valor_adquisicion:,.2f}"
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
                    "codigo": bien.codigo,
                    "descripcion": bien.descripcion,
                    "tipo": bien.tipo,
                    "valor_adquisicion": bien.valor_adquisicion,
                    "fecha_adquisicion": bien.fecha_adquisicion,
                    "ubicacion": bien.ubicacion,
                    "estado": bien.estado,
                    "observaciones": bien.observaciones,
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
