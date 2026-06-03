import os
import sys
from database.connection import probar_conexion, engine
from database.base       import Base
import models  # registra todas las tablas en SQLAlchemy


def inicializar_bd() -> bool:
    ok, mensaje = probar_conexion()
    if not ok:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Error de conexión",
            f"No se pudo conectar a MySQL:\n\n{mensaje}\n\n"
            f"Verifica que:\n"
            f"• MySQL esté corriendo\n"
            f"• El archivo .env tenga las credenciales correctas\n"
            f"• La base de datos '{os.getenv('DB_NAME', 'unab_talleres')}' exista"
        )
        return False
    # Crea las tablas que no existan (no toca las que ya existen)
    Base.metadata.create_all(engine)
    return True


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore    import Qt

    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Talleres UNAB")
    app.setApplicationVersion("1.0.0")

    # Verificar BD antes de mostrar cualquier ventana
    if not inicializar_bd():
        sys.exit(1)

    # Forzar tema claro al iniciar la app
    from utils.themes import ThemeManager
    ThemeManager.aplicar(app, "claro")

    # BUCLE DE SESIONES:
    # Permite cerrar sesión y volver al login sin reiniciar la app.
    while True:
        from ui.login_window import LoginWindow
        login = LoginWindow()
        resultado = login.exec()   # exec() bloquea hasta que el dialog se cierre

        if resultado != LoginWindow.DialogCode.Accepted:
            # El usuario cerró la ventana sin loguearse → salir
            break

        # Login exitoso → abrir ventana principal
        from ui.main_window import MainWindow
        ventana_principal = MainWindow(sesion=login.sesion_activa)
        ventana_principal.show()
        app.exec()   # bloquea hasta que MainWindow se cierre
        # Cuando MainWindow se cierra → el while vuelve a mostrar el login

    sys.exit(0)


if __name__ == "__main__":
    main()
