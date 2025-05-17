"""
Funciones de utilidad para el scraping de precios de juegos de Xbox.
"""
import re
from typing import Optional, Union, Literal

# Compilar las expresiones regulares para mejor rendimiento
PRICE_PATTERN = re.compile(r'[^\d,.]+')
DISCOUNT_PATTERN = re.compile(r"(\d+)\s*%")

def clean_price_to_float(price_str: Optional[str]) -> Optional[float]:
    """
    Limpia una cadena de precio (ARS$ X.XXX,XX) y la convierte a float.
    
    Args:
        price_str: String que contiene el precio a convertir
        
    Returns:
        Valor float del precio o None si no se puede convertir
    """
    if not price_str or not isinstance(price_str, str):
        return None
    
    try:
        # Eliminar todo excepto dígitos, puntos y comas
        num_str = PRICE_PATTERN.sub('', price_str.strip())
        # Reemplazar separadores de miles y decimales
        num_str = num_str.replace(".", "").replace(",", ".")
        return float(num_str) if num_str else None
    except (ValueError, TypeError):
        return None

def extract_discount_percentage(discount_text_str: Optional[str]) -> Optional[float]:
    """
    Extrae el porcentaje de descuento numérico de un texto como '-20%'.
    
    Args:
        discount_text_str: String que contiene el porcentaje de descuento
        
    Returns:
        Valor float del porcentaje de descuento o None si no se encuentra
    """
    if not discount_text_str or not isinstance(discount_text_str, str):
        return None
    
    match = DISCOUNT_PATTERN.search(discount_text_str)
    try:
        return float(match.group(1)) if match else None
    except (ValueError, AttributeError):
        return None

def comparar_precio(precio_actual: Optional[float], precio_previo: Optional[float]) -> Optional[Literal["increased", "decreased", "unchanged"]]:
    """
    Compara dos precios y determina si subió, bajó o sigue igual.
    
    Args:
        precio_actual: Precio actual del juego
        precio_previo: Precio previo del juego para comparar
        
    Returns:
        String que indica si el precio aumentó, disminuyó o no cambió
    """
    if precio_actual is None or precio_previo is None:
        return None
    
    # Usar una pequeña tolerancia para evitar problemas con números flotantes
    epsilon = 0.001
    diff = precio_actual - precio_previo
    
    if diff > epsilon:
        return "increased"
    elif diff < -epsilon:
        return "decreased"
    else:
        return "unchanged"
