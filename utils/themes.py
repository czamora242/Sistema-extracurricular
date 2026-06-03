import os
from dotenv import load_dotenv, set_key

load_dotenv()

# ══════════════════════════════════════════════════════════════════
# PALETAS DE COLORES
# Cada clave se usa en el QSS con {COLOR_BG}, {COLOR_TEXT}, etc.
# ══════════════════════════════════════════════════════════════════

LIGHT = {
    "COLOR_BG":           "#f8f7f4",   # fondo general de la app
    "COLOR_SURFACE":      "#ffffff",   # fondo de inputs, cards, tablas
    "COLOR_SURFACE2":     "#f0eee8",   # superficies secundarias (barra menú, etc.)
    "COLOR_TEXT":         "#1a1a18",   # texto principal
    "COLOR_TEXT_MUTED":   "#73726c",   # texto secundario (placeholders, subtítulos)
    "COLOR_TEXT_HINT":    "#a09e96",   # texto muy tenue (versión, hints)
    "COLOR_BORDER":       "#d4d3cc",   # bordes estándar
    "COLOR_BORDER_LIGHT": "#e8e6e0",   # bordes tenues (separadores)
    "COLOR_PRIMARY":      "#534AB7",   # color de acento principal (botones, activo)
    "COLOR_PRIMARY_HOVER":"#4339A0",   # botón hover
    "COLOR_PRIMARY_PRESS":"#362E87",   # botón pressed
    "COLOR_PRIMARY_DIS":  "#a09ed4",   # botón disabled
    "COLOR_SIDEBAR_BG":   "#1e1d2e",   # fondo del sidebar (igual en ambos temas)
    "COLOR_SIDEBAR_ACTIVE":"#534AB7",  # ítem activo en sidebar
    "COLOR_SIDEBAR_HOVER":"#2d2b45",   # ítem hover en sidebar
    "COLOR_SIDEBAR_TEXT": "#c2c0d4",   # texto en sidebar
    "COLOR_SIDEBAR_MUTED":"#9b99c4",   # texto tenue en sidebar (rol)
    "COLOR_SIDEBAR_LOGOUT":"#ff8a80",  # botón logout en sidebar
    "COLOR_ERROR_BG":     "#fdf0ee",   # fondo de mensaje de error
    "COLOR_ERROR_BORDER": "#f5c6c0",   # borde de mensaje de error
    "COLOR_ERROR_TEXT":   "#C0392B",   # texto de mensaje de error
    "COLOR_ERROR_INPUT":  "#C0392B",   # borde de input en error
    "COLOR_SUCCESS":      "#1D9E75",   # mensajes de éxito
    "COLOR_STATUS_BG":    "#f0eee8",   # barra de estado inferior
    "TEMA_ICONO":         "☀️",         # icono del botón toggle
    "TEMA_NOMBRE":        "claro",
}

DARK = {
    "COLOR_BG":           "#1a1a1f",
    "COLOR_SURFACE":      "#242430",
    "COLOR_SURFACE2":     "#13131a",
    "COLOR_TEXT":         "#e8e6e0",
    "COLOR_TEXT_MUTED":   "#6e6d67",
    "COLOR_TEXT_HINT":    "#4a4a52",
    "COLOR_BORDER":       "#3a3a42",
    "COLOR_BORDER_LIGHT": "#2d2d35",
    "COLOR_PRIMARY":      "#6554C0",   # un poco más claro en oscuro para contraste
    "COLOR_PRIMARY_HOVER":"#7668CC",
    "COLOR_PRIMARY_PRESS":"#4e41a8",
    "COLOR_PRIMARY_DIS":  "#3d3460",
    "COLOR_SIDEBAR_BG":   "#13131a",
    "COLOR_SIDEBAR_ACTIVE":"#6554C0",
    "COLOR_SIDEBAR_HOVER":"#1e1d2e",
    "COLOR_SIDEBAR_TEXT": "#c2c0d4",
    "COLOR_SIDEBAR_MUTED":"#7a78a0",
    "COLOR_SIDEBAR_LOGOUT":"#ff6b6b",
    "COLOR_ERROR_BG":     "#2d1a18",
    "COLOR_ERROR_BORDER": "#6b2f2a",
    "COLOR_ERROR_TEXT":   "#ff8a80",
    "COLOR_ERROR_INPUT":  "#ff6b6b",
    "COLOR_SUCCESS":      "#2ecc71",
    "COLOR_STATUS_BG":    "#13131a",
    "TEMA_ICONO":         "🌙",
    "TEMA_NOMBRE":        "oscuro",
}


