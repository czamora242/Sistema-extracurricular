"""
ui/dialogo_vincular_docente_usuario.py   ──   Dialog para vincular Docente con Usuario
═══════════════════════════════════════════════════════════════════════════════

¿QUÉ HACE?
  Dialog mejorado que muestra:
  • Lista de docentes SIN usuario (lado izquierdo)
  • Lista de usuarios DISPONIBLES (lado derecho)
  • Botón para vincular (→)
  • Botón para desvinc ular (←)
  • Búsqueda en ambas listas

VENTAJAS:
  • Interfaz más intuitiva
  • Ves docentes y usuarios simultáneamente
  • Vincular es más visual

USO:
  from ui.dialogo_vincular_docente_usuario import DialogoVincularDocenteUsuario
  
  dialogo = DialogoVincularDocenteUsuario(sesion_usuario=self.sesion, parent=self)
  dialogo.exec()
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QMessageBox,
    QLabel, QHeaderView
)

from services.docente_service import DocenteService
from services.usuario_service import UsuarioService
from services.auth_service import SesionUsuario


class DialogoVincularDocenteUsuario(QDialog):
    """
    Dialog para vincular docentes con usuarios.
    
    INTERFAZ:
      Izquierda: Docentes sin usuario
      Derecha: Usuarios disponibles
      Centro: Botones para vincular/desvinc ular
    """

    def __init__(self, sesion_usuario: SesionUsuario, parent=None):
        super().__init__(parent)
        self.sesion_usuario = sesion_usuario

        self.setWindowTitle("Vincular Docentes con Usuarios")
        self.setMinimumSize(900, 500)
        self.setModal(True)

        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self) -> None:
        """Construye la interfaz."""
        raiz = QHBoxLayout()
        raiz.setSpacing(15)
        raiz.setContentsMargins(15, 15, 15, 15)

        # ════════════════════════════════════════════════════════
        # SECCIÓN IZQUIERDA: DOCENTES SIN USUARIO
        # ════════════════════════════════════════════════════════

        col_izq = QVBoxLayout()

        # Título y búsqueda
        titulo_iz = QLabel("📚 Docentes sin Usuario")
        titulo_iz.setStyleSheet("font-weight: bold; font-size: 12px;")
        col_izq.addWidget(titulo_iz)

        self.inp_buscar_docentes = QLineEdit()
        self.inp_buscar_docentes.setPlaceholderText("Buscar docente...")
        self.inp_buscar_docentes.textChanged.connect(self._filtrar_docentes)
        col_izq.addWidget(self.inp_buscar_docentes)

        # Tabla de docentes
        self.tabla_docentes = QTableWidget()
        self.tabla_docentes.setColumnCount(3)
        self.tabla_docentes.setHorizontalHeaderLabels(["ID", "DNI", "Nombre"])
        self.tabla_docentes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_docentes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_docentes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_docentes.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_docentes.setSelectionMode(QTableWidget.SingleSelection)
        col_izq.addWidget(self.tabla_docentes)

        raiz.addLayout(col_izq, 1)

        # ════════════════════════════════════════════════════════
        # SECCIÓN CENTRO: BOTONES
        # ════════════════════════════════════════════════════════

        col_centro = QVBoxLayout()
        col_centro.addStretch()

        # Botón vincular (→)
        btn_vincular = QPushButton("➜ Vincular →")
        btn_vincular.setMinimumHeight(40)
        btn_vincular.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_vincular.clicked.connect(self._vincular)
        col_centro.addWidget(btn_vincular)

        col_centro.addSpacing(10)

        # Botón desvinc ular (←)
        btn_desvincular = QPushButton("← Desvinc ular")
        btn_desvincular.setMinimumHeight(40)
        btn_desvincular.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        btn_desvincular.clicked.connect(self._desvincular)
        col_centro.addWidget(btn_desvincular)

        col_centro.addStretch()
        raiz.addLayout(col_centro, 0)

        # ════════════════════════════════════════════════════════
        # SECCIÓN DERECHA: USUARIOS DISPONIBLES
        # ════════════════════════════════════════════════════════

        col_der = QVBoxLayout()

        # Título y búsqueda
        titulo_der = QLabel("👤 Usuarios Disponibles")
        titulo_der.setStyleSheet("font-weight: bold; font-size: 12px;")
        col_der.addWidget(titulo_der)

        self.inp_buscar_usuarios = QLineEdit()
        self.inp_buscar_usuarios.setPlaceholderText("Buscar usuario...")
        self.inp_buscar_usuarios.textChanged.connect(self._filtrar_usuarios)
        col_der.addWidget(self.inp_buscar_usuarios)

        # Tabla de usuarios
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(3)
        self.tabla_usuarios.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre"])
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_usuarios.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_usuarios.setSelectionMode(QTableWidget.SingleSelection)
        col_der.addWidget(self.tabla_usuarios)

        raiz.addLayout(col_der, 1)

        # ════════════════════════════════════════════════════════
        # BOTONES INFERIORES
        # ════════════════════════════════════════════════════════

        botones_inf = QHBoxLayout()
        botones_inf.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedSize(100, 32)
        btn_cerrar.clicked.connect(self.accept)
        botones_inf.addWidget(btn_cerrar)

        layout_final = QVBoxLayout()
        layout_final.addLayout(raiz)
        layout_final.addLayout(botones_inf)

        self.setLayout(layout_final)

    def _cargar_datos(self) -> None:
        """Carga datos de docentes y usuarios."""
        # Docentes sin usuario
        resultado_docentes = DocenteService.listar(sin_usuario=True, activos_solo=True)
        self.docentes_datos = resultado_docentes.lista or []

        # Usuarios activos
        resultado_usuarios = UsuarioService.listar(activos_solo=True)
        self.usuarios_datos = resultado_usuarios.lista or []

        self._actualizar_tabla_docentes()
        self._actualizar_tabla_usuarios()

    def _actualizar_tabla_docentes(self) -> None:
        """Actualiza tabla de docentes."""
        self.tabla_docentes.setRowCount(len(self.docentes_datos))

        for row, docente in enumerate(self.docentes_datos):
            self.tabla_docentes.setItem(row, 0, QTableWidgetItem(str(docente["id"])))
            self.tabla_docentes.setItem(row, 1, QTableWidgetItem(docente["dni"]))
            self.tabla_docentes.setItem(row, 2, QTableWidgetItem(docente["nombre"]))

    def _actualizar_tabla_usuarios(self) -> None:
        """Actualiza tabla de usuarios."""
        self.tabla_usuarios.setRowCount(len(self.usuarios_datos))

        for row, usuario in enumerate(self.usuarios_datos):
            self.tabla_usuarios.setItem(row, 0, QTableWidgetItem(str(usuario["id"])))
            self.tabla_usuarios.setItem(row, 1, QTableWidgetItem(usuario["username"]))
            self.tabla_usuarios.setItem(row, 2, QTableWidgetItem(usuario["nombre"]))

    def _filtrar_docentes(self) -> None:
        """Filtra tabla de docentes."""
        buscar = self.inp_buscar_docentes.text().lower()

        for row in range(len(self.docentes_datos)):
            docente = self.docentes_datos[row]
            coincide = (
                buscar in str(docente["id"]).lower() or
                buscar in docente["dni"].lower() or
                buscar in docente["nombre"].lower()
            )
            self.tabla_docentes.setRowHidden(row, not coincide)

    def _filtrar_usuarios(self) -> None:
        """Filtra tabla de usuarios."""
        buscar = self.inp_buscar_usuarios.text().lower()

        for row in range(len(self.usuarios_datos)):
            usuario = self.usuarios_datos[row]
            coincide = (
                buscar in str(usuario["id"]).lower() or
                buscar in usuario["username"].lower() or
                buscar in usuario["nombre"].lower()
            )
            self.tabla_usuarios.setRowHidden(row, not coincide)

    def _vincular(self) -> None:
        """Vincula docente seleccionado con usuario seleccionado."""
        # Obtener filas seleccionadas
        docentes_sel = self.tabla_docentes.selectedIndexes()
        usuarios_sel = self.tabla_usuarios.selectedIndexes()

        if not docentes_sel or not usuarios_sel:
            QMessageBox.warning(
                self,
                "Error",
                "Selecciona un docente y un usuario."
            )
            return

        # Obtener datos
        row_docente = docentes_sel[0].row()
        row_usuario = usuarios_sel[0].row()

        docente = self.docentes_datos[row_docente]
        usuario = self.usuarios_datos[row_usuario]

        # Confirmar
        resultado = QMessageBox.question(
            self,
            "Confirmar vinculación",
            f"¿Vincular:\n\n"
            f"Docente: {docente['nombre']}\n"
            f"Usuario: {usuario['nombre']} ({usuario['username']})\n\n"
            f"¿Continuar?"
        )

        if resultado != QMessageBox.Yes:
            return

        # Vincular
        res = DocenteService.vincular_usuario(
            docente_id=docente["id"],
            usuario_id=usuario["id"],
            usuario_editor_id=self.sesion_usuario.usuario_id
        )

        if res.ok:
            QMessageBox.information(
                self,
                "✓ Éxito",
                f"Docente vinculado correctamente.\n\n"
                f"{docente['nombre']} → {usuario['username']}"
            )
            # Recargar datos
            self._cargar_datos()
            # Limpiar búsqueda
            self.inp_buscar_docentes.clear()
            self.inp_buscar_usuarios.clear()
        else:
            QMessageBox.warning(self, "Error", res.mensaje)

    def _desvincular(self) -> None:
        """Desvincula docente de su usuario actual."""
        # Necesita cargar docentes CON usuario
        resultado = DocenteService.listar(activos_solo=True)
        docentes_con_usuario = [d for d in (resultado.lista or []) if d["usuario"] != "Sin usuario"]

        if not docentes_con_usuario:
            QMessageBox.information(
                self,
                "Info",
                "No hay docentes vinculados a desvinc ular."
            )
            return

        # Dialog para seleccionar
        dialogo_sel = DialogoSeleccionarDocenteVinculado(docentes_con_usuario, parent=self)
        if dialogo_sel.exec():
            docente_id = dialogo_sel.obtener_docente_id()
            if docente_id:
                resultado = QMessageBox.question(
                    self,
                    "Confirmar",
                    "¿Desvinc ular este docente de su usuario?"
                )

                if resultado == QMessageBox.Yes:
                    res = DocenteService.desvincular_usuario(
                        docente_id=docente_id,
                        usuario_editor_id=self.sesion_usuario.usuario_id
                    )

                    if res.ok:
                        QMessageBox.information(self, "✓ Éxito", res.mensaje)
                        self._cargar_datos()
                    else:
                        QMessageBox.warning(self, "Error", res.mensaje)


class DialogoSeleccionarDocenteVinculado(QDialog):
    """Dialog para seleccionar un docente que ya tiene usuario."""

    def __init__(self, docentes, parent=None):
        super().__init__(parent)
        self.docentes = docentes
        self.docente_id_seleccionado = None

        self.setWindowTitle("Seleccionar Docente para Desvinc ular")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Selecciona docente a desvinc ular:"))

        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["ID", "Docente", "Usuario"])
        tabla.setSelectionBehavior(QTableWidget.SelectRows)
        tabla.setSelectionMode(QTableWidget.SingleSelection)
        tabla.setRowCount(len(docentes))

        for row, docente in enumerate(docentes):
            tabla.setItem(row, 0, QTableWidgetItem(str(docente["id"])))
            tabla.setItem(row, 1, QTableWidgetItem(docente["nombre"]))
            tabla.setItem(row, 2, QTableWidgetItem(docente["usuario"]))

        self.tabla = tabla
        layout.addWidget(tabla)

        botones = QHBoxLayout()
        botones.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        botones.addWidget(btn_ok)
        layout.addLayout(botones)

        self.setLayout(layout)

    def obtener_docente_id(self):
        """Retorna ID del docente seleccionado."""
        rows = self.tabla.selectedIndexes()
        if rows:
            row = rows[0].row()
            return int(self.tabla.item(row, 0).text())
        return None