"""
ui/bienes/formulario_bien_dialog.py   ──   Formulario de Bienes
═══════════════════════════════════════════════════════════════
"""

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDoubleSpinBox, QTextEdit,
    QMessageBox, QDateEdit
)

from services.bienes_service import BienesService
from services.auth_service import SesionUsuario


class FormularioBienDialog(QDialog):
    """Formulario compacto de bienes patrimoniales."""

    def __init__(self, sesion: SesionUsuario, bien_id: int = None, parent=None):
        super().__init__(parent)
        self.sesion = sesion
        self.bien_id = bien_id
        self.service = BienesService()
        self.datos = None

        if bien_id:
            r = self.service.obtener_por_id(bien_id)
            if r.ok:
                self.datos = r.datos

        self._configurar()
        self._ui()

        if self.datos:
            self._cargar()

    # ─────────────────────────────────────────────
    def _configurar(self):
        self.setWindowTitle("Bien Patrimonial")
        self.setFixedWidth(420)   # 👈 MÁS PEQUEÑO
        self.setFixedHeight(620)  # 👈 MÁS COMPACTO
        self.setModal(True)

    # ─────────────────────────────────────────────
    def _ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("🏛️ Bien Patrimonial")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        titulo.setFont(font)
        layout.addWidget(titulo)

        # ── Código
        layout.addWidget(QLabel("Código"))
        self.inp_codigo = QLineEdit()
        if self.bien_id:
            self.inp_codigo.setReadOnly(True)
        layout.addWidget(self.inp_codigo)

        # ── Descripción
        layout.addWidget(QLabel("Descripción"))
        self.inp_desc = QLineEdit()
        layout.addWidget(self.inp_desc)

        # ── Categoría (ANTES tipo → corregido)
        layout.addWidget(QLabel("Categoría"))
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItems(["Audio","Vestuario", "Instrumento musicales", "Implementos de danza","Iluminación"])
        layout.addWidget(self.cmb_categoria)

        # ── Valor
        layout.addWidget(QLabel("Valor (S/.)"))
        self.spn_valor = QDoubleSpinBox()
        self.spn_valor.setMaximum(999999)
        self.spn_valor.setDecimals(2)
        layout.addWidget(self.spn_valor)

        # ── Fecha
        layout.addWidget(QLabel("Fecha adquisición"))
        self.dt_fecha = QDateEdit()
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setDate(QDate.currentDate())
        layout.addWidget(self.dt_fecha)

        # ── Estado (CORREGIDO según servicio)
        layout.addWidget(QLabel("Estado"))
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems([
            "Disponible",
            "Asignado",
            "Mantenimiento",
            "DeBaja"
        ])
        layout.addWidget(self.cmb_estado)

        # ── Observaciones
        layout.addWidget(QLabel("Observaciones"))
        self.txt_obs = QTextEdit()
        self.txt_obs.setFixedHeight(50)
        layout.addWidget(self.txt_obs)

        # ── BOTONES
        btns = QHBoxLayout()

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self._guardar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btns.addWidget(btn_guardar)
        btns.addWidget(btn_cancelar)

        layout.addLayout(btns)

    # ─────────────────────────────────────────────
    def _cargar(self):
        self.inp_codigo.setText(self.datos.get("codigo_patrimonial", ""))
        self.inp_desc.setText(self.datos.get("descripcion", ""))
        self.cmb_categoria.setCurrentText(self.datos.get("categoria", "Mueble"))
        self.spn_valor.setValue(float(self.datos.get("valor_adquisicion") or 0))
        self.cmb_estado.setCurrentText(self.datos.get("estado", "Disponible"))
        self.txt_obs.setText(self.datos.get("observaciones", ""))

        fecha = self.datos.get("fecha_adquisicion")
        if fecha:
            self.dt_fecha.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))

    # ─────────────────────────────────────────────
    def _guardar(self):
        if not self.inp_codigo.text().strip():
            QMessageBox.warning(self, "Validación", "Código obligatorio")
            return

        if not self.inp_desc.text().strip():
            QMessageBox.warning(self, "Validación", "Descripción obligatoria")
            return

        if self.spn_valor.value() <= 0:
            QMessageBox.warning(self, "Validación", "Valor debe ser mayor a 0")
            return

        datos = {
            "codigo_patrimonial": self.inp_codigo.text().strip(),
            "descripcion": self.inp_desc.text().strip(),
            "categoria": self.cmb_categoria.currentText(),
            "valor_adquisicion": self.spn_valor.value(),
            "fecha_adquisicion": self.dt_fecha.date().toString("yyyy-MM-dd"),
            "estado": self.cmb_estado.currentText(),
            "observaciones": self.txt_obs.toPlainText().strip()
        }

        usuario_id = self.sesion.usuario_id

        if self.bien_id:
            r = self.service.editar(self.bien_id, datos, usuario_id)
        else:
            r = self.service.registrar(datos, usuario_id)

        if r.ok:
            QMessageBox.information(self, "Éxito", r.mensaje)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", r.mensaje)