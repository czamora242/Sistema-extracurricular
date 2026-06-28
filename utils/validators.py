"""
utils/validators.py
═══════════════════════════════════════════════════════════════

Funciones de validación reutilizables para toda la aplicación.

EJEMPLOS:
  from utils.validators import validar_email, validar_dni

  es_válido, error = validar_email("juan@unab.edu.pe")
  es_válido, error = validar_dni("12345678")
"""

from typing import Tuple
import re


# ═══════════════════════════════════════════════════════════════════════════
# VALIDADORES DE IDENTIDAD
# ═══════════════════════════════════════════════════════════════════════════

def validar_dni(dni: str) -> Tuple[bool, str]:
    """
    Valida un DNI peruano.
    Debe tener 8 dígitos numéricos.
    """
    dni_limpio = dni.strip()

    if not dni_limpio:
        return False, "El DNI es obligatorio"

    if not dni_limpio.isdigit():
        return False, "El DNI debe contener solo dígitos"

    if len(dni_limpio) != 8:
        return False, "El DNI debe tener 8 dígitos"

    return True, ""


def validar_codigo_estudiantil(codigo: str) -> Tuple[bool, str]:
    """
    Valida un código estudiantil.
    Formato esperado: 7-8 caracteres alpanuméricos.
    Ej: 2024001, A2024001
    """
    codigo_limpio = codigo.strip().upper()

    if not codigo_limpio:
        return False, "El código estudiantil es obligatorio"

    if not codigo_limpio.replace("-", "").isalnum():
        return False, "El código debe ser alfanumérico"

    if len(codigo_limpio) < 6:
        return False, "El código debe tener al menos 6 caracteres"

    if len(codigo_limpio) > 20:
        return False, "El código no puede exceder 20 caracteres"

    return True, ""


# ═══════════════════════════════════════════════════════════════════════════
# VALIDADORES DE COMUNICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def validar_email(email: str) -> Tuple[bool, str]:
    """
    Valida un correo electrónico.
    """
    email_limpio = email.strip().lower()

    if not email_limpio:
        return False, "El correo es obligatorio"

    # Expresión regular básica pero efectiva
    patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(patron, email_limpio):
        return False, "El correo no tiene un formato válido"

    return True, ""


def validar_email_institucional(email: str) -> Tuple[bool, str]:
    """
    Valida que sea un correo institucional (@unab.edu.pe).
    """
    es_valido, error = validar_email(email)
    if not es_valido:
        return False, error

    if not email.strip().lower().endswith("@unab.edu.pe"):
        return False, "El correo debe ser institucional (@unab.edu.pe)"

    return True, ""


def validar_telefono(telefono: str) -> Tuple[bool, str]:
    """
    Valida un número de teléfono peruano.
    Acepta: 9 dígitos, con o sin espacios/guiones.
    Ej: 987654321, 98 765 4321, 98-765-4321
    """
    telefono_limpio = "".join(c for c in telefono if c.isdigit())

    if not telefono_limpio:
        return False, "El teléfono es obligatorio"

    if len(telefono_limpio) != 9:
        return False, "El teléfono debe tener 9 dígitos"

    if not telefono_limpio.startswith("9"):
        return False, "El teléfono peruano debe empezar con 9"

    return True, ""


# ═══════════════════════════════════════════════════════════════════════════
# VALIDADORES DE NOMBRES Y TEXTO
# ═══════════════════════════════════════════════════════════════════════════

def validar_nombres(nombres: str, min_len: int = 2, max_len: int = 100) -> Tuple[bool, str]:
    """
    Valida un campo de nombres.
    """
    nombres_limpio = nombres.strip()

    if not nombres_limpio:
        return False, "El nombre es obligatorio"

    if len(nombres_limpio) < min_len:
        return False, f"El nombre debe tener al menos {min_len} caracteres"

    if len(nombres_limpio) > max_len:
        return False, f"El nombre no puede exceder {max_len} caracteres"

    return True, ""


def validar_apellidos(apellidos: str) -> Tuple[bool, str]:
    """
    Valida un campo de apellidos.
    """
    return validar_nombres(apellidos, min_len=2, max_len=100)


def validar_username(username: str) -> Tuple[bool, str]:
    """
    Valida un nombre de usuario.
    - 4-20 caracteres
    - Solo letras, números y guiones bajos
    - No espacios ni caracteres especiales
    """
    username_limpio = username.strip().lower()

    if not username_limpio:
        return False, "El nombre de usuario es obligatorio"

    if len(username_limpio) < 4:
        return False, "El usuario debe tener al menos 4 caracteres"

    if len(username_limpio) > 20:
        return False, "El usuario no puede exceder 20 caracteres"

    if not re.match(r"^[a-z0-9_-]+$", username_limpio):
        return False, "El usuario solo puede contener letras, números, guiones y guiones bajos"

    return True, ""


def validar_password(password: str) -> Tuple[bool, str]:
    """
    Valida una contraseña.

    REQUISITOS:
      - Al menos 8 caracteres
      - Al menos 1 mayúscula
      - Al menos 1 minúscula
      - Al menos 1 número
      - Al menos 1 carácter especial (!@#$%^&*)

    RETORNA:
      (True, "") si es válida
      (False, "error") si no cumple los requisitos
    """
    pwd = password.strip()

    if not pwd:
        return False, "La contraseña es obligatoria"

    if len(pwd) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if not any(c.isupper() for c in pwd):
        return False, "La contraseña debe contener al menos 1 mayúscula"

    if not any(c.islower() for c in pwd):
        return False, "La contraseña debe contener al menos 1 minúscula"

    if not any(c.isdigit() for c in pwd):
        return False, "La contraseña debe contener al menos 1 número"

    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in pwd):
        return False, "La contraseña debe contener al menos 1 carácter especial (!@#$%^&*)"

    return True, ""


# ═══════════════════════════════════════════════════════════════════════════
# VALIDADORES DE FORMATO
# ═══════════════════════════════════════════════════════════════════════════

def validar_codigo_taller(codigo: str) -> Tuple[bool, str]:
    """
    Valida un código de taller.
    Formato esperado: TAL-2025-001, o similar.
    """
    codigo_limpio = codigo.strip().upper()

    if not codigo_limpio:
        return False, "El código del taller es obligatorio"

    if not re.match(r"^[A-Z]{2,4}-\d{4}-\d{3,}$", codigo_limpio):
        return False, "El código debe tener formato: TAL-2025-001"

    return True, ""


def validar_fecha(fecha_str: str, formato: str = "%d/%m/%Y") -> Tuple[bool, str]:
    """
    Valida una fecha en string.
    """
    from datetime import datetime

    try:
        datetime.strptime(fecha_str.strip(), formato)
        return True, ""
    except ValueError:
        return False, f"La fecha no tiene un formato válido. Esperado: {formato}"


def validar_hora(hora_str: str, formato: str = "%H:%M") -> Tuple[bool, str]:
    """
    Valida una hora en string.
    """
    from datetime import datetime

    try:
        datetime.strptime(hora_str.strip(), formato)
        return True, ""
    except ValueError:
        return False, f"La hora no tiene un formato válido. Esperado: {formato}"


# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════

def limpiar_texto(texto: str) -> str:
    """
    Limpia un texto: trimming, normaliza espacios.
    """
    return " ".join(texto.strip().split())


def es_vacio_o_nulo(valor) -> bool:
    """
    Verifica si un valor es None, vacío o whitespace-only.
    """
    if valor is None:
        return True
    return str(valor).strip() == ""
