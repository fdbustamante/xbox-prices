"""
Funciones para gestionar los datos de juegos (cargar, guardar, etc).
"""
import os
import json
import datetime
from scrap.config import logger

def cargar_datos_previos(json_file_path):
    """Carga los datos de juegos previos desde un archivo JSON si existe."""
    if not os.path.exists(json_file_path):
        print(f"No existe archivo previo {json_file_path}")
        return {}
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        # Crear un diccionario para buscar rápidamente por título
        juegos_previos = {}
        if 'juegos' in datos and isinstance(datos['juegos'], list):
            for juego in datos['juegos']:
                if 'titulo' in juego and 'precio_num' in juego:
                    juegos_previos[juego['titulo']] = juego
        
        print(f"Datos previos cargados: {len(juegos_previos)} juegos")
        return juegos_previos
    except Exception as e:
        print(f"Error al cargar datos previos: {e}")
        return {}

def guardar_datos(juegos, output_filename):
    """Guarda los datos de juegos en un archivo JSON."""
    try:
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos_completos = {
            "fecha_creacion": fecha_actual,
            "juegos": juegos
        }
        
        # Asegurarse de que el directorio exista
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, ensure_ascii=False, indent=4)
        
        print(f"\nDatos guardados en {output_filename} con fecha: {fecha_actual}")
        return fecha_actual
    except Exception as e:
        logger.error(f"Error al guardar los datos en JSON: {e}")
        return None

def filtrar_juegos_por_precio(juegos, tipo_filtro="decreased"):
    """Filtra la lista de juegos según el cambio de precio."""
    return [j for j in juegos if j['precio_cambio'] == tipo_filtro]

def generar_mensaje_telegram(juegos_bajaron_precio, fecha_actual, debug=False):
    """Genera el mensaje para enviar a Telegram."""
    mensaje = f"<b>🎮 ALERTA DE BAJADA DE PRECIOS XBOX PC</b>\n\n"
    mensaje += f"<i>Fecha: {fecha_actual}</i>\n\n"
    
    if juegos_bajaron_precio:
        mensaje += f"<b>Encontré {len(juegos_bajaron_precio)} juegos que bajaron de precio:</b>\n\n"
        
        # Mostrar primero los juegos con mayor porcentaje de descuento o mayor diferencia absoluta
        top_juegos = sorted(
            juegos_bajaron_precio, 
            key=lambda j: abs((j['precio_num'] or 0) - (j['precio_anterior_num'] or 0)) if j['precio_anterior_num'] else 0,
            reverse=True
        )[:10]  # Mostrar máximo 10 juegos en la notificación
        
        for i, juego in enumerate(top_juegos, 1):
            titulo = juego['titulo']
            precio_actual = juego['precio_num']
            precio_anterior = juego['precio_anterior_num']
            link = juego['link']
            
            # Calcular el porcentaje de descuento respecto al precio anterior
            porcentaje = 0
            if precio_anterior and precio_actual:
                porcentaje = (1 - (precio_actual / precio_anterior)) * 100
            
            precio_actual_fmt = f"ARS$ {precio_actual:,.2f}".replace(',', '.')
            precio_anterior_fmt = f"ARS$ {precio_anterior:,.2f}".replace(',', '.')
            
            mensaje += f"{i}. <b>{titulo}</b>\n"
            mensaje += f"   ↓ Bajó de {precio_anterior_fmt} a {precio_actual_fmt} (-{porcentaje:.1f}%)\n"
            mensaje += f"   🔗 <a href=\"{link}\">Ver en la tienda</a>\n\n"
        
        if len(juegos_bajaron_precio) > 10:
            mensaje += f"<i>... y {len(juegos_bajaron_precio) - 10} juegos más con bajadas de precio.</i>\n"
        
        mensaje += f"\n🌐 <a href=\"https://fdbustamante.github.io/xbox-prices/\">Ver todos los juegos</a>"
    else:
        mensaje += "<i>No se encontraron juegos que hayan bajado de precio, este es un mensaje de prueba.</i>"
    
    return mensaje
