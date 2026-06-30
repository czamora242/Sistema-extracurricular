"""
ui/usuarios/dialog_reset_password_admin.py

Permite que un administrador restablezca
la contraseña de cualquier usuario.
"""

from PySide6.QtWidgets import (QDialog,QVBoxLayout,
    QHBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox)
from services.auth_service import (AuthService,SesionUsuario)


class DialogResetPasswordAdmin(QDialog):
    def __init__(self,usuario_id: int,sesion: SesionUsuario,parent=None):
        super().__init__(parent)

        self.usuario_id = usuario_id
        self.sesion = sesion

        self._configurar()
        self._construir_ui()

    # ==========================================================
    # CONFIGURACIÓN
    # ==========================================================

    def _configurar(self):

        self.setWindowTitle("Restablecer contraseña")
        self.setFixedWidth(420)
        self.setModal(True)

        self.setStyleSheet("""
            QLabel#titulo{
                font-size:15px;
                font-weight:bold;
                color:#222;
            }

            QLabel#subtitulo{
                color:#777;
                font-size:10px;
            }

            QLabel{
                font-size:10px;
            }

            QLineEdit{

                background:white;
                border:1px solid #d8d8d8;
                border-radius:4px;
                padding:6px;
                min-height:30px;

            }

            QLineEdit:focus{
                border:2px solid #2563eb;
            }
            QPushButton{
                border:none;
                border-radius:4px;
                padding:8px 14px;
                font-weight:bold;
            }
            QPushButton:hover{
                background:#1d4ed8;
            }
            QPushButton#btnCancelar{
                background:#6b7280;
            }
            QPushButton#btnCancelar:hover{
                background:#4b5563;
            }
        """)

    # ==========================================================
    # INTERFAZ
    # ==========================================================

    def _construir_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(20,20,20,20)
        layout.setSpacing(10)

        titulo = QLabel("Restablecer contraseña")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        subtitulo = QLabel("Ingrese la nueva contraseña del usuario.")
        subtitulo.setObjectName("subtitulo")
        layout.addWidget(subtitulo)

        layout.addSpacing(10)

        layout.addWidget(QLabel("Nueva contraseña"))
        self.inp_password = QLineEdit()
        self.inp_password.setEchoMode(QLineEdit.Password)
        self.inp_password.setPlaceholderText("Mínimo 8 caracteres")
        layout.addWidget(self.inp_password)

        layout.addWidget(QLabel("Confirmar contraseña"))
        self.inp_confirmar = QLineEdit()
        self.inp_confirmar.setEchoMode(QLineEdit.Password)
        self.inp_confirmar.setPlaceholderText("Repita la contraseña")
        layout.addWidget(self.inp_confirmar)

        layout.addSpacing(15)

        botones = QHBoxLayout()
        botones.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self._guardar)
        botones.addWidget(self.btn_guardar)

        layout.addLayout(botones)

    # ==========================================================
    # VALIDAR
    # ==========================================================

    def _validar(self):

        password = self.inp_password.text()
        confirmar = self.inp_confirmar.text()
        if not password:
            return False, "Debe ingresar la contraseña."
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."
        if password != confirmar:
            return False, "Las contraseñas no coinciden."

        return True, ""

    # ==========================================================
    # GUARDAR
    # ==========================================================

    def _guardar(self):
        valido, mensaje = self._validar()
        if not valido:
            QMessageBox.warning(self,"Validación",mensaje)
            return

        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando...")
        try:

            resultado = AuthService.restablecer_password_admin(
                sesion_activa=self.sesion,
                usuario_id=self.usuario_id,
                password_nuevo=self.inp_password.text(),
                password_confirmacion=self.inp_confirmar.text()
            )

            if resultado.ok:
                QMessageBox.information(self,"Contraseña actualizada",resultado.mensaje)
                self.accept()
            else:
                QMessageBox.warning(self,"Error",resultado.mensaje)

        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

        finally:
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText("Guardar")