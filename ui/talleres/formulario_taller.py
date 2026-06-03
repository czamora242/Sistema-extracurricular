"""
ui/talleres/formulario_taller.py   ──   Sprint 3 / HU-06, HU-07
════════════════════════════════════════════════════════════════

Diálogo de registro y edición de un taller.
Incluye la pestaña de generación automática de sesiones (HU-07).

LAYOUT (QTabWidget con 2 pestañas):

  Pestaña 1 — Datos del taller:
  ┌─────────────────────────────────────────────────────┐
  │  Código*      Nombre*                               │
  │  Ciclo*       Docente*                              │
  │  Categoría    Sede                                  │
  │  Cupo máx.*   Umbral de asistencia* (50-100%)       │
  │  Descripción                                        │
  └─────────────────────────────────────────────────────┘

  Pestaña 2 — Sesiones (solo en modo nuevo o sin asistencia):
  ┌─────────────────────────────────────────────────────┐
  │  Fecha inicio*    Fecha fin*                        │
  │  Días: [Lun] [Mar] [Mié] [Jue] [Vie] [Sáb] [Dom]  │
  │  Hora inicio*     Hora fin*                         │
  │  Vista previa: Se generarán N sesiones              │
  └─────────────────────────────────────────────────────┘

NOMBRES DE PROPIEDADES (objectName):
  inp_codigo          QLineEdit
  inp_nombre          QLineEdit
  cmb_ciclo           QComboBox
  cmb_docente         QComboBox
  inp_categoria       QLineEdit
  inp_sede            QLineEdit
  spn_cupo            QSpinBox
  spn_umbral          QSpinBox
  txt_descripcion     QTextEdit
  dte_inicio          QDateEdit
  dte_fin             QDateEdit
  chk_lun … chk_dom  QCheckBox (7 checkboxes)
  inp_hora_inicio     QLineEdit  formato HH:MM
  inp_hora_fin        QLineEdit  formato HH:MM
  lbl_preview_sesiones QLabel   "Se generarán N sesiones"
  lbl_mensaje         QLabel
  btn_guardar         QPushButton
  btn_cancelar        QPushButton
"""

from datetime import date, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QTextEdit, QCheckBox, QTabWidget,
    QWidget, QFrame, QDateEdit, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui  import QFont, QIntValidator

from services.taller_service import TallerService