# ══════════════════════════════════════════════════════════════════
# HOJA DE ESTILOS QSS (Qt Style Sheet)
# ══════════════════════════════════════════════════════════════════

def get_stylesheet(paleta: dict) -> str:
    """
    Genera el QSS completo interpolando los colores de la paleta.

    QSS es el sistema de estilos de Qt — similar a CSS pero para widgets.
    Este QSS cubre TODOS los widgets del sistema (login, main, diálogos).
    Al llamar app.setStyleSheet(qss), se aplica a toda la aplicación.
    """
    return """
    /* ── GLOBAL ───────────────────────────────────────────────── */
    QWidget, QDialog, QMainWindow {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }}

    /* ── INPUTS ───────────────────────────────────────────────── */
    QLineEdit {{
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 9px 13px;
        font-size: 13px;
        selection-background-color: {COLOR_PRIMARY};
    }}
    QLineEdit:focus {{
        border: 1.5px solid {COLOR_PRIMARY};
    }}
    QLineEdit:disabled {{
        background-color: {COLOR_SURFACE2};
        color: {COLOR_TEXT_MUTED};
    }}
    QLineEdit[error="true"] {{
        border: 1.5px solid {COLOR_ERROR_INPUT};
    }}
    QLineEdit::placeholder {{
        color: {COLOR_TEXT_MUTED};
    }}

    /* ── BOTONES PRIMARIOS ────────────────────────────────────── */
    QPushButton#btn_ingresar,
    QPushButton#btn_guardar {{
        background-color: {COLOR_PRIMARY};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 11px 16px;
        font-size: 14px;
        font-weight: 500;
    }}
    QPushButton#btn_ingresar:hover,
    QPushButton#btn_guardar:hover {{
        background-color: {COLOR_PRIMARY_HOVER};
    }}
    QPushButton#btn_ingresar:pressed,
    QPushButton#btn_guardar:pressed {{
        background-color: {COLOR_PRIMARY_PRESS};
    }}
    QPushButton#btn_ingresar:disabled,
    QPushButton#btn_guardar:disabled {{
        background-color: {COLOR_PRIMARY_DIS};
    }}

    /* ── BOTONES SECUNDARIOS ──────────────────────────────────── */
    QPushButton#btn_cancelar,
    QPushButton#btn_secundario {{
        background-color: transparent;
        color: {COLOR_TEXT_MUTED};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 13px;
    }}
    QPushButton#btn_cancelar:hover {{
        background-color: {COLOR_SURFACE2};
        color: {COLOR_TEXT};
    }}

    /* ── BOTÓN OJO (contraseña) ───────────────────────────────── */
    QPushButton#btn_ojo {{
        border: none;
        background: transparent;
        font-size: 16px;
        padding: 0 8px;
        color: {COLOR_TEXT_MUTED};
        border-radius: 0 8px 8px 0;
    }}
    QPushButton#btn_ojo:hover {{ color: {COLOR_TEXT}; }}

    /* ── LABEL TÍTULO ─────────────────────────────────────────── */
    QLabel#lbl_titulo {{
        font-size: 22px;
        font-weight: 500;
        color: {COLOR_TEXT};
    }}
    QLabel#lbl_subtitulo {{
        font-size: 13px;
        color: {COLOR_TEXT_MUTED};
    }}
    QLabel#lbl_etiqueta {{
        font-size: 13px;
        font-weight: 500;
        color: {COLOR_TEXT};
        margin-top: 4px;
    }}
    QLabel#lbl_version {{
        font-size: 11px;
        color: {COLOR_TEXT_HINT};
    }}

    /* ── LABEL ERROR ──────────────────────────────────────────── */
    QLabel#lbl_error {{
        background-color: {COLOR_ERROR_BG};
        color: {COLOR_ERROR_TEXT};
        border: 1px solid {COLOR_ERROR_BORDER};
        border-radius: 7px;
        padding: 8px 12px;
        font-size: 12px;
    }}

    /* ── SIDEBAR ──────────────────────────────────────────────── */
    QWidget#sidebar {{
        background-color: {COLOR_SIDEBAR_BG};
        min-width: 220px;
        max-width: 220px;
    }}
    QLabel#sidebar_titulo {{
        color: #ffffff;
        font-size: 13px;
        font-weight: 500;
        padding: 0 14px;
    }}
    QLabel#sidebar_rol {{
        color: {COLOR_SIDEBAR_MUTED};
        font-size: 10px;
        padding: 0 14px;
        letter-spacing: 0.5px;
    }}
    QPushButton#btn_modulo {{
        text-align: left;
        padding: 11px 18px;
        border: none;
        background: transparent;
        color: {COLOR_SIDEBAR_TEXT};
        font-size: 13px;
        border-radius: 0;
    }}
    QPushButton#btn_modulo:hover {{
        background-color: {COLOR_SIDEBAR_HOVER};
        color: #ffffff;
    }}
    QPushButton#btn_modulo[activo="true"] {{
        background-color: {COLOR_SIDEBAR_ACTIVE};
        color: #ffffff;
        font-weight: 500;
    }}
    QPushButton#btn_logout {{
        text-align: left;
        padding: 10px 18px;
        border: none;
        background: transparent;
        color: {COLOR_SIDEBAR_LOGOUT};
        font-size: 13px;
    }}
    QPushButton#btn_logout:hover {{
        background-color: {COLOR_SIDEBAR_HOVER};
    }}

    /* ── BARRA DE MENÚ ────────────────────────────────────────── */
    QMenuBar {{
        background-color: {COLOR_SURFACE2};
        color: {COLOR_TEXT};
        border-bottom: 0.5px solid {COLOR_BORDER_LIGHT};
        padding: 2px 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {COLOR_SURFACE};
        border-radius: 4px;
    }}
    QMenu {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 7px 20px 7px 12px;
        border-radius: 5px;
        color: {COLOR_TEXT};
    }}
    QMenu::item:selected {{
        background-color: {COLOR_PRIMARY};
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background: {COLOR_BORDER_LIGHT};
        margin: 4px 8px;
    }}

    /* ── BARRA DE ESTADO ──────────────────────────────────────── */
    QStatusBar {{
        background-color: {COLOR_STATUS_BG};
        color: {COLOR_TEXT_MUTED};
        border-top: 0.5px solid {COLOR_BORDER_LIGHT};
        font-size: 11px;
        padding: 0 4px;
    }}

    /* ── TABLAS (QTableWidget) ────────────────────────────────── */
    QTableWidget {{
        background-color: {COLOR_SURFACE};
        gridline-color: {COLOR_BORDER_LIGHT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        selection-background-color: {COLOR_PRIMARY};
        selection-color: #ffffff;
        alternate-background-color: {COLOR_SURFACE2};
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        color: {COLOR_TEXT};
    }}
    QHeaderView::section {{
        background-color: {COLOR_SURFACE2};
        color: {COLOR_TEXT_MUTED};
        border: none;
        border-bottom: 1px solid {COLOR_BORDER};
        padding: 8px 10px;
        font-weight: 500;
        font-size: 12px;
    }}

    /* ── COMBOS Y SPINBOX ─────────────────────────────────────── */
    QComboBox, QSpinBox, QDateEdit {{
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
    }}
    QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
        border: 1.5px solid {COLOR_PRIMARY};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        selection-background-color: {COLOR_PRIMARY};
        selection-color: #ffffff;
        border-radius: 6px;
    }}

    /* ── SCROLLBAR ────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {COLOR_BG};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ── TOOLTIPS ─────────────────────────────────────────────── */
    QToolTip {{
        background-color: {COLOR_TEXT};
        color: {COLOR_BG};
        border: none;
        border-radius: 5px;
        padding: 5px 8px;
        font-size: 11px;
    }}

    /* ── DIÁLOGOS DE MENSAJE ──────────────────────────────────── */
    QMessageBox {{
        background-color: {COLOR_SURFACE};
    }}
    QMessageBox QLabel {{
        color: {COLOR_TEXT};
        font-size: 13px;
    }}

    /* ── ÁREA CENTRAL (contenido) ─────────────────────────────── */
    QWidget#area_central {{
        background-color: {COLOR_BG};
    }}
    QLabel#bienvenida_titulo {{
        font-size: 24px;
        font-weight: 500;
        color: {COLOR_TEXT};
    }}
    QLabel#bienvenida_sub {{
        font-size: 14px;
        color: {COLOR_TEXT_MUTED};
    }}
    """.format(**paleta)


