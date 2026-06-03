import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui  import QPixmap, QFont, QIntValidator

from services.estudiante_service import EstudianteService


class FormularioEstudianteDialog(QDialog):

    def __init__(self, sesion, estudiante_id: int = None, parent=None):
        super().__init__(parent)
        self.sesion          = sesion
        self.estudiante_id   = estudiante_id   # None = modo nuevo
        self._foto_ruta      = None            # ruta seleccionada
        self._es_edicion     = estudiante_id is not None

        self.setModal(True)
        self.setFixedSize(640, 480)
        self.setWindowTitle(
            "Editar estudiante" if self._es_edicion else "Nuevo estudiante"
        )
        self.setWindowFlags(self.windowFlags() &
                            ~Qt.WindowType.WindowContextHelpButtonHint)

        self._construir_ui()
        self._cargar_carreras()

        if self._es_edicion:
            self._cargar_datos()

    # ──────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ──────────────────────────────────────────────────────────────
    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.setSpacing(0)

        # ── Título ────────────────────────────────────────────────
        lbl_titulo = QLabel(
            "Editar estudiante" if self._es_edicion else "Nuevo estudiante"
        )
        lbl_titulo.setObjectName("lbl_titulo_dialogo")
        font = QFont()
        font.setPointSize(16)
        font.setWeight(QFont.Weight.Medium)
        lbl_titulo.setFont(font)
        raiz.addWidget(lbl_titulo)
        raiz.addSpacing(4)

        lbl_sub = QLabel(
            "Modifica los campos y haz clic en Guardar."
            if self._es_edicion else
            "Completa los campos obligatorios (*) y guarda."
        )
        lbl_sub.setObjectName("lbl_subtitulo_dialogo")
        raiz.addWidget(lbl_sub)
        raiz.addSpacing(18)

        # ── Cuerpo: foto (izq) + campos (der) ─────────────────────
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)

        cuerpo.addWidget(self._panel_foto())
        cuerpo.addLayout(self._panel_campos(), 1)
        raiz.addLayout(cuerpo)

        raiz.addSpacing(14)

        # ── Mensaje de feedback ───────────────────────────────────
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setObjectName("lbl_mensaje")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setVisible(False)
        raiz.addWidget(self.lbl_mensaje)

        raiz.addStretch()

        # ── Separador ─────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separador")
        raiz.addWidget(sep)
        raiz.addSpacing(12)

        # ── Botones ───────────────────────────────────────────────
        pie = QHBoxLayout()
        pie.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setFixedSize(110, 38)
        self.btn_cancelar.clicked.connect(self.reject)
        pie.addWidget(self.btn_cancelar)

        pie.addSpacing(8)

        self.btn_guardar = QPushButton(
            "Guardar cambios" if self._es_edicion else "Registrar estudiante"
        )
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setFixedSize(170, 38)
        self.btn_guardar.clicked.connect(self._guardar)
        pie.addWidget(self.btn_guardar)

        raiz.addLayout(pie)

    # ── Panel izquierdo: foto ─────────────────────────────────────
    def _panel_foto(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("frame_foto")
        frame.setFixedWidth(130)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Contenedor de foto
        self.lbl_foto = QLabel()
        self.lbl_foto.setObjectName("lbl_foto")
        self.lbl_foto.setFixedSize(120, 130)
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto.setScaledContents(True)
        # Imagen placeholder
        self._mostrar_foto_placeholder()
        lay.addWidget(self.lbl_foto)

        self.btn_foto = QPushButton("📷 Cambiar foto")
        self.btn_foto.setObjectName("btn_foto")
        self.btn_foto.setFixedHeight(30)
        self.btn_foto.clicked.connect(self._seleccionar_foto)
        lay.addWidget(self.btn_foto)

        return frame

    # ── Panel derecho: campos del formulario ──────────────────────
    def _panel_campos(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setVerticalSpacing(12)

        def lbl(texto, obligatorio=False):
            t = f"{texto} <span style='color:#C0392B'>*</span>" if obligatorio else texto
            l = QLabel(t)
            l.setObjectName("lbl_etiqueta")
            return l

        def inp(name, placeholder="", max_len=100):
            i = QLineEdit()
            i.setObjectName(name)
            i.setPlaceholderText(placeholder)
            i.setMaxLength(max_len)
            i.setFixedHeight(34)
            return i

        # Fila 0: DNI | Código
        grid.addWidget(lbl("DNI", True),      0, 0)
        grid.addWidget(lbl("Código", True),   0, 1)
        self.inp_dni = inp("inp_dni", "72345678", 8)
        self.inp_dni.setValidator(QIntValidator(0, 99999999))
        self.inp_codigo = inp("inp_codigo", "2021100123", 20)
        grid.addWidget(self.inp_dni,    1, 0)
        grid.addWidget(self.inp_codigo, 1, 1)

        # Fila 1: Apellidos | Nombres
        grid.addWidget(lbl("Apellidos", True), 2, 0)
        grid.addWidget(lbl("Nombres", True),   2, 1)
        self.inp_apellidos = inp("inp_apellidos", "Pérez García")
        self.inp_nombres   = inp("inp_nombres",   "Juan Carlos")
        grid.addWidget(self.inp_apellidos, 3, 0)
        grid.addWidget(self.inp_nombres,   3, 1)

        # Fila 2: Carrera | Ciclo
        grid.addWidget(lbl("Carrera", True), 4, 0)
        grid.addWidget(lbl("Ciclo"),          4, 1)

        self.cmb_carrera = QComboBox()
        self.cmb_carrera.setObjectName("cmb_carrera")
        self.cmb_carrera.setFixedHeight(34)

        self.cmb_ciclo = QComboBox()
        self.cmb_ciclo.setObjectName("cmb_ciclo")
        self.cmb_ciclo.setFixedHeight(34)
        self.cmb_ciclo.addItem("— Sin especificar —", None)
        for c in range(1, 11):
            self.cmb_ciclo.addItem(str(c), c)

        grid.addWidget(self.cmb_carrera, 5, 0)
        grid.addWidget(self.cmb_ciclo,   5, 1)

        # Fila 3: Email | Teléfono
        grid.addWidget(lbl("Email"),     6, 0)
        grid.addWidget(lbl("Teléfono"),  6, 1)
        self.inp_email    = inp("inp_email",    "juan@unab.edu.pe", 120)
        self.inp_telefono = inp("inp_telefono", "987654321", 20)
        grid.addWidget(self.inp_email,    7, 0)
        grid.addWidget(self.inp_telefono, 7, 1)

        return grid

    # ──────────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ──────────────────────────────────────────────────────────────
    def _cargar_carreras(self):
        """Rellena el combo de carreras desde el servicio."""
        self.cmb_carrera.addItem("— Selecciona carrera —", None)
        for c in EstudianteService.listar_carreras():
            self.cmb_carrera.addItem(
                f"{c['nombre']}  ({c['facultad']})", c["id"]
            )

    def _cargar_datos(self):
        """Rellena el formulario con los datos del estudiante a editar."""
        datos = EstudianteService.obtener_por_id(self.estudiante_id)
        if not datos:
            self._mostrar_mensaje("No se encontró el estudiante.", error=True)
            return

        self.inp_dni.setText(datos["dni"])
        self.inp_codigo.setText(datos["codigo_estudiantil"])
        self.inp_apellidos.setText(datos["apellidos"])
        self.inp_nombres.setText(datos["nombres"])
        self.inp_email.setText(datos["email"])
        self.inp_telefono.setText(datos["telefono"])

        # Seleccionar carrera
        for i in range(self.cmb_carrera.count()):
            if self.cmb_carrera.itemData(i) == datos["carrera_id"]:
                self.cmb_carrera.setCurrentIndex(i)
                break

        # Seleccionar ciclo
        ciclo = datos.get("ciclo_actual")
        if ciclo:
            for i in range(self.cmb_ciclo.count()):
                if self.cmb_ciclo.itemData(i) == ciclo:
                    self.cmb_ciclo.setCurrentIndex(i)
                    break

        # Foto
        if datos.get("foto_ruta") and os.path.exists(datos["foto_ruta"]):
            self._foto_ruta = datos["foto_ruta"]
            self._mostrar_foto(datos["foto_ruta"])

        # En edición, DNI y código son de solo lectura
        self.inp_dni.setReadOnly(True)
        self.inp_codigo.setReadOnly(True)
        self.inp_dni.setToolTip("No se puede cambiar el DNI")
        self.inp_codigo.setToolTip("No se puede cambiar el código")

    # ──────────────────────────────────────────────────────────────
    # FOTO
    # ──────────────────────────────────────────────────────────────
    def _mostrar_foto_placeholder(self):
        """Muestra un cuadro gris con icono de persona."""
        self.lbl_foto.setText("👤")
        font = QFont()
        font.setPointSize(36)
        self.lbl_foto.setFont(font)
        self.lbl_foto.setStyleSheet(
            "background:#e8e6e0; border-radius:8px; color:#a09e96;"
        )

    def _mostrar_foto(self, ruta: str):
        pix = QPixmap(ruta)
        if not pix.isNull():
            self.lbl_foto.setPixmap(
                pix.scaled(120, 130,
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            )
            self.lbl_foto.setStyleSheet("border-radius:8px;")

    def _seleccionar_foto(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar foto",
            "",
            "Imágenes (*.jpg *.jpeg *.png *.webp)",
        )
        if ruta:
            self._foto_ruta = ruta
            self._mostrar_foto(ruta)

    # ──────────────────────────────────────────────────────────────
    # VALIDACIÓN Y GUARDADO
    # ──────────────────────────────────────────────────────────────
    def _validar_campos(self) -> str | None:
        """
        Retorna un mensaje de error si hay un campo inválido,
        o None si todo está bien.
        """
        if not self.inp_dni.text().strip():
            self.inp_dni.setFocus()
            return "El DNI es obligatorio."
        if len(self.inp_dni.text().strip()) != 8:
            self.inp_dni.setFocus()
            return "El DNI debe tener exactamente 8 dígitos."
        if not self.inp_codigo.text().strip():
            self.inp_codigo.setFocus()
            return "El código estudiantil es obligatorio."
        if not self.inp_apellidos.text().strip():
            self.inp_apellidos.setFocus()
            return "Los apellidos son obligatorios."
        if not self.inp_nombres.text().strip():
            self.inp_nombres.setFocus()
            return "Los nombres son obligatorios."
        if self.cmb_carrera.currentData() is None:
            return "Selecciona una carrera."
        return None

    def _guardar(self):
        """Valida y llama al servicio correspondiente."""
        error = self._validar_campos()
        if error:
            self._mostrar_mensaje(error, error=True)
            return

        datos = {
            "dni":                self.inp_dni.text().strip(),
            "codigo_estudiantil": self.inp_codigo.text().strip(),
            "apellidos":          self.inp_apellidos.text().strip(),
            "nombres":            self.inp_nombres.text().strip(),
            "carrera_id":         self.cmb_carrera.currentData(),
            "ciclo_actual":       self.cmb_ciclo.currentData(),
            "email":              self.inp_email.text().strip(),
            "telefono":           self.inp_telefono.text().strip(),
            "foto_ruta":          self._foto_ruta,
        }

        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando…")

        if self._es_edicion:
            resultado = EstudianteService.editar(
                self.estudiante_id, datos, self.sesion.usuario_id
            )
        else:
            resultado = EstudianteService.registrar(
                datos, self.sesion.usuario_id
            )

        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText(
            "Guardar cambios" if self._es_edicion else "Registrar estudiante"
        )

        if resultado.ok:
            self._mostrar_mensaje(resultado.mensaje, error=False)
            # Cerrar el diálogo con éxito tras una breve pausa
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1200, self.accept)
        else:
            self._mostrar_mensaje(resultado.mensaje, error=True)

    # ──────────────────────────────────────────────────────────────
    # UTILIDADES
    # ──────────────────────────────────────────────────────────────
    def _mostrar_mensaje(self, texto: str, error: bool = False):
        """Muestra feedback de éxito o error debajo del formulario."""
        if error:
            self.lbl_mensaje.setStyleSheet(
                "background:#fdf0ee; color:#C0392B; border:1px solid #f5c6c0;"
                "border-radius:7px; padding:8px 12px;"
            )
        else:
            self.lbl_mensaje.setStyleSheet(
                "background:#e8f8f2; color:#1D9E75; border:1px solid #a8e6cf;"
                "border-radius:7px; padding:8px 12px;"
            )
        self.lbl_mensaje.setText(texto)
        self.lbl_mensaje.setVisible(True)
