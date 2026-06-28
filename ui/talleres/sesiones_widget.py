"""
ui/talleres/sesiones_widget.py   ──   Sprint 3 / HU-07
═══════════════════════════════════════════════════════

Diálogo de gestión de sesiones de un taller.

LAYOUT:
  ┌──────────────────────────────────────────────────────┐
  │  Sesiones — Danzas Folklóricas          [✕ Cerrar]  │
  │──────────────────────────────────────────────────────│
  │  Ciclo: 2025-I  |  Docente: María López              │
  │──────────────────────────────────────────────────────│
  │  #  │ Fecha     │ Hora     │ Estado      │ Asistencias│
  │──────────────────────────────────────────────────────│
  │  1  │ 01/06/25  │ 14:00-16 │ Programada  │ 0/32      │
  │  2  │ 03/06/25  │ 14:00-16 │ Realizada   │ 28/32     │
  │──────────────────────────────────────────────────────│
  │                    [Cambiar estado] [Observaciones]   │
  └──────────────────────────────────────────────────────┘

NOMBRES DE PROPIEDADES (objectName):
  tbl_sesiones        QTableWidget  tabla de sesiones
  btn_cambiar_estado  QPushButton   cambiar estado de sesión
  btn_observaciones   QPushButton   agregar observaciones
  lbl_titulo          QLabel        nombre del taller
  lbl_info            QLabel        ciclo y docente
  btn_cerrar          QPushButton   cierra el diálogo
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QMenu,
    QMessageBox, QInputDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui  import QColor, QFont

from services.taller_service import TallerService


class SesionesDialog(QDialog):
    """
    USO:
        dlg = SesionesDialog(taller_id=5, sesion=sesion_usuario, parent=self)
        dlg.exec()
    """

    COLUMNAS = [
        (0, "#",             45),
        (1, "Fecha",        100),
        (2, "Hora",          90),
        (3, "Estado",       120),
        (4, "Asistencias",   90),
        (5, "Observaciones", 200),
    ]

    ESTADOS_SESION = ("Programada", "Realizada", "Cancelada")

    def __init__(self, taller_id: int, sesion, parent=None):
        super().__init__(parent)
        self.taller_id  = taller_id
        self.sesion     = sesion
        self._datos     = []

        self.setModal(True)
        self.setMinimumSize(840, 480)
        self.setWindowTitle("Sesiones del taller")
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._construir_ui()
        self._cargar_datos()

    # ──────────────────────────────────────────────────────────────
    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(22, 18, 22, 18)
        raiz.setSpacing(0)

        # Título
        self.lbl_titulo = QLabel("Sesiones del taller")
        self.lbl_titulo.setObjectName("lbl_titulo_dialogo")
        f = QFont(); f.setPointSize(16); f.setWeight(QFont.Weight.Medium)
        self.lbl_titulo.setFont(f)
        raiz.addWidget(self.lbl_titulo)
        raiz.addSpacing(4)

        self.lbl_info = QLabel("")
        self.lbl_info.setObjectName("lbl_info_sesiones")
        raiz.addWidget(self.lbl_info)
        raiz.addSpacing(14)

        # Tabla
        self.tbl_sesiones = self._construir_tabla()
        self.tbl_sesiones.setObjectName("tbl_sesiones")
        raiz.addWidget(self.tbl_sesiones, 1)

        raiz.addSpacing(12)

        # Botones
        pie = QHBoxLayout()
        pie.addStretch()

        self.btn_cambiar_estado = QPushButton("Cambiar estado")
        self.btn_cambiar_estado.setObjectName("btn_cambiar_estado")
        self.btn_cambiar_estado.setFixedHeight(34)
        self.btn_cambiar_estado.setEnabled(False)
        self.btn_cambiar_estado.clicked.connect(self._cambiar_estado)
        pie.addWidget(self.btn_cambiar_estado)

        pie.addSpacing(6)

        self.btn_observaciones = QPushButton("Observaciones")
        self.btn_observaciones.setObjectName("btn_observaciones")
        self.btn_observaciones.setFixedHeight(34)
        self.btn_observaciones.setEnabled(False)
        self.btn_observaciones.clicked.connect(self._agregar_observaciones)
        pie.addWidget(self.btn_observaciones)

        pie.addSpacing(8)

        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setObjectName("btn_cerrar")
        self.btn_cerrar.setFixedSize(100, 34)
        self.btn_cerrar.clicked.connect(self.accept)
        pie.addWidget(self.btn_cerrar)

        raiz.addLayout(pie)

        # Habilitar botones al seleccionar
        self.tbl_sesiones.itemSelectionChanged.connect(
            self._on_seleccion_cambio)

    def _construir_tabla(self) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(len(self.COLUMNAS))
        tbl.setHorizontalHeaderLabels([c[1] for c in self.COLUMNAS])
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setShowGrid(False)
        tbl.setSortingEnabled(False)
        tbl.verticalHeader().setVisible(False)
        tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tbl.customContextMenuRequested.connect(self._menu_contextual)

        for idx, _, ancho in self.COLUMNAS:
            tbl.setColumnWidth(idx, ancho)
        tbl.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setDefaultSectionSize(36)
        return tbl

    # ──────────────────────────────────────────────────────────────
    def _cargar_datos(self):
        """Carga datos del taller y sus sesiones."""
        t_datos = TallerService.obtener_por_id(self.taller_id)
        if not t_datos:
            self.lbl_titulo.setText("Taller no encontrado")
            return

        self.lbl_titulo.setText(f"Sesiones — {t_datos['nombre']}")
        self.lbl_info.setText(
            f"Ciclo: <b>{t_datos['ciclo']}</b>  |  "
            f"Docente: <b>{t_datos['docente']}</b>  |  "
            f"Total sesiones: {t_datos['total_sesiones']}"
        )

        self._datos = TallerService.listar_sesiones(self.taller_id)
        self._poblar_tabla()

    def _poblar_tabla(self):
        self.tbl_sesiones.setRowCount(len(self._datos))

        COLORES_ESTADO = {
            "Programada": ("#73726c", "#f0eee8"),
            "Realizada":  ("#1D9E75", "#E8F8F2"),
            "Cancelada":  ("#C0392B", "#fdf0ee"),
        }

        for fila, s in enumerate(self._datos):
            valores = [
                str(s["numero"]),
                s["fecha"],
                s["hora_inicio"],
                s["estado"],
                f"{s['asistencias']}",
                s["observaciones"],
            ]

            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |
                                      Qt.AlignmentFlag.AlignLeft)

                if col in (0, 2, 3, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Colorear estado
                if col == 3:
                    fg, bg = COLORES_ESTADO.get(val, ("#333", "#fff"))
                    item.setForeground(QColor(fg))
                    item.setBackground(QColor(bg))

                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, s["id"])

                self.tbl_sesiones.setItem(fila, col, item)

    # ──────────────────────────────────────────────────────────────
    def _on_seleccion_cambio(self):
        """Habilita botones si hay fila seleccionada."""
        hay = bool(self.tbl_sesiones.selectedItems())
        self.btn_cambiar_estado.setEnabled(hay)
        self.btn_observaciones.setEnabled(hay)

    def _sesion_id_seleccionada(self) -> int | None:
        fila = self.tbl_sesiones.currentRow()
        if fila < 0:
            return None
        item = self.tbl_sesiones.item(fila, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    # ──────────────────────────────────────────────────────────────
    def _cambiar_estado(self):
        """Cambia el estado de una sesión."""
        sid = self._sesion_id_seleccionada()
        if not sid:
            return

        fila = self.tbl_sesiones.currentRow()
        estado_actual = self._datos[fila]["estado"]

        menu = QMenu(self)
        for estado in [e for e in self.ESTADOS_SESION
                       if e != estado_actual]:
            menu.addAction(f"Cambiar a {estado}",
                          lambda e=estado: self._confirmar_cambio_estado(
                              sid, e, fila))

        menu.exec(self.btn_cambiar_estado.mapToGlobal(
            self.btn_cambiar_estado.rect().bottomLeft()))

    def _confirmar_cambio_estado(self, sid: int, nuevo: str, fila: int):
        from services.sesion_service import SesionService
        res = SesionService.cambiar_estado(sid, nuevo, self.sesion.usuario_id)
        
        if not res.ok:
            QMessageBox.warning(self, "Error", res.mensaje)
            return
        
        # Si fue exitoso, actualizar la tabla
        self._datos[fila]["estado"] = nuevo
        self.tbl_sesiones.item(fila, 3).setText(nuevo)
        
        fg, bg = {
            "Programada": ("#73726c", "#f0eee8"),
            "Realizada":  ("#1D9E75", "#E8F8F2"),
            "Cancelada":  ("#C0392B", "#fdf0ee"),
        }.get(nuevo, ("#333", "#fff"))
        
        item = self.tbl_sesiones.item(fila, 3)
        item.setForeground(QColor(fg))
        item.setBackground(QColor(bg))
        
        QMessageBox.information(self, "Actualizado", res.mensaje)

    # ──────────────────────────────────────────────────────────────
    def _agregar_observaciones(self):
        """Abre un diálogo para agregar/editar observaciones."""
        fila = self.tbl_sesiones.currentRow()
        if fila < 0:
            return

        obs_actual = self._datos[fila].get("observaciones", "")

        obs_nueva, ok = QInputDialog.getMultiLineText(
            self,
            "Observaciones de la sesión",
            "Ingresa observaciones (opcional):",
            obs_actual
        )

        if ok:
            self._datos[fila]["observaciones"] = obs_nueva
            self.tbl_sesiones.item(fila, 5).setText(obs_nueva)
            QMessageBox.information(self, "Guardado",
                "Observaciones actualizadas.")

    def _menu_contextual(self, pos):
        if not self._sesion_id_seleccionada():
            return
        menu = QMenu(self)
        menu.addAction("Cambiar estado",  self._cambiar_estado)
        menu.addAction("Observaciones",   self._agregar_observaciones)
        menu.exec(self.tbl_sesiones.mapToGlobal(pos))
