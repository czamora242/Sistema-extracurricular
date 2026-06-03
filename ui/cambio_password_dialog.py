from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout
)
from services.auth_service import AuthService, SesionUsuario


class CambioPasswordDialog(QDialog):

    def __init__(self, sesion: SesionUsuario, parent=None):
        super().__init__(parent)
        self.sesion = sesion
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedSize(380, 380)
        self.setModal(True)   # bloquea la ventana principal mientras esté abierto
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QLabel { font-size: 13px; color: #3d3d3a; font-weight: 500; }
            QLineEdit {
                padding: 9px 12px; border: 1px solid #d4d3cc;
                border-radius: 7px; font-size: 13px;
            }
            QLineEdit:focus { border: 1.5px solid #534AB7; }
            QPushButton#btn_guardar {
                background-color: #534AB7; color: white; border: none;
                border-radius: 7px; padding: 11px; font-size: 13px;
                font-weight: 500; margin-top: 6px;
            }
            QPushButton#btn_guardar:hover { background-color: #4339A0; }
            QPushButton#btn_cancelar {
                background-color: transparent; color: #73726c;
                border: 1px solid #d4d3cc; border-radius: 7px;
                padding: 11px; font-size: 13px;
            }
        """)

        layout.addWidget(QLabel("Contraseña actual"))
        self.inp_actual = QLineEdit()
        self.inp_actual.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_actual.setPlaceholderText("Tu contraseña actual")
        layout.addWidget(self.inp_actual)

        layout.addWidget(QLabel("Nueva contraseña"))
        self.inp_nueva = QLineEdit()
        self.inp_nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_nueva.setPlaceholderText("Mínimo 8 caracteres")
        layout.addWidget(self.inp_nueva)

        layout.addWidget(QLabel("Confirmar nueva contraseña"))
        self.inp_confirmar = QLineEdit()
        self.inp_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_confirmar.setPlaceholderText("Repite la nueva contraseña")
        layout.addWidget(self.inp_confirmar)

        layout.addSpacing(6)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("btn_guardar")
        btn_guardar.clicked.connect(self._guardar)

        btns.addWidget(btn_cancelar)
        btns.addWidget(btn_guardar)
        layout.addLayout(btns)

    def _guardar(self) -> None:
        resultado = AuthService.cambiar_password(
            sesion_activa        = self.sesion,
            password_actual      = self.inp_actual.text(),
            password_nuevo       = self.inp_nueva.text(),
            password_confirmacion= self.inp_confirmar.text()
        )
        if resultado.ok:
            QMessageBox.information(self, "Éxito", resultado.mensaje)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", resultado.mensaje)
            self.inp_nueva.clear()
            self.inp_confirmar.clear()
