"""
diagnostico.py
══════════════
Ejecuta este archivo PRIMERO para saber exactamente qué falla.
No necesita base de datos ni nada instalado para correr.

CÓMO USARLO:
    python diagnostico.py

Te dirá exactamente qué está mal y cómo solucionarlo.
"""

import sys
import os

print("=" * 60)
print("  DIAGNÓSTICO — Sistema de Talleres UNAB")
print("=" * 60)

errores   = []
warnings  = []
ok_lista  = []

# ── 1. Versión de Python ─────────────────────────────────────────
version = sys.version_info
if version.major < 3 or (version.major == 3 and version.minor < 10):
    errores.append(
        f"Python {version.major}.{version.minor} detectado.\n"
        f"   Se necesita Python 3.10 o superior.\n"
        f"   Descarga: https://www.python.org/downloads/"
    )
else:
    ok_lista.append(f"Python {version.major}.{version.minor}.{version.micro}")

# ── 2. Librerías instaladas ──────────────────────────────────────
librerias = {
    "PySide6":      "pip install PySide6",
    "sqlalchemy":   "pip install sqlalchemy",
    "pymysql":      "pip install pymysql",
    "dotenv":       "pip install python-dotenv",
    "bcrypt":       "pip install bcrypt",
    "openpyxl":     "pip install openpyxl",
    "alembic":      "pip install alembic",
}

for lib, cmd_install in librerias.items():
    try:
        __import__(lib if lib != "dotenv" else "dotenv")
        ok_lista.append(f"Librería: {lib}")
    except ImportError:
        errores.append(
            f"Falta la librería: '{lib}'\n"
            f"   Solución: {cmd_install}"
        )

# ── 3. Archivo .env ──────────────────────────────────────────────
if os.path.exists(".env"):
    ok_lista.append("Archivo .env encontrado")
    from dotenv import load_dotenv
    load_dotenv()

    campos_requeridos = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS"]
    for campo in campos_requeridos:
        val = os.getenv(campo)
        if not val:
            errores.append(
                f"El .env no tiene el campo: {campo}\n"
                f"   Abre .env y agrega: {campo}=valor"
            )
        elif campo == "DB_PASS" and val in ("tu_contraseña_aqui", "", "password"):
            warnings.append(
                f"DB_PASS parece ser el valor de ejemplo.\n"
                f"   Cambia 'tu_contraseña_aqui' por tu contraseña real de MySQL."
            )
        else:
            if campo != "DB_PASS":
                ok_lista.append(f".env {campo}={val}")
            else:
                ok_lista.append(f".env DB_PASS=****** (configurado)")
else:
    errores.append(
        "No existe el archivo .env\n"
        "   Solución: copia .env.example y renómbralo a .env\n"
        "   Luego edítalo con tus datos de MySQL."
    )

# ── 4. Estructura de carpetas ────────────────────────────────────
carpetas = ["database", "models", "services", "ui", "utils"]
for carpeta in carpetas:
    if os.path.isdir(carpeta):
        ok_lista.append(f"Carpeta: {carpeta}/")
    else:
        errores.append(
            f"No existe la carpeta: {carpeta}/\n"
            f"   Solución: asegúrate de ejecutar desde la carpeta raíz del proyecto."
        )

# ── 5. Archivos críticos ─────────────────────────────────────────
archivos = [
    "main.py",
    "database/base.py",
    "database/connection.py",
    "models/__init__.py",
    "services/auth_service.py",
    "ui/login_window.py",
    "ui/main_window.py",
    "utils/themes.py",
]
for archivo in archivos:
    if os.path.exists(archivo):
        ok_lista.append(f"Archivo: {archivo}")
    else:
        errores.append(
            f"No existe el archivo: {archivo}\n"
            f"   Solución: descomprime el ZIP en la carpeta correcta."
        )

# ── 6. Conexión a MySQL ──────────────────────────────────────────
if not errores:   # solo intentar si todo lo anterior está OK
    try:
        sys.path.insert(0, ".")
        from database.connection import probar_conexion
        ok_conn, msg_conn = probar_conexion()
        if ok_conn:
            ok_lista.append("Conexión a MySQL: OK")
        else:
            errores.append(
                f"No se pudo conectar a MySQL:\n"
                f"   {msg_conn}\n\n"
                f"   Verifica:\n"
                f"   1. MySQL está corriendo (ábrelo en servicios de Windows)\n"
                f"   2. El usuario y contraseña en .env son correctos\n"
                f"   3. La base de datos '{os.getenv('DB_NAME','unab_talleres')}' existe\n"
                f"      Si no existe, créala en MySQL Workbench:\n"
                f"      CREATE DATABASE unab_talleres CHARACTER SET utf8mb4;"
            )
    except Exception as e:
        errores.append(f"Error al importar módulos del proyecto:\n   {e}")
else:
    warnings.append("Saltando prueba de MySQL — resuelve los errores anteriores primero.")

# ── REPORTE FINAL ────────────────────────────────────────────────
print()
if ok_lista:
    print("✅  TODO OK:")
    for item in ok_lista:
        print(f"    {item}")

if warnings:
    print()
    print("⚠️   ADVERTENCIAS:")
    for i, w in enumerate(warnings, 1):
        print(f"\n    [{i}] {w}")

if errores:
    print()
    print("❌  ERRORES QUE DEBES CORREGIR:")
    for i, e in enumerate(errores, 1):
        print(f"\n    [{i}] {e}")
    print()
    print("─" * 60)
    print("  Corrige los errores en orden y vuelve a ejecutar")
    print("  este diagnóstico hasta que no haya errores.")
    print("─" * 60)
else:
    print()
    print("─" * 60)
    print("  Sin errores. Ejecuta: python main.py")
    print("─" * 60)

print()