class FormularioTallerDialog(QDialog):
    """
    USO nuevo:
        dlg = FormularioTallerDialog(sesion=sesion)
        if dlg.exec(): ...

    USO edición:
        dlg = FormularioTallerDialog(sesion=sesion, taller_id=5)
        if dlg.exec(): ...
    """

    DIAS = ["Lunes", "Martes", "Miércoles",
            "Jueves", "Viernes", "Sábado", "Domingo"]

    def __init__(self, sesion, taller_id: int = None, parent=None):
        super().__init__(parent)
        self.sesion      = sesion
        self.taller_id   = taller_id
        self._es_edicion = taller_id is not None

        self.setModal(True)
        self.setMinimumSize(620, 520)
        self.setWindowTitle(
            "Editar taller" if self._es_edicion else "Nuevo taller"
        )
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._construir_ui()
        self._cargar_combos()
        if self._es_edicion:
            self._cargar_datos()

    # ──────────────────────────────────────────────────────────────
    # UI
    # ──────────────────────────────────────────────────────────────
    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(22, 18, 22, 18)
        raiz.setSpacing(0)

        # Título
        lbl = QLabel("Editar taller" if self._es_edicion else "Nuevo taller")
        lbl.setObjectName("lbl_titulo_dialogo")
        f = QFont(); f.setPointSize(16); f.setWeight(QFont.Weight.Medium)
        lbl.setFont(f)
        raiz.addWidget(lbl)
        raiz.addSpacing(14)

        # Pestañas
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_datos(),    "📋  Datos del taller")
        self.tabs.addTab(self._tab_sesiones(), "📅  Sesiones automáticas")
        raiz.addWidget(self.tabs, 1)

        raiz.addSpacing(10)

        # Mensaje
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setObjectName("lbl_mensaje")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setVisible(False)
        raiz.addWidget(self.lbl_mensaje)

        raiz.addSpacing(10)

        # Botones
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separador")
        raiz.addWidget(sep)
        raiz.addSpacing(10)

        pie = QHBoxLayout()
        pie.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setFixedSize(110, 38)
        self.btn_cancelar.clicked.connect(self.reject)
        pie.addWidget(self.btn_cancelar)

        pie.addSpacing(8)

        self.btn_guardar = QPushButton(
            "Guardar cambios" if self._es_edicion else "Crear taller"
        )
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setFixedSize(160, 38)
        self.btn_guardar.clicked.connect(self._guardar)
        pie.addWidget(self.btn_guardar)

        raiz.addLayout(pie)

    # ── Pestaña 1: datos ─────────────────────────────────────────
    def _tab_datos(self) -> QWidget:
        w   = QWidget()
        lay = QGridLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(12, 14, 12, 14)

        def lbl(texto, req=False):
            t = f"{texto} <span style='color:#C0392B'>*</span>" if req else texto
            l = QLabel(t)
            l.setObjectName("lbl_etiqueta")
            return l

        def inp(name, ph="", maxlen=100):
            i = QLineEdit()
            i.setObjectName(name)
            i.setPlaceholderText(ph)
            i.setMaxLength(maxlen)
            i.setFixedHeight(34)
            return i

        # Fila 0: Código | Nombre
        lay.addWidget(lbl("Código", True), 0, 0)
        lay.addWidget(lbl("Nombre del taller", True), 0, 1)
        self.inp_codigo = inp("inp_codigo", "TAL-2025-001", 20)
        self.inp_nombre = inp("inp_nombre", "Danzas Folklóricas")
        if self._es_edicion:
            self.inp_codigo.setReadOnly(True)
        lay.addWidget(self.inp_codigo, 1, 0)
        lay.addWidget(self.inp_nombre, 1, 1)

        # Fila 1: Ciclo | Docente
        lay.addWidget(lbl("Ciclo académico", True), 2, 0)
        lay.addWidget(lbl("Docente", True), 2, 1)
        self.cmb_ciclo = QComboBox()
        self.cmb_ciclo.setObjectName("cmb_ciclo")
        self.cmb_ciclo.setFixedHeight(34)
        self.cmb_docente = QComboBox()
        self.cmb_docente.setObjectName("cmb_docente")
        self.cmb_docente.setFixedHeight(34)
        lay.addWidget(self.cmb_ciclo,   3, 0)
        lay.addWidget(self.cmb_docente, 3, 1)

        # Fila 2: Categoría | Sede
        lay.addWidget(lbl("Categoría"), 4, 0)
        lay.addWidget(lbl("Sede"), 4, 1)
        self.inp_categoria = inp("inp_categoria", "Arte y Cultura")
        self.inp_sede      = inp("inp_sede",      "Pabellón A - Sala 203")
        lay.addWidget(self.inp_categoria, 5, 0)
        lay.addWidget(self.inp_sede,      5, 1)

        # Fila 3: Cupo | Umbral
        lay.addWidget(lbl("Cupo máximo", True), 6, 0)
        lay.addWidget(lbl("Umbral de asistencia (%) *"), 6, 1)

        self.spn_cupo = QSpinBox()
        self.spn_cupo.setObjectName("spn_cupo")
        self.spn_cupo.setRange(1, 500)
        self.spn_cupo.setValue(30)
        self.spn_cupo.setFixedHeight(34)

        self.spn_umbral = QSpinBox()
        self.spn_umbral.setObjectName("spn_umbral")
        self.spn_umbral.setRange(50, 100)
        self.spn_umbral.setValue(80)
        self.spn_umbral.setSuffix(" %")
        self.spn_umbral.setFixedHeight(34)
        self.spn_umbral.setToolTip(
            "Porcentaje mínimo de asistencia para que el estudiante sea apto.\n"
            "Entre 50% y 100%."
        )

        lay.addWidget(self.spn_cupo,   7, 0)
        lay.addWidget(self.spn_umbral, 7, 1)

        # Fila 4: Descripción (span 2 col)
        lay.addWidget(lbl("Descripción"), 8, 0, 1, 2)
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setObjectName("txt_descripcion")
        self.txt_descripcion.setPlaceholderText(
            "Descripción opcional del taller…"
        )
        self.txt_descripcion.setFixedHeight(70)
        lay.addWidget(self.txt_descripcion, 9, 0, 1, 2)

        lay.setColumnStretch(0, 1)
        lay.setColumnStretch(1, 1)
        return w

    # ── Pestaña 2: sesiones ───────────────────────────────────────
    def _tab_sesiones(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 14, 12, 14)
        lay.setSpacing(12)

        info = QLabel(
            "El sistema generará automáticamente todas las sesiones "
            "en los días y horario indicados."
        )
        info.setObjectName("lbl_subtitulo_dialogo")
        info.setWordWrap(True)
        lay.addWidget(info)

        # Fechas
        grid = QGridLayout()
        grid.setSpacing(10)

        def lbl_e(t, req=False):
            txt = f"{t} <span style='color:#C0392B'>*</span>" if req else t
            l = QLabel(txt); l.setObjectName("lbl_etiqueta")
            return l

        grid.addWidget(lbl_e("Fecha de inicio", True), 0, 0)
        grid.addWidget(lbl_e("Fecha de fin",    True), 0, 1)

        self.dte_inicio = QDateEdit()
        self.dte_inicio.setObjectName("dte_inicio")
        self.dte_inicio.setCalendarPopup(True)
        self.dte_inicio.setFixedHeight(34)
        self.dte_inicio.setDate(QDate.currentDate())
        self.dte_inicio.dateChanged.connect(self._actualizar_preview)

        self.dte_fin = QDateEdit()
        self.dte_fin.setObjectName("dte_fin")
        self.dte_fin.setCalendarPopup(True)
        self.dte_fin.setFixedHeight(34)
        self.dte_fin.setDate(QDate.currentDate().addDays(90))
        self.dte_fin.dateChanged.connect(self._actualizar_preview)

        grid.addWidget(self.dte_inicio, 1, 0)
        grid.addWidget(self.dte_fin,    1, 1)

        # Horas
        grid.addWidget(lbl_e("Hora de inicio", True), 2, 0)
        grid.addWidget(lbl_e("Hora de fin",    True), 2, 1)

        self.inp_hora_inicio = QLineEdit("08:00")
        self.inp_hora_inicio.setObjectName("inp_hora_inicio")
        self.inp_hora_inicio.setFixedHeight(34)
        self.inp_hora_inicio.setMaxLength(5)
        self.inp_hora_inicio.setPlaceholderText("HH:MM")
        self.inp_hora_inicio.textChanged.connect(self._actualizar_preview)

        self.inp_hora_fin = QLineEdit("10:00")
        self.inp_hora_fin.setObjectName("inp_hora_fin")
        self.inp_hora_fin.setFixedHeight(34)
        self.inp_hora_fin.setMaxLength(5)
        self.inp_hora_fin.setPlaceholderText("HH:MM")
        self.inp_hora_fin.textChanged.connect(self._actualizar_preview)

        grid.addWidget(self.inp_hora_inicio, 3, 0)
        grid.addWidget(self.inp_hora_fin,    3, 1)

        lay.addLayout(grid)

        # Días de la semana
        lay.addWidget(lbl_e("Días de la semana *"))
        dias_lay = QHBoxLayout()
        dias_lay.setSpacing(6)
        self.chk_dias = []
        for i, dia in enumerate(self.DIAS):
            chk = QCheckBox(dia[:3])   # Lun, Mar, Mié…
            chk.setObjectName(f"chk_{dia[:3].lower()}")
            chk.setToolTip(dia)
            chk.stateChanged.connect(self._actualizar_preview)
            # Por defecto Lun-Vie activos
            if i < 5:
                chk.setChecked(True)
            self.chk_dias.append(chk)
            dias_lay.addWidget(chk)
        dias_lay.addStretch()
        lay.addLayout(dias_lay)

        # Preview
        self.lbl_preview_sesiones = QLabel("")
        self.lbl_preview_sesiones.setObjectName("lbl_preview_sesiones")
        self.lbl_preview_sesiones.setWordWrap(True)
        lay.addWidget(self.lbl_preview_sesiones)

        lay.addStretch()
        self._actualizar_preview()
        return w

    # ──────────────────────────────────────────────────────────────
    # COMBOS
    # ──────────────────────────────────────────────────────────────
    def _cargar_combos(self):
        self.cmb_ciclo.addItem("— Selecciona ciclo —", None)
        for c in TallerService.listar_ciclos():
            self.cmb_ciclo.addItem(c["nombre"], c["id"])

        self.cmb_docente.addItem("— Selecciona docente —", None)
        for d in TallerService.listar_docentes():
            self.cmb_docente.addItem(d["nombre"], d["id"])

    # ──────────────────────────────────────────────────────────────
    # CARGA EN MODO EDICIÓN
    # ──────────────────────────────────────────────────────────────
    def _cargar_datos(self):
        datos = TallerService.obtener_por_id(self.taller_id)
        if not datos:
            self._mostrar_mensaje("Taller no encontrado.", error=True)
            return

        self.inp_codigo.setText(datos["codigo"])
        self.inp_nombre.setText(datos["nombre"])
        self.inp_categoria.setText(datos["categoria"])
        self.inp_sede.setText(datos["sede"])
        self.spn_cupo.setValue(datos["cupo_maximo"])
        self.spn_umbral.setValue(datos["umbral"])
        self.txt_descripcion.setPlainText(datos["descripcion"])

        for i in range(self.cmb_ciclo.count()):
            if self.cmb_ciclo.itemData(i) == datos["ciclo_id"]:
                self.cmb_ciclo.setCurrentIndex(i); break

        for i in range(self.cmb_docente.count()):
            if self.cmb_docente.itemData(i) == datos["docente_id"]:
                self.cmb_docente.setCurrentIndex(i); break

        # Si ya tiene sesiones con asistencia, deshabilitar pestaña de sesiones
        if datos["sesiones_realizadas"] > 0:
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabToolTip(1,
                "No se pueden regenerar sesiones con asistencia registrada.")

    # ──────────────────────────────────────────────────────────────
    # PREVIEW DE SESIONES
    # ──────────────────────────────────────────────────────────────
    def _actualizar_preview(self):
        """Calcula y muestra cuántas sesiones se generarían."""
        try:
            fi = self.dte_inicio.date().toPython()
            ff = self.dte_fin.date().toPython()
            dias = [i for i, chk in enumerate(self.chk_dias)
                    if chk.isChecked()]

            if not dias:
                self.lbl_preview_sesiones.setText(
                    "⚠️  Selecciona al menos un día.")
                return
            if fi >= ff:
                self.lbl_preview_sesiones.setText(
                    "⚠️  La fecha de inicio debe ser anterior a la de fin.")
                return

            total = 0
            cursor = fi
            while cursor <= ff:
                if cursor.weekday() in dias:
                    total += 1
                cursor += timedelta(days=1)

            dias_nombres = [self.DIAS[d][:3] for d in dias]
            self.lbl_preview_sesiones.setText(
                f"✅  Se generarán <b>{total} sesiones</b> "
                f"({', '.join(dias_nombres)}) "
                f"del {fi.strftime('%d/%m/%Y')} "
                f"al {ff.strftime('%d/%m/%Y')}."
            )
        except Exception:
            self.lbl_preview_sesiones.setText("")

    # ──────────────────────────────────────────────────────────────
    # VALIDACIÓN Y GUARDADO
    # ──────────────────────────────────────────────────────────────
    def _validar(self) -> str | None:
        if not self.inp_codigo.text().strip():
            return "El código es obligatorio."
        if not self.inp_nombre.text().strip():
            return "El nombre es obligatorio."
        if self.cmb_ciclo.currentData() is None:
            return "Selecciona el ciclo académico."
        if self.cmb_docente.currentData() is None:
            return "Selecciona el docente."
        return None

    def _guardar(self):
        error = self._validar()
        if error:
            self._mostrar_mensaje(error, error=True)
            return

        datos = {
            "codigo":             self.inp_codigo.text().strip(),
            "nombre":             self.inp_nombre.text().strip(),
            "ciclo_academico_id": self.cmb_ciclo.currentData(),
            "docente_id":         self.cmb_docente.currentData(),
            "categoria":          self.inp_categoria.text().strip(),
            "sede":               self.inp_sede.text().strip(),
            "cupo_maximo":        self.spn_cupo.value(),
            "umbral_asistencia":  self.spn_umbral.value(),
            "descripcion":        self.txt_descripcion.toPlainText().strip(),
        }

        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando…")

        if self._es_edicion:
            res = TallerService.editar(
                self.taller_id, datos, self.sesion.usuario_id)
        else:
            res = TallerService.registrar(datos, self.sesion.usuario_id)

        # Generar sesiones si es nuevo y la pestaña está activa
        if res.ok and not self._es_edicion:
            taller_id_nuevo = res.datos["id"]
            dias = [i for i, chk in enumerate(self.chk_dias)
                    if chk.isChecked()]
            if dias:
                res_ses = TallerService.generar_sesiones(
                    taller_id   = taller_id_nuevo,
                    fecha_inicio = self.dte_inicio.date().toPython(),
                    fecha_fin    = self.dte_fin.date().toPython(),
                    dias_semana  = dias,
                    hora_inicio  = self.inp_hora_inicio.text().strip(),
                    hora_fin     = self.inp_hora_fin.text().strip(),
                    usuario_id   = self.sesion.usuario_id,
                )
                if not res_ses.ok:
                    self._mostrar_mensaje(
                        f"Taller creado, pero error en sesiones: {res_ses.mensaje}",
                        error=True)
                    self.btn_guardar.setEnabled(True)
                    self.btn_guardar.setText("Crear taller")
                    return

        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText(
            "Guardar cambios" if self._es_edicion else "Crear taller")

        if res.ok:
            self._mostrar_mensaje(res.mensaje, error=False)
            QTimer.singleShot(1200, self.accept)
        else:
            self._mostrar_mensaje(res.mensaje, error=True)

    def _mostrar_mensaje(self, texto: str, error: bool = False):
        if error:
            self.lbl_mensaje.setStyleSheet(
                "background:#fdf0ee;color:#C0392B;"
                "border:1px solid #f5c6c0;border-radius:7px;padding:8px 12px;")
        else:
            self.lbl_mensaje.setStyleSheet(
                "background:#e8f8f2;color:#1D9E75;"
                "border:1px solid #a8e6cf;border-radius:7px;padding:8px 12px;")
        self.lbl_mensaje.setText(texto)
        self.lbl_mensaje.setVisible(True)