# ══════════════════════════════════════════════════════════════════
# GESTOR DE TEMAS
# ══════════════════════════════════════════════════════════════════

class ThemeManager:
    """
    Clase de utilidad para gestionar el tema de la app.
    Todos los métodos son @staticmethod — no necesitas instanciar.

    Estado actual del tema se guarda en la variable de clase _tema_actual.
    """
    _tema_actual: str = "claro"   # valor por defecto
    _env_file: str    = ".env"

    @staticmethod
    def aplicar(app, nombre_tema: str) -> None:
        """
        Aplica un tema a toda la aplicación PySide6.

        PARÁMETROS:
          app:         la instancia de QApplication (QApplication.instance())
          nombre_tema: "claro" o "oscuro"

        EFECTO INMEDIATO:
          app.setStyleSheet(qss) → todos los widgets existentes se repintan
          sin necesidad de reiniciar la aplicación.

        USO:
            from PySide6.QtWidgets import QApplication
            from utils.themes import ThemeManager
            ThemeManager.aplicar(QApplication.instance(), "oscuro")
        """
        paleta = DARK if nombre_tema == "oscuro" else LIGHT
        app.setStyleSheet(get_stylesheet(paleta))
        ThemeManager._tema_actual = nombre_tema

        # Guardar preferencia en .env
        try:
            set_key(ThemeManager._env_file, "APP_TEMA", nombre_tema)
        except Exception:
            pass   # si no se puede escribir .env, no es crítico

    @staticmethod
    def toggle(app) -> str:
        """
        Alterna entre claro y oscuro.
        Retorna el nombre del tema aplicado ("claro" o "oscuro").

        USO en el botón de la MainWindow:
            nuevo_tema = ThemeManager.toggle(QApplication.instance())
            self.btn_tema.setText("🌙" if nuevo_tema == "claro" else "☀️")
        """
        nuevo = "oscuro" if ThemeManager._tema_actual == "claro" else "claro"
        ThemeManager.aplicar(app, nuevo)
        return nuevo

    @staticmethod
    def cargar_preferencia(app) -> None:
        """
        Lee la preferencia guardada en .env y aplica el tema.
        Llamar en main.py antes de mostrar cualquier ventana.

        USO en main.py:
            ThemeManager.cargar_preferencia(app)
        """
        tema = os.getenv("APP_TEMA", "claro")
        ThemeManager.aplicar(app, tema)

    @staticmethod
    def tema_actual() -> str:
        """Retorna el nombre del tema actualmente aplicado."""
        return ThemeManager._tema_actual

    @staticmethod
    def icono_boton() -> str:
        """Retorna el icono correcto para el botón de toggle."""
        paleta = DARK if ThemeManager._tema_actual == "oscuro" else LIGHT
        return paleta["TEMA_ICONO"]
