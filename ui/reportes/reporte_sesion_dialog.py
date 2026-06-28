"""
ui/asistencia/reporte_asistencia_dialog.py   ──   Sprint 4 / HU-10
═══════════════════════════════════════════════════════════════════

Diálogo para visualizar reportes de asistencia de un taller.
Muestra la asistencia por sesión y permite exportar/filtrar.

LAYOUT:
  ┌──────────────────────────────────────────────────┐
  │  Reporte de Asistencia      [✕ Cerrar]            │
  │──────────────────────────────────────────────────│
  │  Taller: [Danzas Folklóricas ▼]                  │
  │  📊 Sesión 1 — 01/06/2025      Realizada         │
  │  ✓ 28 presentes | ✗ 2 ausentes | ⚠ 0 justif.   │
  │  Asistencia: 93.3% (umbral: 80%)                 │
  │──────────────────────────────────────────────────│
  │  Nombre | DNI | Est. | Obs.                      │
  │  María... | 12345678 | P |                       │
  │  Juan... | 87654321 | A | ...                    │
  │──────────────────────────────────────────────────│
  │  [Anterior] [Siguiente] [Exportar PDF]            │
  │                    [Cerrar]                       │
  └──────────────────────────────────────────────────┘
"""

from datetime import date
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from services.asistencia_service import AsistenciaService
from services.taller_service import TallerService


