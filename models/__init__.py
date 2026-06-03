"""
models/__init__.py
──────────────────
Importa TODOS los modelos en un solo lugar.

¿Por qué es necesario?
  SQLAlchemy solo puede crear las tablas (Base.metadata.create_all)
  o resolver las relaciones si ha "visto" todas las clases antes.
  Importar este __init__ garantiza que eso ocurra.

USO en cualquier parte del proyecto:
    from models import Estudiante, Taller, Asistencia
    # en vez de:
    from models.estudiante import Estudiante
    from models.taller import Taller
    ...
"""

# EP-01 · Autenticación
from models.rol      import Rol
from models.usuario  import Usuario
from models.auditoria import Auditoria

# EP-02 · Estudiantes
from models.academico   import Facultad, Carrera
from models.estudiante  import Estudiante

# EP-03 · Talleres
from models.ciclo_docente import CicloAcademico, Docente
from models.taller        import Taller, Sesion, Inscripcion

# EP-04 · Asistencia
from models.asistencia import Asistencia

# EP-05 · Lista de Aptos
from models.lista_aptos import ListaAptos, ListaAptoDetalle

# EP-06 · Bienes Patrimoniales
from models.bienes import BienPatrimonial, AsignacionBien

__all__ = [
    # EP-01
    "Rol", "Usuario", "Auditoria",
    # EP-02
    "Facultad", "Carrera", "Estudiante",
    # EP-03
    "CicloAcademico", "Docente", "Taller", "Sesion", "Inscripcion",
    # EP-04
    "Asistencia",
    # EP-05
    "ListaAptos", "ListaAptoDetalle",
    # EP-06
    "BienPatrimonial", "AsignacionBien",
]
