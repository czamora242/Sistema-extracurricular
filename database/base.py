"""
¿Por qué un archivo separado?
  Si Base estuviera en connection.py, los modelos importarían
  connection.py y ese archivo importaría los modelos → importación
  circular. Tenerla separada rompe ese ciclo.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base común de todos los modelos SQLAlchemy del proyecto."""
    pass