class ReporteAsistenciaDialog(QDialog):
    """
    USO:
        dlg = ReporteAsistenciaDialog(sesion=sesion_usuario, parent=self)
        dlg.exec()
    """

    def __init__(self, sesion_usuario, parent=None):
        super().__init__(parent)
        self.sesion = sesion_usuario
        self.taller_actual = None
        self.sesion_actual = None
        self.sesiones = []
        self.idx_sesion = 0

        self.setModal(True)
        self.setMinimumSize(1000, 650)
        self.setWindowTitle("Reporte de Asistencia")
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._construir_ui()
        self._cargar_datos()

    # ──────────────────────────────────────────────────────────────
    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 16, 20, 16)
        raiz.setSpacing(0)

        # Título
        lbl_titulo = QLabel("Reporte de Asistencia")
        lbl_titulo.setObjectName("lbl_titulo_dialogo")
        f = QFont(); f.setPointSize(16); f.setWeight(QFont.Weight.Medium)
        lbl_titulo.setFont(f)
        raiz.addWidget(lbl_titulo)
        raiz.addSpacing(12)

        # Selector de taller
        sel = QHBoxLayout()
        sel.addWidget(QLabel("Taller:"))
        self.cmb_taller = QComboBox()
        self.cmb_taller.setObjectName("cmb_taller")
        self.cmb_taller.setFixedHeight(32)
        self.cmb_taller.currentIndexChanged.connect(self._on_taller_cambio)
        sel.addWidget(self.cmb_taller, 1)
        sel.addStretch()
        raiz.addLayout(sel)
        raiz.addSpacing(12)

        # Info de sesión actual
        self.lbl_info_sesion = QLabel("")
        self.lbl_info_sesion.setObjectName("lbl_info_sesion")
        f = QFont(); f.setPointSize(11); f.setWeight(QFont.Weight.Medium)
        self.lbl_info_sesion.setFont(f)
        raiz.addWidget(self.lbl_info_sesion)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setObjectName("lbl_resumen_asistencia")
        raiz.addWidget(self.lbl_resumen)
        raiz.addSpacing(10)

        # Tabla de asistencia
        self.tbl_asistencia = self._construir_tabla()
        raiz.addWidget(self.tbl_asistencia, 1)

        raiz.addSpacing(10)

        # Controles de sesión
        controles = QHBoxLayout()

        self.btn_anterior = QPushButton("◀ Sesión anterior")
        self.btn_anterior.setObjectName("btn_anterior")
        self.btn_anterior.setFixedHeight(32)
        self.btn_anterior.clicked.connect(self._sesion_anterior)
        controles.addWidget(self.btn_anterior)

        controles.addSpacing(6)

        self.btn_siguiente = QPushButton("Sesión siguiente ▶")
        self.btn_siguiente.setObjectName("btn_siguiente")
        self.btn_siguiente.setFixedHeight(32)
        self.btn_siguiente.clicked.connect(self._sesion_siguiente)
        controles.addWidget(self.btn_siguiente)

        controles.addStretch()

        self.btn_exportar = QPushButton("📥 Exportar PDF")
        self.btn_exportar.setObjectName("btn_exportar")
        self.btn_exportar.setFixedHeight(32)
        self.btn_exportar.clicked.connect(self._exportar_pdf)
        controles.addWidget(self.btn_exportar)

        raiz.addLayout(controles)
        raiz.addSpacing(10)

        # Botón cerrar
        pie = QHBoxLayout()
        pie.addStretch()

        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setObjectName("btn_cerrar")
        self.btn_cerrar.setFixedSize(100, 34)
        self.btn_cerrar.clicked.connect(self.accept)
        pie.addWidget(self.btn_cerrar)

        raiz.addLayout(pie)

    def _construir_tabla(self) -> QTableWidget:
        tbl = QTableWidget()

        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels([
            "Nombre",
            "DNI",
            "Estado",
            "Observación"
        ])

        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)

        tbl.setAlternatingRowColors(True)
        tbl.setShowGrid(False)
        tbl.setSortingEnabled(False)
        tbl.verticalHeader().setVisible(False)

        tbl.setColumnWidth(0, 350)
        tbl.setColumnWidth(1, 120)
        tbl.setColumnWidth(2, 100)
        tbl.setColumnWidth(3, 300)

        return tbl

    # ──────────────────────────────────────────────────────────────
    def _cargar_datos(self):
        """Carga talleres activos."""
        talleres = TallerService.buscar(estado="Activo")

        if not talleres:
            self.cmb_taller.addItem("❌ No hay talleres activos", None)
            return

        for taller in talleres:
            self.cmb_taller.addItem(
                f"{taller['nombre']} ({taller['docente']})",
                taller["id"]
            )

    def _on_taller_cambio(self):
        """Al cambiar taller, cargar sesiones."""
        taller_id = self.cmb_taller.currentData()
        if not taller_id:
            self.sesiones = []
            self.idx_sesion = 0
            self.tbl_asistencia.setRowCount(0)
            return

        self.taller_actual = taller_id
        self.sesiones = TallerService.listar_sesiones(taller_id)
        self.idx_sesion = 0

        if not self.sesiones:
            self.lbl_info_sesion.setText("⚠️  Este taller no tiene sesiones.")
            self.lbl_resumen.setText("")
            self.tbl_asistencia.setRowCount(0)
            return

        self._mostrar_sesion()

    def _mostrar_sesion(self):
        """Muestra la sesión actual."""
        if not self.sesiones or self.idx_sesion < 0 or self.idx_sesion >= len(
            self.sesiones
        ):
            self.tbl_asistencia.setRowCount(0)
            return

        sesion = self.sesiones[self.idx_sesion]
        sesion_id = sesion["id"]
        self.sesion_actual = sesion_id

        # Actualizar info
        self.lbl_info_sesion.setText(
            f"📅 Sesión {sesion['numero']} — {sesion['fecha']}   |   "
            f"⏰ {sesion['hora_inicio']} a {sesion['hora_fin']}   |   "
            f"Estado: {sesion['estado']}"
        )

        # Obtener resumen
        resumen = AsistenciaService.obtener_resumen_sesion(sesion_id)
        self.lbl_resumen.setText(
            f"✓ {resumen['presentes']} presentes   |   "
            f"✗ {resumen['ausentes']} ausentes    |   "
            f"⚠ {resumen['justificados']} justificados   |   "
            f"<b>Asistencia: {resumen['porcentaje']:.1f}%</b>"
        )

        # Obtener asistencias
        asistencias = AsistenciaService.obtener_por_sesion(sesion_id)

        # Obtener nombres de estudiantes (necesita inscripcion_id)
        from database.connection import get_session
        from models import Inscripcion

        estudiantes_map = {}
        try:
            with get_session() as session:
                inscripciones = session.query(Inscripcion).filter(
                    Inscripcion.taller_id == self.taller_actual
                ).all()
                for i in inscripciones:
                    estudiantes_map[i.id] = {
                        "nombre": i.estudiante.nombre_completo,
                        "dni": i.estudiante.dni,
                    }
        except:
            pass

        # Poblar tabla
        self.tbl_asistencia.setRowCount(len(asistencias))

        for fila, asist in enumerate(asistencias):
            insc_id = asist["inscripcion_id"]
            est_info = estudiantes_map.get(insc_id, {
                "nombre": "Desconocido",
                "dni": "---"
            })

            # Nombre
            item_nombre = QTableWidgetItem(est_info["nombre"])
            self.tbl_asistencia.setItem(fila, 0, item_nombre)

            # DNI
            item_dni = QTableWidgetItem(est_info["dni"])
            item_dni.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_asistencia.setItem(fila, 1, item_dni)

            # Estado
            item_estado = QTableWidgetItem(asist["estado_legible"])
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color según estado
            if asist["estado"] == "P":
                item_estado.setBackground(QColor("#d5f4e6"))
            elif asist["estado"] == "A":
                item_estado.setBackground(QColor("#fadbd8"))
            elif asist["estado"] == "J":
                item_estado.setBackground(QColor("#fef5e7"))

            self.tbl_asistencia.setItem(fila, 2, item_estado)

            # Observación
            obs = asist.get("observacion", "")
            item_obs = QTableWidgetItem(obs)
            self.tbl_asistencia.setItem(fila, 3, item_obs)

        # Actualizar botones
        self.btn_anterior.setEnabled(self.idx_sesion > 0)
        self.btn_siguiente.setEnabled(self.idx_sesion < len(self.sesiones) - 1)

    def _sesion_anterior(self):
        """Ir a sesión anterior."""
        if self.idx_sesion > 0:
            self.idx_sesion -= 1
            self._mostrar_sesion()

    def _sesion_siguiente(self):
        """Ir a sesión siguiente."""
        if self.idx_sesion < len(self.sesiones) - 1:
            self.idx_sesion += 1
            self._mostrar_sesion()

    def _exportar_pdf(self):
        if not self.sesion_actual:
            QMessageBox.warning(
                self,
                "Exportar PDF",
                "No hay una sesión seleccionada."
            )
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte",
            f"reporte_sesion_{self.sesion_actual}.pdf",
            "PDF (*.pdf)"
        )

        if not archivo:
            return

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle
            )
            from reportlab.lib.styles import getSampleStyleSheet

            doc = SimpleDocTemplate(archivo, pagesize=letter)
            elementos = []
            estilos = getSampleStyleSheet()

            # ─────────────────────────────
            # Título
            # ─────────────────────────────
            elementos.append(
                Paragraph(
                    "REPORTE DE ASISTENCIA",
                    estilos["Title"]
                )
            )

            elementos.append(Spacer(1, 12))

            # ─────────────────────────────
            # Datos de sesión
            # ─────────────────────────────
            sesion = self.sesiones[self.idx_sesion]

            elementos.append(
                Paragraph(
                    f"<b>Taller:</b> {self.cmb_taller.currentText()}",
                    estilos["Normal"]
                )
            )

            elementos.append(
                Paragraph(
                    f"<b>Sesión:</b> {sesion['numero']}",
                    estilos["Normal"]
                )
            )

            elementos.append(
                Paragraph(
                    f"<b>Fecha:</b> {sesion['fecha']}",
                    estilos["Normal"]
                )
            )

            elementos.append(
                Paragraph(
                    f"<b>Horario:</b> {sesion['hora_inicio']} - {sesion['hora_fin']}",
                    estilos["Normal"]
                )
            )

            elementos.append(
                Paragraph(
                    f"<b>Estado:</b> {sesion['estado']}",
                    estilos["Normal"]
                )
            )

            elementos.append(Spacer(1, 12))

            # ─────────────────────────────
            # Resumen
            # ─────────────────────────────
            resumen = AsistenciaService.obtener_resumen_sesion(
                self.sesion_actual
            )

            elementos.append(
                Paragraph(
                    f"""
                    <b>Presentes:</b> {resumen['presentes']}<br/>
                    <b>Ausentes:</b> {resumen['ausentes']}<br/>
                    <b>Justificados:</b> {resumen['justificados']}<br/>
                    <b>Porcentaje:</b> {resumen['porcentaje']:.1f}%
                    """,
                    estilos["Normal"]
                )
            )

            elementos.append(Spacer(1, 15))

            # ─────────────────────────────
            # Tabla
            # ─────────────────────────────
            datos_tabla = [
                ["Nombre", "DNI", "Estado", "Observación"]
            ]

            for fila in range(self.tbl_asistencia.rowCount()):

                nombre = self.tbl_asistencia.item(fila, 0)
                dni = self.tbl_asistencia.item(fila, 1)
                estado = self.tbl_asistencia.item(fila, 2)
                obs = self.tbl_asistencia.item(fila, 3)

                datos_tabla.append([
                    nombre.text() if nombre else "",
                    dni.text() if dni else "",
                    estado.text() if estado else "",
                    obs.text() if obs else ""
                ])

            tabla = Table(
                datos_tabla,
                colWidths=[180, 80, 80, 180]
            )

            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

                ('GRID', (0, 0), (-1, -1), 1, colors.black),

                ('ALIGN', (1, 1), (2, -1), 'CENTER'),

                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
            ]))

            elementos.append(tabla)

            elementos.append(Spacer(1, 20))

            elementos.append(
                Paragraph(
                    f"Generado el {date.today().strftime('%d/%m/%Y')}",
                    estilos["Italic"]
                )
            )

            doc.build(elementos)

            QMessageBox.information(
                self,
                "PDF generado",
                f"Reporte exportado correctamente:\n\n{archivo}"
            )

        except ImportError:
            QMessageBox.critical(
                self,
                "Error",
                "ReportLab no está instalado.\n\n"
                "Ejecute:\n\npip install reportlab"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo generar el PDF.\n\n{str(e)}"
            )