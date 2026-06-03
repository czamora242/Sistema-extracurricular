import sys, os
sys.path.insert(0, ".")

print("Creando usuario administrador inicial...")

# Verificar .env
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("DB_PASS"):
    print("❌ No encontré el archivo .env")
    print("   Copia .env.example → .env y configura tus datos de MySQL.")
    sys.exit(1)

# Importar modelos y conexión
try:
    from database.connection import engine, probar_conexion
    from database.base import Base
    import models
    from models import Rol, Usuario
    from database.connection import get_session
except Exception as e:
    print(f"❌ Error al importar el proyecto: {e}")
    print("   Asegúrate de tener el entorno virtual activado.")
    print("   Ejecuta: venv\\Scripts\\activate")
    sys.exit(1)

# Verificar conexión
ok, msg = probar_conexion()
if not ok:
    print(f"❌ No se pudo conectar a MySQL: {msg}")
    print()
    print("   Verifica:")
    print("   1. MySQL está corriendo")
    print("   2. Los datos en .env son correctos")
    print(f"   3. La BD '{os.getenv('DB_NAME')}' existe")
    sys.exit(1)

print("✅ Conexión a MySQL OK")

# Crear todas las tablas si no existen
Base.metadata.create_all(engine)
print("✅ Tablas creadas/verificadas")

# Verificar si ya existe el admin
with get_session() as session:
    admin_existente = session.query(Usuario).filter(
        Usuario.username == "admin"
    ).first()

    if admin_existente:
        print()
        print("⚠️  El usuario 'admin' ya existe.")
        respuesta = input("   ¿Deseas cambiar su contraseña? (s/n): ").strip().lower()
        if respuesta == "s":
            nueva = input("   Nueva contraseña (mínimo 8 caracteres): ").strip()
            if len(nueva) < 8:
                print("❌ La contraseña debe tener al menos 8 caracteres.")
                sys.exit(1)
            admin_existente.set_password(nueva)
            print("✅ Contraseña actualizada.")
        else:
            print("   Sin cambios.")
        sys.exit(0)

    # Crear rol Administrador si no existe
    rol_admin = session.query(Rol).filter(Rol.nombre == "Administrador").first()
    if not rol_admin:
        rol_admin = Rol(nombre="Administrador", descripcion="Acceso total al sistema")
        session.add(rol_admin)

        # Crear también los otros roles
        session.add(Rol(nombre="Docente",   descripcion="Gestiona asistencia de sus talleres"))
        session.add(Rol(nombre="Operador",  descripcion="Gestiona bienes patrimoniales"))
        session.flush()   # obtener los IDs sin hacer commit todavía
        print("✅ Roles creados: Administrador, Docente, Operador")

    # Crear usuario admin
    nuevo_admin = Usuario(
        rol_id    = rol_admin.id,
        nombres   = "Administrador",
        apellidos = "Sistema",
        username  = "admin",
        email     = "admin@unab.edu.pe",
        activo    = True,
    )
    nuevo_admin.set_password("Admin1234!")
    session.add(nuevo_admin)

print()
print("══════════════════════════════════════════")
print("  Usuario administrador creado exitosamente")
print("══════════════════════════════════════════")
print()
print("  Usuario:    admin")
print("  Contraseña: Admin1234!")
print()
print("  ⚠️  Cambia la contraseña después del primer login.")
print()
print("  Ejecuta la aplicación con: python main.py")
print("══════════════════════════════════════════")
