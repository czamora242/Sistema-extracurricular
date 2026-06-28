"""
ui/asistencia/registro_asistencia_dialog.py   ──   ACTUALIZADO CON FILTRADO POR ROL
═══════════════════════════════════════════════════════════════════════════════════

Ahora filtra talleres según el rol:
  - Administrador → Ve todos los talleres
  - Docente → Ve solo sus talleres a cargo
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox,
    QLineEdit, QMessageBox, QCheckBox,QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from services.asistencia_service import AsistenciaService
from services.taller_service import TallerService


class RegistroAsistenciaDialog(QWidget):
    """
    USO:
        dlg = RegistroAsistenciaDialog(sesion=sesion_usuario, parent=self)
        if dlg.exec(): ...
    
    CAMBIO:
        Ahora usa TallerService.listar_para_asistencia(usuario_id, rol_nombre)
        para filtrar talleres según el rol del usuario.
    """

    COLUMNAS = [
        (0, "Nombre",    250),
        (1, "DNI",       100),
        (2, "Carrera",   150),
        (3, "Presente",   80),
        (4, "Ausente",    80),
        (5, "Justif.",    80),
    ]

    def __init__(self, sesion_usuario, parent=None):
        super().__init__(parent)
        self.sesion       = sesion_usuario
        self._inscritos   = []
        self._asistencias = {}
        self._timer = QTimer(singleShot=True, interval=300)
        self._timer.timeout.connect(self._filtrar_tabla)

        self.setMinimumSize(1000, 620)
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
        raiz.setContentsMargins(24, 20, 24, 16)
        raiz.setSpacing(0)

        # Título
        lbl_titulo = QLabel("Registrar Asistencia")
        lbl_titulo.setObjectName("lbl_titulo_dialogo")
        f = QFont(); f.setPointSize(20); f.setWeight(QFont.Weight.Bold)
        lbl_titulo.setFont(f)
        raiz.addWidget(lbl_titulo)
        raiz.addSpacing(10)

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

        self.btn_todos_presente = QPushButton("✓ Todos Presente")
        self.btn_todos_presente.setObjectName("btn_todos_presente")
        self.btn_todos_presente.setFixedHeight(32)
        self.btn_todos_presente.clicked.connect(
            lambda: self._marcar_todos("P"))
        controles.addWidget(self.btn_todos_presente)

        controles.addSpacing(6)

        self.btn_todos_ausente = QPushButton("✗ Todos Ausente")
        self.btn_todos_ausente.setObjectName("btn_todos_ausente")
        self.btn_todos_ausente.setFixedHeight(32)
        self.btn_todos_ausente.clicked.connect(
            lambda: self._marcar_todos("A"))
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
        tbl.itemChanged.connect(self._on_estado_cambiado)
        return tbl

    # ──────────────────────────────────────────────────────────────
    def _cargar_datos(self):
        """
        ✅ CAMBIO: Usa listar_para_asistencia() que filtra por rol
        
        Si es Administrador → Ve todos los talleres
        Si es Docente → Ve solo sus talleres a cargo
        """
        talleres = TallerService.listar_para_asistencia(
            usuario_id=self.sesion.usuario_id,
            rol_nombre=self.sesion.rol_nombre,
            estado="Activo"
        )
        
        if not talleres:
            if self.sesion.es_docente:
                mensaje = "❌ No tienes talleres asignados"
            else:
                mensaje = "❌ No hay talleres activos"
            self.cmb_taller.addItem(mensaje, None)
            return
        
        for taller in talleres:
            self.cmb_taller.addItem(
                f"{taller['nombre']} ({taller['docente']})",
                taller["id"]
            )

    def _on_estado_cambiado(self, item):
        """Permite marcar solo un estado (P/A/J) por fila."""
        col = item.column()
        if col not in (3, 4, 5):
            return
        if item.checkState() != Qt.CheckState.Checked:
            return
        self.tbl_asistencia.blockSignals(True)
        fila = item.row()
        for c in (3, 4, 5):
            if c != col:
                otro = self.tbl_asistencia.item(fila, c)
                if otro:
                    otro.setCheckState(Qt.CheckState.Unchecked)

        self.tbl_asistencia.blockSignals(False)
        self.btn_guardar.setEnabled(True)
        self._actualizar_estado()

    def _on_taller_cambio(self):
        """Al cambiar taller, cargar sesiones."""
        self.cmb_sesion.blockSignals(True)
        self.cmb_sesion.clear()
        self.cmb_sesion.blockSignals(False)

        taller_id = self.cmb_taller.currentData()
        if not taller_id:
            return

        sesiones = TallerService.listar_sesiones(taller_id)
        for ses in sesiones:
            texto = f"Sesión {ses['numero']} — {ses['fecha']}"
            self.cmb_sesion.addItem(texto, ses["id"])

    def _on_sesion_cambio(self):
        """Al cambiar sesión, cargar inscritos."""
        sesion_id = self.cmb_sesion.currentData()
        if not sesion_id:
            self.tbl_asistencia.setRowCount(0)
            self.btn_guardar.setEnabled(False)
            return

        taller_id = self.cmb_taller.currentData()
        self._inscritos = TallerService.listar_inscritos(
            taller_id, solo_activos=True
        )

        self._asistencias = {}
        asistencias_previas = AsistenciaService.obtener_por_sesion(sesion_id)
        for a in asistencias_previas:
            self._asistencias[a["inscripcion_id"]] = {
                "estado": a["estado"],
                "observacion": a.get("observacion", "")
            }

        presentes = sum(1 for a in asistencias_previas if a["estado"] == "P")
        justificados = sum(1 for a in asistencias_previas if a["estado"] == "J")
        
        self.lbl_info_sesion.setText(
            f"<b>{len(self._inscritos)} inscritos</b> | "
            f"{presentes} presentes | {justificados} justificados"
        )

        self._poblar_tabla()
        self.btn_guardar.setEnabled(len(self._asistencias) == 0)

    def _poblar_tabla(self):
        """Llena la tabla con inscritos."""
        self.tbl_asistencia.blockSignals(True)
        self.tbl_asistencia.setRowCount(len(self._inscritos))
        for fila, est in enumerate(self._inscritos):
            insc_id = est["inscripcion_id"]
            prev = self._asistencias.get(insc_id, {})
            
            # Nombre
            item_nombre = QTableWidgetItem(est["nombre_completo"])
            item_nombre.setData(Qt.ItemDataRole.UserRole, insc_id)
            self.tbl_asistencia.setItem(fila, 0, item_nombre)
            
            # DNI
            item_dni = QTableWidgetItem(est["dni"])
            item_dni.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_asistencia.setItem(fila, 1, item_dni)
            
            # Carrera
            item_carrera = QTableWidgetItem(est["carrera"])
            self.tbl_asistencia.setItem(fila, 2, item_carrera)
            
            # Presente, Ausente, Justificado
            for col_idx in (3, 4, 5):
                item = QTableWidgetItem()
                item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled |
                    Qt.ItemFlag.ItemIsUserCheckable
                )
                self.tbl_asistencia.setItem(fila, col_idx, item)

        self.tbl_asistencia.blockSignals(False)
        self._actualizar_estado()

    def _marcar_todos(self, estado: str):
        """Marca todos los estudiantes con el estado indicado."""
        col_map = {"P": 3, "A": 4, "J": 5}
        self.tbl_asistencia.blockSignals(True)
        for fila in range(self.tbl_asistencia.rowCount()):
            self.tbl_asistencia.item(fila, 3).setCheckState(Qt.CheckState.Unchecked)
            self.tbl_asistencia.item(fila, 4).setCheckState(Qt.CheckState.Unchecked)
            self.tbl_asistencia.item(fila, 5).setCheckState(Qt.CheckState.Unchecked)
            self.tbl_asistencia.item(fila, col_map[estado]).setCheckState(Qt.CheckState.Checked)
        self.tbl_asistencia.blockSignals(False)
        self.btn_guardar.setEnabled(True)
        self._actualizar_estado()

    def _filtrar_tabla(self):
        """Filtra tabla por búsqueda."""
        texto = self.inp_buscar.text().lower()
        for fila in range(self.tbl_asistencia.rowCount()):
            nombre = self.tbl_asistencia.item(fila, 0).text().lower()
            dni = self.tbl_asistencia.item(fila, 1).text().lower()
            visible = texto in nombre or texto in dni
            self.tbl_asistencia.setRowHidden(fila, not visible)

    def _actualizar_estado(self):
        """Actualiza el label de estado."""
        presentes = 0
        ausentes = 0
        justificados = 0
        
        for fila in range(self.tbl_asistencia.rowCount()):
            if self.tbl_asistencia.item(fila, 3).checkState() == Qt.CheckState.Checked:
                presentes += 1
            elif self.tbl_asistencia.item(fila, 4).checkState() == Qt.CheckState.Checked:
                ausentes += 1
            elif self.tbl_asistencia.item(fila, 5).checkState() == Qt.CheckState.Checked:
                justificados += 1

        total = self.tbl_asistencia.rowCount()

        self.lbl_estado.setText(
            f"<b>{presentes} presentes | {justificados} justificados | "
            f"{ausentes} ausentes</b> (Total: {total})"
        )

    def _guardar_asistencia(self):
        """Guarda todos los registros de asistencia."""
        sesion_id = self.cmb_sesion.currentData()
        if not sesion_id:
            QMessageBox.warning(self, "Error", "Selecciona una sesión")
            return

        registrados = 0
        errores = 0
        errores_msg = []

        for fila in range(self.tbl_asistencia.rowCount()):
            nombre_item = self.tbl_asistencia.item(fila, 0)
            insc_id = nombre_item.data(Qt.ItemDataRole.UserRole)

            estado = None
            if self.tbl_asistencia.item(fila, 3).checkState() == Qt.CheckState.Checked:
                estado = "P"
            elif self.tbl_asistencia.item(fila, 4).checkState() == Qt.CheckState.Checked:
                estado = "A"
            elif self.tbl_asistencia.item(fila, 5).checkState() == Qt.CheckState.Checked:
                estado = "J"

            if not estado:
                errores += 1
                errores_msg.append(f"Fila {fila + 1}: Sin estado seleccionado")
                continue

            res = AsistenciaService.registrar(
                sesion_id=sesion_id,
                inscripcion_id=insc_id,
                estado=estado,
                usuario_id=self.sesion.usuario_id
            )

            if res.ok:
                registrados += 1
            else:
                errores += 1
                errores_msg.append(f"Fila {fila + 1}: {res.mensaje}")

        mensaje = f"✅ Asistencia registrada: {registrados} estudiantes"
        if errores > 0:
            mensaje += f"\n❌ Errores: {errores}"
            if errores_msg:
                mensaje += "\n" + "\n".join(errores_msg[:3])

        QMessageBox.information(self, "Resultado", mensaje)
        
        if registrados > 0 and errores == 0:
            self._on_sesion_cambio()