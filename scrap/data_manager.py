"""
Funciones para gestionar los datos de juegos (cargar, guardar, etc).
"""
import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TypedDict
from scrap.config import logger

class GameDict(TypedDict, total=False):
    """Tipo para representar un juego en formato diccionario."""
    titulo: str
    link: str
    imagen_url: str
    precio_num: Optional[float]
    precio_old_num: Optional[float]
    precio_descuento_num: Optional[float]
    precio_texto: str
    precio_cambio: Optional[str]
    precio_anterior_num: Optional[float]

def cargar_datos_previos(json_file_path: str) -> Dict[str, GameDict]:
    """
    Carga los datos de juegos previos desde un archivo JSON si existe.
    
    Args:
        json_file_path: Ruta al archivo JSON con los datos previos
        
    Returns:
        Diccionario con los juegos previos indexados por título
    """
    path = Path(json_file_path)
    if not path.exists():
        logger.info(f"No existe archivo previo {json_file_path}")
        return {}
    
    try:
        with path.open('r', encoding='utf-8') as f:
            datos = json.load(f)
            
        # Crear un diccionario para buscar rápidamente por título
        juegos_previos = {}
        if isinstance(datos, dict) and 'juegos' in datos and isinstance(datos['juegos'], list):
            # Usar comprensión de diccionario para crear el índice
            juegos_previos = {
                juego['titulo']: juego 
                for juego in datos['juegos'] 
                if 'titulo' in juego
            }
        
        logger.info(f"Datos previos cargados: {len(juegos_previos)} juegos")
        return juegos_previos
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON de datos previos: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error al cargar datos previos: {e}")
        return {}

def guardar_datos(juegos: List[GameDict], output_filename: str) -> Optional[str]:
    """
    Guarda los datos de juegos en un archivo JSON.
    
    Args:
        juegos: Lista de diccionarios con los datos de los juegos
        output_filename: Ruta donde se guardará el archivo JSON
        
    Returns:
        String con la fecha de creación o None si ocurrió un error
    """
    from scrap.config import get_formatted_datetime
    fecha_actual = get_formatted_datetime()
    datos_completos = {
        "fecha_creacion": fecha_actual,
        "total_juegos": len(juegos),
        "juegos": juegos
    }
    
    try:
        # Asegurarse de que el directorio exista
        Path(output_filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Datos guardados en {output_filename} con fecha: {fecha_actual}")
        return fecha_actual
    except Exception as e:
        logger.error(f"Error al guardar los datos en JSON: {e}")
        return None

def filtrar_juegos_por_precio(juegos: List[GameDict], tipo_filtro: str = "decreased") -> List[GameDict]:
    """
    Filtra la lista de juegos según el cambio de precio.
    
    Args:
        juegos: Lista de juegos a filtrar
        tipo_filtro: Tipo de cambio a filtrar ("decreased", "increased", "unchanged")
        
    Returns:
        Lista de juegos que cumplen con el filtro
    """
    return [j for j in juegos if j.get('precio_cambio') == tipo_filtro]

def _formatear_precio(valor: Optional[float]) -> str:
    """Formatea un valor numérico como string de precio."""
    if valor is None:
        return "N/A"
    return f"ARS$ {valor:,.2f}".replace(',', '.')

def generar_mensaje_telegram(juegos_bajaron_precio: List[GameDict], fecha_actual: str, debug: bool = False) -> str:
    """
    Genera el mensaje para enviar a Telegram.
    
    Args:
        juegos_bajaron_precio: Lista de juegos que bajaron de precio
        fecha_actual: Fecha actual formateada como string
        debug: Indica si está en modo debug
        
    Returns:
        Mensaje formateado para enviar a Telegram
    """
    mensaje = [
        "<b>🎮 ALERTA DE BAJADA DE PRECIOS XBOX PC</b>",
        "",
        f"<i>Fecha: {fecha_actual}</i>",
        ""
    ]
    
    if not juegos_bajaron_precio and not debug:
        mensaje.append("<i>No se encontraron juegos que hayan bajado de precio.</i>")
        return "\n".join(mensaje)
    
    if juegos_bajaron_precio:
        mensaje.append(f"<b>Encontré {len(juegos_bajaron_precio)} juegos que bajaron de precio:</b>")
        mensaje.append("")
        
        # Ordenar por mayor diferencia de precio (absoluta)
        def calcular_diferencia(juego: GameDict) -> float:
            actual = juego.get('precio_num') or 0
            anterior = juego.get('precio_anterior_num') or 0
            return abs(anterior - actual)
        
        # Mostrar máximo 10 juegos en la notificación
        top_juegos = sorted(juegos_bajaron_precio, key=calcular_diferencia, reverse=True)[:10]
        
        for i, juego in enumerate(top_juegos, 1):
            titulo = juego.get('titulo', 'Sin título')
            precio_actual = juego.get('precio_num')
            precio_anterior = juego.get('precio_anterior_num')
            link = juego.get('link', '#')
            
            # Calcular el porcentaje de descuento respecto al precio anterior
            porcentaje = 0
            if precio_anterior and precio_actual and precio_anterior > 0:
                porcentaje = (1 - (precio_actual / precio_anterior)) * 100
            
            precio_actual_fmt = _formatear_precio(precio_actual)
            precio_anterior_fmt = _formatear_precio(precio_anterior)
            
            mensaje.extend([
                f"{i}. <b>{titulo}</b>",
                f"   ↓ Bajó de {precio_anterior_fmt} a {precio_actual_fmt} (-{porcentaje:.1f}%)",
                f"   🔗 <a href=\"{link}\">Ver en la tienda</a>",
                ""
            ])
        
        if len(juegos_bajaron_precio) > 10:
            mensaje.append(f"<i>... y {len(juegos_bajaron_precio) - 10} juegos más con bajadas de precio.</i>")
        
        mensaje.append("\n🌐 <a href=\"https://fdbustamante.github.io/xbox-prices/\">Ver todos los juegos</a>")
    else:
        mensaje.append("<i>No se encontraron juegos que hayan bajado de precio, este es un mensaje de prueba.</i>")
    
    return "\n".join(mensaje)
