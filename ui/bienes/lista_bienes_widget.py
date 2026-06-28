
"""
ui/bienes/lista_bienes_widget.py   ──   EP-06 Gestión de Bienes
═══════════════════════════════════════════════════════════════
Widget para listar, agregar, editar y gestionar bienes patrimoniales.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLineEdit, QComboBox, QFrame
)

from services.bienes_service import BienesService
from services.auth_service import SesionUsuario
from .formulario_bien_dialog import FormularioBienDialog


class ListaBienesWidget(QWidget):
    """Widget principal de gestión de bienes patrimoniales."""

    def __init__(self, sesion: SesionUsuario):
        super().__init__()
        self.sesion = sesion
        self.bienes_service = BienesService()
        self.bienes_filtrados = []

        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        # ── TÍTULO ────────────────────────────────────────────────
        titulo = QLabel("Gestión de Bienes Patrimoniales")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        titulo.setFont(font)
        layout.addWidget(titulo)

        # ── FILTROS ───────────────────────────────────────────────
        layout.addWidget(self._crear_panel_filtros())

        # ── TABLA ────────────────────────────────────────────────
        self.tabla_bienes = QTableWidget()
        self.tabla_bienes.setColumnCount(6)
        self.tabla_bienes.setHorizontalHeaderLabels([
            "Código", "Descripción", "Categoría", "Estado", "Valor", "Acciones"
        ])
        self.tabla_bienes.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.tabla_bienes.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla_bienes, 1)

        # ── BOTONES ───────────────────────────────────────────────
        botones = QHBoxLayout()

        btn_agregar = QPushButton("➕ Agregar Bien")
        btn_agregar.clicked.connect(self._abrir_agregar)
        botones.addWidget(btn_agregar)

        botones.addStretch()

        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.clicked.connect(self._cargar_datos)
        botones.addWidget(btn_actualizar)

        layout.addLayout(botones)

    def _crear_panel_filtros(self) -> QFrame:
        panel = QFrame()
        layout = QHBoxLayout(panel)

        layout.addWidget(QLabel("🔍 Buscar:"))
        self.inp_buscar = QLineEdit()
        self.inp_buscar.setPlaceholderText("Código o descripción...")
        self.inp_buscar.textChanged.connect(self._filtrar_tabla)
        layout.addWidget(self.inp_buscar, 1)

        layout.addWidget(QLabel("Categoría:"))
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItem("Todos", None)
        self.cmb_categoria.addItem("Mueble", "Mueble")
        self.cmb_categoria.addItem("Inmueble", "Inmueble")
        self.cmb_categoria.addItem("Electrónico", "Electrónico")
        self.cmb_categoria.currentIndexChanged.connect(self._filtrar_tabla)
        layout.addWidget(self.cmb_categoria)

        layout.addWidget(QLabel("Estado:"))
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItem("Todos", None)
        self.cmb_estado.addItem("Disponible", "Disponible")
        self.cmb_estado.addItem("Asignado", "Asignado")
        self.cmb_estado.addItem("Mantenimiento", "Mantenimiento")
        self.cmb_estado.addItem("De Baja", "DeBaja")
        self.cmb_estado.currentIndexChanged.connect(self._filtrar_tabla)
        layout.addWidget(self.cmb_estado)

        return panel

    def _cargar_datos(self) -> None:
        resultado = self.bienes_service.listar()

        if not resultado.ok:
            QMessageBox.warning(self, "Error", resultado.mensaje)
            return

        self.bienes_filtrados = resultado.lista or []
        self._mostrar_bienes()

    def _mostrar_bienes(self) -> None:
        self.tabla_bienes.setRowCount(len(self.bienes_filtrados))
        self.tabla_bienes.verticalHeader().setDefaultSectionSize(32)
        self.tabla_bienes.verticalHeader().setVisible(False)
        self.tabla_bienes.setWordWrap(False)

        for fila, bien in enumerate(self.bienes_filtrados):

            self.tabla_bienes.setItem(fila, 0, QTableWidgetItem(bien["codigo_patrimonial"]))
            self.tabla_bienes.setItem(fila, 1, QTableWidgetItem(bien["descripcion"]))
            self.tabla_bienes.setItem(fila, 2, QTableWidgetItem(bien["categoria"]))

            # Estado con color
            item_estado = QTableWidgetItem(bien["estado"])
            if bien["estado"] == "Disponible":
                item_estado.setBackground(QColor("#d1fae5"))
            elif bien["estado"] == "Asignado":
                item_estado.setBackground(QColor("#fef3c7"))
            elif bien["estado"] == "Mantenimiento":
                item_estado.setBackground(QColor("#fde68a"))
            elif bien["estado"] == "DeBaja":
                item_estado.setBackground(QColor("#fee2e2"))
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_bienes.setItem(fila, 3, item_estado)

            # Valor
            self.tabla_bienes.setItem(fila, 4, QTableWidgetItem(bien["valor"]))

            # Acciones
            btn_widget = QWidget()
            btn_widget.setFixedHeight(40)

            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Botón Editar
            btn_editar = QPushButton("Editar")
            btn_editar.setFixedSize(40, 24)
            btn_editar.setCursor(Qt.PointingHandCursor)
            btn_editar.setStyleSheet("""
            QPushButton{
                background-color:#2563eb;
                color:white;
                border:none;
                border-radius:4px;
                font-size:10px;
                font-weight:bold;
                padding:0px;
            }
            QPushButton:hover{
                background-color:#1d4ed8;
            }
            """)
            btn_editar.clicked.connect(lambda _, b=bien: self._editar_bien(b))
            btn_layout.addWidget(btn_editar)

            # Botón Dar baja
            btn_eliminar = QPushButton("Baja")
            btn_eliminar.setFixedSize(40, 24)
            btn_eliminar.setCursor(Qt.PointingHandCursor)
            btn_eliminar.setStyleSheet("""
            QPushButton{
                background-color:#dc2626;
                color:white;
                border:none;
                border-radius:4px;
                font-size:10px;
                font-weight:bold;
                padding:0px;
            }
            QPushButton:hover{
                background-color:#b91c1c;
            }
            """)
            btn_eliminar.clicked.connect(lambda _, b=bien: self._dar_de_baja(b))
            btn_layout.addWidget(btn_eliminar)

            self.tabla_bienes.setCellWidget(fila, 5, btn_widget)
            self.tabla_bienes.setRowHeight(fila, 48)

    def _filtrar_tabla(self) -> None:
        buscar = self.inp_buscar.text().lower()
        categoria = self.cmb_categoria.currentData()
        estado = self.cmb_estado.currentData()

        resultado = self.bienes_service.listar(filtro={
            "codigo": buscar or None,
            "descripcion": buscar or None,
            "categoria": categoria,
            "estado": estado
        })

        if resultado.ok:
            self.bienes_filtrados = resultado.lista or []
            self._mostrar_bienes()

    def _abrir_agregar(self) -> None:
        dlg = FormularioBienDialog(sesion=self.sesion,parent=self)
        if dlg.exec():
            self._cargar_datos()

    def _editar_bien(self, bien: dict) -> None:
        dlg = FormularioBienDialog(sesion=self.sesion,bien_id=bien["id"],parent=self)
        if dlg.exec():
            self._cargar_datos()

    def _dar_de_baja(self, bien: dict) -> None:
        respuesta = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Dar de baja el bien {bien['codigo_patrimonial']}?"
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        resultado = self.bienes_service.cambiar_estado(
            bien["id"],
            "DeBaja",
            self.sesion.usuario_id
        )

        if resultado.ok:
            QMessageBox.information(self, "Éxito", "Bien dado de baja")
            self._cargar_datos()
        else:
            QMessageBox.critical(self, "Error", resultado.mensaje)

