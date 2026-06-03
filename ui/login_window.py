from PySide6.QtCore    import Qt, QTimer
from PySide6.QtGui     import QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QApplication, QSizePolicy
)

from services.auth_service import AuthService, SesionUsuario


class LoginWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.sesion_activa: SesionUsuario | None = None
        self._intentos_ui = 0   # contador visual para feedback progresivo

        self._configurar_ventana()
        self._construir_ui()
        self._conectar_señales()

    # CONFIGURACIÓN INICIAL

    def _configurar_ventana(self) -> None:
        """
        Configura propiedades básicas de la ventana.

        setWindowFlags: elimina el botón de maximizar y el de ayuda
        que Qt añade por defecto en QDialog.
        """
        self.setWindowTitle("Sistema de Talleres — UNAB")
        self.setFixedSize(420, 520)                            # tamaño fijo, no redimensionable
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.MSWindowsFixedSizeDialogHint         # sin botón maximizar
        )
        # Centrar en pantalla
        pantalla = QApplication.primaryScreen().geometry()
        x = (pantalla.width()  - self.width())  // 2
        y = (pantalla.height() - self.height()) // 2
        self.move(x, y)

        # Estilos CSS — Qt soporta un subconjunto de CSS llamado QSS
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f7f4;
            }
            QLabel#titulo {
                font-size: 22px;
                font-weight: 600;
                color: #1a1a18;
            }
            QLabel#subtitulo {
                font-size: 13px;
                color: #73726c;
            }
            QLabel#etiqueta {
                font-size: 13px;
                font-weight: 500;
                color: #3d3d3a;
                margin-top: 6px;
            }
            QLineEdit {
                padding: 10px 14px;
                border: 1px solid #d4d3cc;
                border-radius: 8px;
                font-size: 14px;
                background-color: #ffffff;
                color: #1a1a18;
            }
            QLineEdit:focus {
                border: 1.5px solid #534AB7;
                outline: none;
            }
            QLineEdit[error="true"] {
                border: 1.5px solid #C0392B;
            }
            QPushButton#btn_ingresar {
                background-color: #534AB7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: 500;
                margin-top: 8px;
            }
            QPushButton#btn_ingresar:hover {
                background-color: #4339A0;
            }
            QPushButton#btn_ingresar:pressed {
                background-color: #362E87;
            }
            QPushButton#btn_ingresar:disabled {
                background-color: #a09ed4;
            }
            QPushButton#btn_ojo {
                border: none;
                background: transparent;
                font-size: 16px;
                padding: 0 8px;
                color: #73726c;
            }
            QPushButton#btn_ojo:hover { color: #3d3d3a; }
            QLabel#error_msg {
                color: #C0392B;
                font-size: 12px;
                padding: 8px 12px;
                background-color: #fdf0ee;
                border-radius: 6px;
                border: 1px solid #f5c6c0;
            }
            QLabel#version {
                font-size: 11px;
                color: #a09e96;
            }
        """)

    # ══════════════════════════════════════════════════════════════
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ══════════════════════════════════════════════════════════════

    def _construir_ui(self) -> None:
        """
        Crea todos los widgets y los organiza con layouts.

        LAYOUTS en Qt:
          QVBoxLayout → apila widgets verticalmente (de arriba a abajo)
          QHBoxLayout → apila widgets horizontalmente (lado a lado)
          Los layouts se anidan: un HBox dentro de un VBox, etc.
        """
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 30)
        layout_principal.setSpacing(8)

        # ── Encabezado ───────────────────────────────────────────
        lbl_titulo = QLabel("Sistema de Talleres")
        lbl_titulo.setObjectName("titulo")         # permite aplicar CSS por ID
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_subtitulo = QLabel("Universidad Nacional de Barranca")
        lbl_subtitulo.setObjectName("subtitulo")
        lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Separador visual
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #e8e6e0; margin: 12px 0;")

        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        layout_principal.addSpacing(10)
        layout_principal.addWidget(separador)

        # ── Campo: Usuario ───────────────────────────────────────
        lbl_user = QLabel("Usuario")
        lbl_user.setObjectName("etiqueta")
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ingresa tu usuario")
        self.input_usuario.setMaxLength(50)

        layout_principal.addWidget(lbl_user)
        layout_principal.addWidget(self.input_usuario)

        # ── Campo: Contraseña (con botón ojo) ────────────────────
        lbl_pass = QLabel("Contraseña")
        lbl_pass.setObjectName("etiqueta")

        # Contenedor horizontal: [input] [👁 botón]
        contenedor_pass = QHBoxLayout()
        contenedor_pass.setSpacing(0)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Ingresa tu contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)  # oculta el texto
        self.input_password.setMaxLength(100)

        # Botón ojo — muestra/oculta la contraseña
        self.btn_ojo = QPushButton("👁")
        self.btn_ojo.setObjectName("btn_ojo")
        self.btn_ojo.setFixedSize(40, 42)
        self.btn_ojo.setCheckable(True)    # se queda presionado hasta volver a clicar
        self.btn_ojo.setToolTip("Mostrar/ocultar contraseña")

        contenedor_pass.addWidget(self.input_password)
        contenedor_pass.addWidget(self.btn_ojo)

        layout_principal.addWidget(lbl_pass)
        layout_principal.addLayout(contenedor_pass)

        # ── Mensaje de error (oculto por defecto) ────────────────
        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("error_msg")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setVisible(False)   # empieza oculto

        layout_principal.addSpacing(4)
        layout_principal.addWidget(self.lbl_error)

        # ── Botón Ingresar ───────────────────────────────────────
        self.btn_ingresar = QPushButton("Ingresar")
        self.btn_ingresar.setObjectName("btn_ingresar")
        self.btn_ingresar.setMinimumHeight(46)
        self.btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)

        layout_principal.addWidget(self.btn_ingresar)
        layout_principal.addStretch()   # empuja el contenido hacia arriba

        # ── Versión al pie ───────────────────────────────────────
        lbl_version = QLabel("v1.0.0  ·  UNAB Talleres")
        lbl_version.setObjectName("version")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(lbl_version)

    # ══════════════════════════════════════════════════════════════
    # CONEXIÓN DE SEÑALES (eventos)
    # ══════════════════════════════════════════════════════════════

    def _conectar_señales(self) -> None:

        self.btn_ingresar.clicked.connect(self._intentar_login)

        # Presionar Enter en cualquier campo = hacer login
        self.input_usuario.returnPressed.connect(self._intentar_login)
        self.input_password.returnPressed.connect(self._intentar_login)

        # Botón ojo: alternar visibilidad de la contraseña
        self.btn_ojo.toggled.connect(self._toggle_password_visible)

        # Limpiar el error al escribir de nuevo
        self.input_usuario.textChanged.connect(self._limpiar_error)
        self.input_password.textChanged.connect(self._limpiar_error)

    # ══════════════════════════════════════════════════════════════
    # LÓGICA DE LA VENTANA
    # ══════════════════════════════════════════════════════════════

    def _intentar_login(self) -> None:
        
        username = self.input_usuario.text().strip()
        password = self.input_password.text()

        # Deshabilitar botón mientras procesa
        self.btn_ingresar.setEnabled(False)
        self.btn_ingresar.setText("Verificando...")
        QApplication.processEvents()   # fuerza que Qt dibuje el cambio antes de continuar

        # Llamar al servicio (aquí ocurre todo: BD, bcrypt, bloqueos)
        resultado = AuthService.login(username, password)

        if resultado.ok:
            # ✅ Login exitoso: guardar sesión y cerrar esta ventana
            self.sesion_activa = resultado.sesion
            self.accept()           # QDialog.accept() = cerrar con código "aceptado"
        else:
            # ❌ Error: mostrar mensaje y rehabilitar botón
            self._mostrar_error(resultado.mensaje)
            self.btn_ingresar.setEnabled(True)
            self.btn_ingresar.setText("Ingresar")
            self.input_password.clear()
            self.input_password.setFocus()

    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra el label de error con animación de borde rojo."""
        self.lbl_error.setText(mensaje)
        self.lbl_error.setVisible(True)
        # Bordes rojos en los campos para retroalimentación visual
        self.input_usuario.setProperty("error", "true")
        self.input_password.setProperty("error", "true")
        # Forzar recarga de estilos (necesario cuando cambia una propiedad CSS)
        self.input_usuario.style().unpolish(self.input_usuario)
        self.input_usuario.style().polish(self.input_usuario)
        self.input_password.style().unpolish(self.input_password)
        self.input_password.style().polish(self.input_password)

    def _limpiar_error(self) -> None:
        """Oculta el error cuando el usuario empieza a escribir de nuevo."""
        if self.lbl_error.isVisible():
            self.lbl_error.setVisible(False)
            self.input_usuario.setProperty("error", "false")
            self.input_password.setProperty("error", "false")
            self.input_usuario.style().unpolish(self.input_usuario)
            self.input_usuario.style().polish(self.input_usuario)
            self.input_password.style().unpolish(self.input_password)
            self.input_password.style().polish(self.input_password)

    def _toggle_password_visible(self, visible: bool) -> None:
        """Alterna entre mostrar y ocultar el texto de la contraseña."""
        modo = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self.input_password.setEchoMode(modo)
        self.btn_ojo.setText("🙈" if visible else "👁")
