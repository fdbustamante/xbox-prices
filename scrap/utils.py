"""
Funciones de utilidad para el scraping de precios de juegos de Xbox.
"""
import re
from typing import Optional, Union, Literal

# Compilar expresiones regulares para mejorar el rendimiento
_PRICE_CLEAN_PATTERN = re.compile(r'[^\d,.]+')  # Elimina todo excepto dígitos, puntos y comas
_DISCOUNT_PERCENT_PATTERN = re.compile(r"(\d+)\s*%")  # Extrae el número antes del símbolo %

def clean_price_to_float(price_str: Optional[str]) -> Optional[float]:
    """
    Convierte una cadena de precio (ej: 'ARS$ 1.234,56') a float.
    Args:
        price_str: Cadena con el precio a convertir.
    Returns:
        Valor float del precio o None si no es posible convertir.
    """
    if not isinstance(price_str, str) or not price_str:
        return None
    try:
        # Eliminar caracteres no numéricos relevantes
        num_str = _PRICE_CLEAN_PATTERN.sub('', price_str.strip())
        # Unificar formato: quitar separador de miles y usar punto decimal
        num_str = num_str.replace('.', '').replace(',', '.')
        return float(num_str) if num_str else None
    except (ValueError, TypeError):
        return None

def extract_discount_percentage(discount_text: Optional[str]) -> Optional[float]:
    """
    Extrae el porcentaje de descuento numérico de un texto como '-20%'.
    Args:
        discount_text: Cadena con el porcentaje de descuento.
    Returns:
        Porcentaje de descuento como float, o None si no se encuentra.
    """
    if not isinstance(discount_text, str) or not discount_text:
        return None
    match = _DISCOUNT_PERCENT_PATTERN.search(discount_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def comparar_precio(
    precio_actual: Optional[float],
    precio_previo: Optional[float]
) -> Optional[Literal["increased", "decreased", "unchanged"]]:
    """
    Compara dos precios y determina si subió, bajó o sigue igual.
    Args:
        precio_actual: Precio actual del juego.
        precio_previo: Precio previo del juego para comparar.
    Returns:
        'increased' si subió, 'decreased' si bajó, 'unchanged' si no cambió, o None si falta algún dato.
    """
    if precio_actual is None or precio_previo is None:
        return None
    # Tolerancia para evitar errores por precisión de float
    epsilon = 1e-3
    diff = precio_actual - precio_previo
    if diff > epsilon:
        return "increased"
    elif diff < -epsilon:
        return "decreased"
    return "unchanged"
