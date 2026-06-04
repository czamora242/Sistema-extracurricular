GUÍA DE INSTALACIÓN — Sistema de Talleres UNAB
═══════════════════════════════════════════════

PASO 1 — INSTALAR PYTHON
─────────────────────────
1. Descarga Python 3.11 desde: https://www.python.org/downloads/
2. Durante la instalación:
   ✅ Marca "Add Python to PATH" (muy importante)
   ✅ Marca "Install for all users"
3. Verifica en CMD:
   python --version
   → Debe mostrar: Python 3.11.x


PASO 2 — EXTRAER EL PROYECTO
─────────────────────────────
1. Descomprime el ZIP en una carpeta, por ejemplo:
   C:\Proyectos\unab_talleres\

2. La estructura debe quedar así:
   unab_talleres\
   ├── main.py
   ├── diagnostico.py
   ├── requirements.txt
   ├── .env.example
   ├── database\
   ├── models\
   ├── services\
   ├── ui\
   └── utils\


PASO 3 — ABRIR CMD EN LA CARPETA DEL PROYECTO
──────────────────────────────────────────────
Opción A (recomendada):
  1. Abre la carpeta en el Explorador de Windows
  2. Clic en la barra de direcciones
  3. Escribe: cmd
  4. Presiona Enter

Opción B:
  1. Abre CMD (Win+R → cmd → Enter)
  2. Escribe: cd C:\Proyectos\unab_talleres
  3. Presiona Enter


PASO 4 — CREAR ENTORNO VIRTUAL
────────────────────────────────
En el CMD dentro de la carpeta del proyecto:

  python -m venv venv

Luego activarlo:

  Windows:   venv\Scripts\activate
  (verás que el CMD muestra "(venv)" al inicio)


PASO 5 — INSTALAR LIBRERÍAS
────────────────────────────
Con el entorno virtual activado:

  pip install -r requirements.txt

Esto instala: PySide6, SQLAlchemy, pymysql, bcrypt,
openpyxl, alembic, python-dotenv, reportlab, pytest


PASO 6 — CONFIGURAR LA BASE DE DATOS
──────────────────────────────────────
1. Instala MySQL 8.0: https://dev.mysql.com/downloads/installer/
   (elige "MySQL Server" + "MySQL Workbench")

2. Abre MySQL Workbench
3. Conéctate al servidor local
4. Ejecuta este comando:

   CREATE DATABASE unab_talleres CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

5. Anota tu usuario y contraseña de MySQL


PASO 7 — CREAR EL ARCHIVO .env
────────────────────────────────
1. En la carpeta del proyecto, copia .env.example y llámalo .env
   (solo cambiar el nombre, sin extensión .example)

2. Abre .env con el Bloc de Notas y edita:

   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=unab_talleres
   DB_USER=root
   DB_PASS=tu_contraseña_mysql_aqui    ← cambia esto

   SECRET_KEY=unab2025clave_segura_larga
   RUTA_FOTOS=storage/fotos_estudiantes
   RUTA_EXCEL=storage/listas_excel
   RUTA_PDF=storage/pdfs_bienes
   APP_VERSION=1.0.0
   APP_NOMBRE=Sistema de Talleres UNAB
   APP_TEMA=claro

3. Guarda el archivo


PASO 8 — EJECUTAR EL DIAGNÓSTICO
──────────────────────────────────
Con el entorno virtual activado, en el CMD:

  python diagnostico.py

Si dice "Sin errores" → continúa al paso 9.
Si muestra errores → síguelas instrucciones que aparecen.


PASO 9 — CREAR EL USUARIO ADMINISTRADOR INICIAL
─────────────────────────────────────────────────
Con el entorno virtual activado:

  python crear_admin.py

Esto crea el usuario admin con:
  Usuario:    admin
  Contraseña: Admin1234!
  (cámbiala después del primer login)


PASO 10 — EJECUTAR LA APLICACIÓN
──────────────────────────────────
  python main.py

La aplicación abrirá el login.
Ingresa con: admin / Admin1234!


─────────────────────────────────────────────────
PROBLEMAS COMUNES
─────────────────────────────────────────────────

ERROR: "python no se reconoce como comando"
  → Python no está en el PATH.
  → Reinstala Python y marca "Add Python to PATH".

ERROR: "No module named 'PySide6'"
  → El entorno virtual no está activado.
  → Ejecuta: venv\Scripts\activate

ERROR: "Access denied for user 'root'"
  → La contraseña en .env es incorrecta.
  → Verifica tu contraseña de MySQL.

ERROR: "Unknown database 'unab_talleres'"
  → La base de datos no existe.
  → Ejecútalo en MySQL Workbench:
    CREATE DATABASE unab_talleres CHARACTER SET utf8mb4;

ERROR: "Can't connect to MySQL server"
  → MySQL no está corriendo.
  → Abre "Servicios" de Windows y busca "MySQL80",
    haz clic en "Iniciar".
─────────────────────────────────────────────────
