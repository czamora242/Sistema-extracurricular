"""
ui/asistencia/registro_asistencia_dialog.py   ──   Sprint 4 / HU-09
═══════════════════════════════════════════════════════════════════

Diálogo para registrar asistencia de estudiantes en una sesión.

LAYOUT:
  ┌──────────────────────────────────────────────────────┐
  │  Registrar Asistencia          [✕ Cerrar]            │
  │──────────────────────────────────────────────────────│
  │  Taller: [Danzas Folklóricas ▼]                      │
  │  Sesión: [Sesión 3 — 03/06/2025 ▼]                   │
  │                                                       │
  │  28/30 inscritos | Sesión programada                 │
  │──────────────────────────────────────────────────────│
  │  🔍 [Buscar por nombre…]                             │
  │──────────────────────────────────────────────────────│
  │  ☑ | Nombre    | DNI | Presente | Ausente | Hora   │
  │──────────────────────────────────────────────────────│
  │  ☑ | María… | 12345678 | ✓      |        | 14:02   │
  │  ☐ | Juan…  | 87654321 |        | ✓      |        │
  │──────────────────────────────────────────────────────│
  │  [✓ Todos presente] [✗ Todos ausente]                │
  │                                                       │
  │  28 de 30 presentes (93%)                            │
  │──────────────────────────────────────────────────────│
  │                    [Cancelar] [Guardar asistencia]   │
  └──────────────────────────────────────────────────────┘

NOMBRES DE PROPIEDADES (objectName):
  cmb_taller, cmb_sesion, inp_buscar, tbl_asistencia
  btn_todos_presente, btn_todos_ausente, btn_limpiar
  lbl_info_sesion, lbl_estado, btn_guardar, btn_cancelar
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox,
    QLineEdit, QCheckBox, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui  import QColor, QFont

from services.asistencia_service import AsistenciaService
from services.taller_service import TallerService


class RegistroAsistenciaDialog(QDialog):
    """
    USO:
        dlg = RegistroAsistenciaDialog(sesion=sesion_usuario, parent=self)
        dlg.exec()
    """

    COLUMNAS = [
        (0, "☑",          40),
        (1, "Nombre",    250),
        (2, "DNI",       100),
        (3, "Carrera",   150),
        (4, "Presente",   80),
        (5, "Ausente",    80),
        (6, "Hora",      120),
    ]

    def __init__(self, sesion_usuario, parent=None):
        super().__init__(parent)
        self.sesion       = sesion_usuario
        self._datos_inscritos = []
        self._asistencias = {}  # {estudiante_id: presente}
        self._timer = QTimer(singleShot=True, interval=300)
        self._timer.timeout.connect(self._filtrar_tabla)

        self.setModal(True)
        self.setMinimumSize(940, 600)
        self.setWindowTitle("Registrar Asistencia")
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
        lbl_titulo = QLabel("Registrar Asistencia")
        lbl_titulo.setObjectName("lbl_titulo_dialogo")
        f = QFont(); f.setPointSize(16); f.setWeight(QFont.Weight.Medium)
        lbl_titulo.setFont(f)
        raiz.addWidget(lbl_titulo)
        raiz.addSpacing(12)

        # Selecciones
        sel = QHBoxLayout()

        sel.addWidget(QLabel("Taller:"))
        self.cmb_taller = QComboBox()
        self.cmb_taller.setObjectName("cmb_taller")
        self.cmb_taller.setFixedHeight(32)
        self.cmb_taller.currentIndexChanged.connect(self._on_taller_cambio)
        sel.addWidget(self.cmb_taller, 1)

        sel.addSpacing(16)

        sel.addWidget(QLabel("Sesión:"))
        self.cmb_sesion = QComboBox()
        self.cmb_sesion.setObjectName("cmb_sesion")
        self.cmb_sesion.setFixedHeight(32)
        self.cmb_sesion.currentIndexChanged.connect(self._on_sesion_cambio)
        sel.addWidget(self.cmb_sesion, 1)

        raiz.addLayout(sel)
        raiz.addSpacing(10)

        # Info sesión
        self.lbl_info_sesion = QLabel("")
        self.lbl_info_sesion.setObjectName("lbl_info_sesion")
        raiz.addWidget(self.lbl_info_sesion)
        raiz.addSpacing(12)

        # Búsqueda
        busqueda = QHBoxLayout()
        busqueda.addWidget(QLabel("🔍"))
        self.inp_buscar = QLineEdit()
        self.inp_buscar.setObjectName("inp_buscar")
        self.inp_buscar.setPlaceholderText("Buscar por nombre o DNI…")
        self.inp_buscar.setFixedHeight(32)
        self.inp_buscar.textChanged.connect(self._timer.start)
        busqueda.addWidget(self.inp_buscar)
        raiz.addLayout(busqueda)
        raiz.addSpacing(10)

        # Tabla
        self.tbl_asistencia = self._construir_tabla()
        self.tbl_asistencia.setObjectName("tbl_asistencia")
        raiz.addWidget(self.tbl_asistencia, 1)

        raiz.addSpacing(10)

        # Controles
        controles = QHBoxLayout()

        self.btn_todos_presente = QPushButton("✓ Todos presente")
        self.btn_todos_presente.setObjectName("btn_todos_presente")
        self.btn_todos_presente.setFixedHeight(32)
        self.btn_todos_presente.clicked.connect(
            lambda: self._marcar_todos(True))
        controles.addWidget(self.btn_todos_presente)

        controles.addSpacing(6)

        self.btn_todos_ausente = QPushButton("✗ Todos ausente")
        self.btn_todos_ausente.setObjectName("btn_todos_ausente")
        self.btn_todos_ausente.setFixedHeight(32)
        self.btn_todos_ausente.clicked.connect(
            lambda: self._marcar_todos(False))
        controles.addWidget(self.btn_todos_ausente)

        controles.addSpacing(6)

        self.btn_limpiar = QPushButton("Limpiar búsqueda")
        self.btn_limpiar.setObjectName("btn_limpiar")
        self.btn_limpiar.setFixedHeight(32)
        self.btn_limpiar.clicked.connect(self.inp_buscar.clear)
        controles.addWidget(self.btn_limpiar)

        controles.addStretch()

        raiz.addLayout(controles)
        raiz.addSpacing(8)

        # Estado
        self.lbl_estado = QLabel("")
        self.lbl_estado.setObjectName("lbl_estado_asistencia")
        raiz.addWidget(self.lbl_estado)

        raiz.addSpacing(10)

        # Botones pie
        pie = QHBoxLayout()
        pie.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setFixedSize(100, 34)
        self.btn_cancelar.clicked.connect(self.reject)
        pie.addWidget(self.btn_cancelar)

        pie.addSpacing(8)

        self.btn_guardar = QPushButton("Guardar asistencia")
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setFixedHeight(34)
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self._guardar_asistencia)
        pie.addWidget(self.btn_guardar)

        raiz.addLayout(pie)

    def _construir_tabla(self) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(len(self.COLUMNAS))
        tbl.setHorizontalHeaderLabels([c[1] for c in self.COLUMNAS])
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setShowGrid(False)
        tbl.setSortingEnabled(False)
        tbl.verticalHeader().setVisible(False)

        for idx, _, ancho in self.COLUMNAS:
            tbl.setColumnWidth(idx, ancho)

        tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setDefaultSectionSize(32)
        return tbl

    # ──────────────────────────────────────────────────────────────
    def _cargar_datos(self):
        """Carga datos de ciclos y talleres."""
        ciclos = AsistenciaService.listar_ciclos()
        for ciclo in ciclos:
            self.cmb_taller.addItem(ciclo["nombre"], ciclo["id"])

    def _on_taller_cambio(self):
        """Al cambiar taller, cargar sesiones."""
        self.cmb_sesion.blockSignals(True)
        self.cmb_sesion.clear()
        self.cmb_sesion.blockSignals(False)

        taller_id = self.cmb_taller.currentData()
        if not taller_id:
            return

        sesiones = AsistenciaService.listar_sesiones(taller_id)
        for ses in sesiones:
            texto = f"Sesión {ses['numero']} — {ses['fecha']} {ses['hora']}"
            self.cmb_sesion.addItem(texto, ses["id"])

    def _on_sesion_cambio(self):
        """Al cambiar sesión, cargar inscritos."""
        sesion_id = self.cmb_sesion.currentData()
        if not sesion_id:
            self.tbl_asistencia.setRowCount(0)
            self.btn_guardar.setEnabled(False)
            return

        # Obtener inscritos
        taller_id = self.cmb_taller.currentData()
        from services.taller_service import TallerService
        self._datos_inscritos = TallerService.listar_inscritos(
            taller_id, solo_activos=True
        )

        # Obtener asistencias previas si existen
        self._asistencias = {}
        asistencias_previas = AsistenciaService.obtener_por_sesion(sesion_id)
        for a in asistencias_previas:
            self._asistencias[a["estudiante_id"]] = a["presente"]

        # Actualizar info
        resumen = AsistenciaService.obtener_resumen_sesion(sesion_id)
        self.lbl_info_sesion.setText(
            f"<b>{len(self._datos_inscritos)} inscritos</b> | "
            f"{resumen.get('presentes', 0)} presentes "
            f"({resumen.get('porcentaje', 0):.1f}%)"
        )

        # Poblar tabla
        self._poblar_tabla()

        # Si hay asistencias previas, no permitir guardar de nuevo
        self.btn_guardar.setEnabled(len(self._asistencias) == 0)

    def _poblar_tabla(self):
        """Llena la tabla con inscritos."""
        self.tbl_asistencia.setRowCount(len(self._datos_inscritos))

        for fila, est in enumerate(self._datos_inscritos):
            est_id = est["estudiante_id"]
            presente = self._asistencias.get(est_id)

            # Columna 0: Checkbox selección (para futura multi-selección)
            item_sel = QTableWidgetItem("☑")
            item_sel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_asistencia.setItem(fila, 0, item_sel)

            # Columna 1: Nombre
            item_nombre = QTableWidgetItem(est["nombre_completo"])
            item_nombre.setData(Qt.ItemDataRole.UserRole, est_id)
            self.tbl_asistencia.setItem(fila, 1, item_nombre)

            # Columna 2: DNI
            item_dni = QTableWidgetItem(est["dni"])
            item_dni.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_asistencia.setItem(fila, 2, item_dni)

            # Columna 3: Carrera
            item_carrera = QTableWidgetItem(est["carrera"])
            self.tbl_asistencia.setItem(fila, 3, item_carrera)

            # Columna 4: Presente (checkbox editable)
            item_presente = QTableWidgetItem()
            item_presente.setCheckState(
                Qt.CheckState.Checked if presente is True else Qt.CheckState.Unchecked
            )
            item_presente.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_presente.setData(Qt.ItemDataRole.UserRole + 1, "presente")
            self.tbl_asistencia.setItem(fila, 4, item_presente)

            # Columna 5: Ausente (checkbox editable)
            item_ausente = QTableWidgetItem()
            item_ausente.setCheckState(
                Qt.CheckState.Checked if presente is False else Qt.CheckState.Unchecked
            )
            item_ausente.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ausente.setData(Qt.ItemDataRole.UserRole + 1, "ausente")
            self.tbl_asistencia.setItem(fila, 5, item_ausente)

            # Columna 6: Hora (solo lectura si hay previo)
            hora_texto = ""
            if presente is not None:
                hora_texto = "14:02"  # Placeholder - obtener de BD en producción
            item_hora = QTableWidgetItem(hora_texto)
            item_hora.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_asistencia.setItem(fila, 6, item_hora)

        self._actualizar_estado()

    def _marcar_todos(self, presente: bool):
        """Marca todos los estudiantes como presente/ausente."""
        for fila in range(self.tbl_asistencia.rowCount()):
            item_presente = self.tbl_asistencia.item(fila, 4)
            item_ausente = self.tbl_asistencia.item(fila, 5)

            if presente:
                item_presente.setCheckState(Qt.CheckState.Checked)
                item_ausente.setCheckState(Qt.CheckState.Unchecked)
            else:
                item_presente.setCheckState(Qt.CheckState.Unchecked)
                item_ausente.setCheckState(Qt.CheckState.Checked)

        self._actualizar_estado()

    def _filtrar_tabla(self):
        """Filtra tabla por búsqueda."""
        texto = self.inp_buscar.text().lower()

        for fila in range(self.tbl_asistencia.rowCount()):
            nombre = self.tbl_asistencia.item(fila, 1).text().lower()
            dni = self.tbl_asistencia.item(fila, 2).text().lower()

            visible = texto in nombre or texto in dni
            self.tbl_asistencia.setRowHidden(fila, not visible)

    def _actualizar_estado(self):
        """Actualiza el label de estado."""
        presentes = 0
        for fila in range(self.tbl_asistencia.rowCount()):
            item = self.tbl_asistencia.item(fila, 4)
            if item.checkState() == Qt.CheckState.Checked:
                presentes += 1

        total = self.tbl_asistencia.rowCount()
        pct = (presentes / total * 100) if total > 0 else 0

        self.lbl_estado.setText(
            f"<b>{presentes} de {total} presentes ({pct:.1f}%)</b>"
        )

    def _guardar_asistencia(self):
        """Guarda todos los registros de asistencia."""
        sesion_id = self.cmb_sesion.currentData()
        if not sesion_id:
            QMessageBox.warning(self, "Error", "Selecciona una sesión")
            return

        registrados = 0
        errores = 0

        for fila in range(self.tbl_asistencia.rowCount()):
            nombre_item = self.tbl_asistencia.item(fila, 1)
            est_id = nombre_item.data(Qt.ItemDataRole.UserRole)

            item_presente = self.tbl_asistencia.item(fila, 4)
            presente = item_presente.checkState() == Qt.CheckState.Checked

            res = AsistenciaService.registrar(
                sesion_id, est_id, presente, self.sesion.usuario_id
            )

            if res.ok:
                registrados += 1
            else:
                errores += 1

        mensaje = f"Asistencia registrada: {registrados} estudiantes"
        if errores > 0:
            mensaje += f" ({errores} errores)"

        QMessageBox.information(self, "Éxito", mensaje)
        
        # Cerrar tras 1200ms
        from PySide6.QtCore import QTimer as QtTimer
        QtTimer.singleShot(1200, self.accept)
