"""
Funciones de utilidad para el scraping de precios de juegos de Xbox.
"""
import re

def clean_price_to_float(price_str):
    """Limpia una cadena de precio (ARS$ X.XXX,XX) y la convierte a float."""
    if not price_str or not isinstance(price_str, str):
        return None
    
    num_str = price_str.upper().replace("ARS$", "").replace("+", "").strip()
    num_str = num_str.replace(".", "")
    num_str = num_str.replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        return None

def extract_discount_percentage(discount_text_str):
    """Extrae el porcentaje de descuento numérico de un texto como '-20%'."""
    if not discount_text_str or not isinstance(discount_text_str, str):
        return None
    match = re.search(r"(\d+)\s*%", discount_text_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def comparar_precio(precio_actual, precio_previo):
    """Compara dos precios y determina si subió, bajó o sigue igual."""
    if precio_actual is None or precio_previo is None:
        return None
    
    if precio_actual > precio_previo:
        return "increased"
    elif precio_actual < precio_previo:
        return "decreased"
    else:
        return "unchanged"
