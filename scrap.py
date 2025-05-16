import time
import json
import datetime
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from telegram import Bot
from telegram.error import TelegramError
import asyncio

# Configuración de Telegram (prioriza variables de entorno por sobre configuración local)
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
DEBUG = os.environ.get('TELEGRAM_DEBUG', 'False').lower() == 'true'

# Si no hay variables de entorno, intenta importar del archivo de configuración local
if not BOT_TOKEN or not CHAT_ID:
    try:
        from telegram_config import BOT_TOKEN as CONFIG_BOT_TOKEN
        from telegram_config import CHAT_ID as CONFIG_CHAT_ID
        from telegram_config import DEBUG as CONFIG_DEBUG
        
        # Solo usa la configuración del archivo si no se establecieron variables de entorno
        if not BOT_TOKEN:
            BOT_TOKEN = CONFIG_BOT_TOKEN
        if not CHAT_ID:
            CHAT_ID = CONFIG_CHAT_ID
        if os.environ.get('TELEGRAM_DEBUG') is None:
            DEBUG = CONFIG_DEBUG
            
        print("Usando configuración de Telegram desde archivo local")
    except ImportError:
        print("ADVERTENCIA: No se encontró archivo de configuración de Telegram ni variables de entorno. Las notificaciones estarán desactivadas.")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xbox_prices_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

async def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje a través de Telegram usando el bot configurado."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("No se puede enviar mensaje a Telegram: token o chat_id no configurados")
        return False
    
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=mensaje, parse_mode="HTML")
        logger.info(f"Mensaje enviado a Telegram correctamente")
        return True
    except TelegramError as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar mensaje a Telegram: {e}")
        return False

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


def scrape_xbox_games(datos_previos=None):
    url = "https://www.xbox.com/es-AR/games/all-games/pc?PlayWith=PC&xr=shellnav"
    base_url_for_links = "https://www.xbox.com"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    print("Iniciando el navegador...")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error al iniciar ChromeDriver: {e}")
        return []

    print(f"Cargando página: {url}")
    driver.get(url)
    print("Esperando carga inicial de la página (10 segundos)...")
    time.sleep(10)

    try:
        cookie_button_xpath = "//button[@id='onetrust-accept-btn-handler']"
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))).click()
        print("Banner de cookies aceptado.")
        time.sleep(3)
    except TimeoutException:
        print("No se encontró el banner de cookies o ya fue aceptado.")
    except Exception as e:
        print(f"Error al aceptar cookies: {e}")

    game_grid_container_selector = "ol.SearchProductGrid-module__container___jew-i"
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, game_grid_container_selector)))
        print("Contenedor de la grilla de juegos encontrado.")
        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ProductCard-module__cardWrapper___6Ls86")))
        print("Primer item de juego visible.")
    except TimeoutException:
        print("Timeout: Contenedor de grilla o primer item no encontrado.")
        with open("xbox_page_source_error_grid.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        return []

    load_more_button_xpath = "//button[.//div[contains(text(),'Cargar más')]]"
    consecutive_failures = 0
    max_failures = 3
    last_item_count = 0
    MAX_GAMES_TO_LOAD = 4000

    while consecutive_failures < max_failures:
        current_items_count = len(driver.find_elements(By.CSS_SELECTOR, "div.ProductCard-module__cardWrapper___6Ls86"))
        print(f"Items actualmente cargados: {current_items_count}")

        if current_items_count >= MAX_GAMES_TO_LOAD:
            print(f"Límite de {MAX_GAMES_TO_LOAD} juegos alcanzado. Deteniendo carga.")
            break

        if current_items_count > 0 and current_items_count == last_item_count:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        last_item_count = current_items_count

        try:
            load_more_button = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, load_more_button_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'nearest'});", load_more_button)
            time.sleep(1.5)
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, load_more_button_xpath))
            )
            try:
                load_more_button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", load_more_button)
            print("Botón 'Cargar más' presionado.")
            WebDriverWait(driver, 25).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.ProductCard-module__cardWrapper___6Ls86")) > last_item_count
            )
            print(f"Nuevos items cargados. Total ahora: {len(driver.find_elements(By.CSS_SELECTOR, 'div.ProductCard-module__cardWrapper___6Ls86'))}")
            time.sleep(3)
        except TimeoutException:
            print("Botón 'Cargar más' no encontrado o no funcional.")
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                print("Se asume que todos los ítems están cargados o el botón ya no es funcional.")
                break
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(5)
        except Exception as e:
            print(f"Error en bucle 'Cargar más': {e}")
            consecutive_failures += 1
            time.sleep(5)
            if consecutive_failures >= max_failures:
                break
    
    print("Scroll final...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(4)

    page_source = driver.page_source
    driver.quit()
    print("Navegador cerrado.")

    with open("xbox_page_source.html", "w", encoding="utf-8") as f:
        f.write(page_source if page_source else "")
    print("HTML guardado en xbox_page_source.html.")

    soup = BeautifulSoup(page_source, 'html.parser')
    games_data = []
    game_items = soup.select("div.ProductCard-module__cardWrapper___6Ls86")
    print(f"Procesando {len(game_items)} items de juego con BeautifulSoup.")

    for item_index, item in enumerate(game_items):
        title_str = "Título no encontrado"
        link_str = "Enlace no encontrado"
        image_url_str = "Imagen no encontrada"
        
        price_text_display = "Precio no disponible" 
        current_price_num = None 
        old_price_num = None # Renombrado de original_price_num
        discount_percentage_num = None # Nuevo campo para el porcentaje

        # Título
        title_tag = item.select_one('span.ProductCard-module__title___nHGIp')
        if title_tag:
            title_str = title_tag.text.strip()

        # Enlace
        link_tag = item.select_one('a.commonStyles-module__basicButton___go-bX')
        if link_tag and link_tag.get('href'):
            link_str = link_tag.get('href')

        # URL de la Imagen
        img_tag = item.select_one('img.ProductCard-module__boxArt___-2vQY')
        if img_tag and img_tag.get('src'):
            image_url_str = img_tag.get('src')

        # Lógica de Precios
        price_container = item.select_one('div.ProductCard-module__priceGroup___bACzG')
        if price_container:
            original_price_span = price_container.select_one('span.Price-module__originalPrice___XNCxs')
            # El precio actual puede ser el normal o el de descuento
            # Usando r antes del string para evitar problemas de escape con \+
            current_price_span = price_container.select_one(r'span.ProductCard-module__price___cs1xr, span.Price-module__listedDiscountPrice___A-\+d5') 
            discount_tag_span = price_container.select_one('div.ProductCard-module__discountTag___OjGFy')

            if original_price_span and current_price_span: # Hay descuento
                original_price_text = original_price_span.text.strip()
                current_price_text = current_price_span.text.strip()
                
                old_price_num = clean_price_to_float(original_price_text)
                current_price_num = clean_price_to_float(current_price_text)
                
                if discount_tag_span:
                    discount_percentage_num = extract_discount_percentage(discount_tag_span.text.strip())

                # Formatear el texto de display
                aria_label_price_info = ""
                if link_tag and link_tag.get('aria-label'):
                    aria_label = link_tag.get('aria-label')
                    # Ejemplo aria-label: "Eyes: The Horror Game, Precio original: ARS$ 70,00; en oferta por ARS$ 56,00 "
                    match_aria = re.search(r"Precio original:\s*(ARS\$\s*[\d\.,]+);\s*en oferta por\s*(ARS\$\s*[\d\.,]+)", aria_label, re.IGNORECASE)
                    if match_aria:
                         price_text_display = f"Antes: {match_aria.group(1).strip()}, Ahora: {match_aria.group(2).strip()}"
                         if discount_percentage_num:
                             price_text_display += f" (-{discount_percentage_num}%)"
                    elif "ARS$" in aria_label: # Si no tiene el formato exacto pero tiene precio
                        price_text_display = aria_label.split(',', 1)[-1].strip() # Tomar la parte del precio
                    else: # Fallback
                        price_text_display = f"Antes: {original_price_text}, Ahora: {current_price_text}"
                else:
                    price_text_display = f"Antes: {original_price_text}, Ahora: {current_price_text}"


            elif current_price_span: # No hay descuento, solo precio actual
                current_price_text = current_price_span.text.strip()
                current_price_num = clean_price_to_float(current_price_text)
                price_text_display = current_price_text
            
            # Manejar "Gratis" e "Incluido con Game Pass" si no se capturaron arriba
            if current_price_num is None and (price_text_display == "Precio no disponible" or not "ARS$" in price_text_display):
                container_text_lower = price_container.text.lower()
                if "gratis" in container_text_lower:
                    price_text_display = "Gratis"
                    current_price_num = 0.0
                elif "incluido con" in container_text_lower or "game pass" in container_text_lower:
                    price_text_display = "Incluido con Game Pass"
                    current_price_num = None
        
        # Fallback si price_container no existe pero hay texto de "Gratis" o "Game Pass" en el item
        if price_text_display == "Precio no disponible" or (current_price_num is None and not "ARS$" in price_text_display and price_text_display != "Incluido con Game Pass"):
            item_text_lower = item.text.lower()
            if "gratis" in item_text_lower: # Buscar "gratis" en todo el item si no se encontró precio
                price_text_display = "Gratis"
                current_price_num = 0.0
            elif "incluido con game pass" in item_text_lower or "game pass" in item_text_lower:
                price_text_display = "Incluido con Game Pass"
                current_price_num = None

        if title_str == "Título no encontrado" and price_text_display == "Precio no disponible":
            # print(f"Item {item_index+1} completamente vacío, omitiendo.")
            continue

        # Comparar con datos previos si existen
        comparacion_precio = None
        precio_anterior_num = None
        # No hacer comparación de precios si el título es "Título no encontrado"
        if title_str != "Título no encontrado" and datos_previos and title_str in datos_previos and current_price_num is not None:
            juego_previo = datos_previos[title_str]
            if 'precio_num' in juego_previo and juego_previo['precio_num'] is not None:
                precio_prev = juego_previo['precio_num']
                comparacion_precio = comparar_precio(current_price_num, precio_prev)
                # Guardar el precio anterior si hubo un cambio
                if comparacion_precio == "increased" or comparacion_precio == "decreased":
                    precio_anterior_num = precio_prev

        games_data.append({
            'titulo': title_str,
            'link': link_str,
            'imagen_url': image_url_str,
            'precio_num': current_price_num,
            'precio_old_num': old_price_num,
            'precio_descuento_num': discount_percentage_num,
            'precio_texto': price_text_display,
            'precio_cambio': comparacion_precio,  # Propiedad que indica cambio en el precio
            'precio_anterior_num': precio_anterior_num  # Nueva propiedad que guarda el precio anterior cuando hubo un cambio
        })

    return games_data

if __name__ == "__main__":
    OUTPUT_FILENAME = "public/xbox_pc_games.json" # Nuevo nombre para no sobreescribir

    print("Iniciando scraper de Xbox PC Games (v2)...")
    
    # Cargar datos previos si existen
    datos_previos = cargar_datos_previos(OUTPUT_FILENAME)
    
    # Ejecutar scraping con datos previos
    juegos = scrape_xbox_games(datos_previos)

    if juegos:
        print(f"\n--- {len(juegos)} Juegos Encontrados ---")
        for i, juego in enumerate(juegos[:20]):
            print(f"{i+1}. Título: {juego['titulo']}")
            print(f"   Link: {juego['link']}")
            print(f"   Imagen: {juego['imagen_url']}")
            print(f"   Precio Num: {juego['precio_num']}")
            if juego['precio_old_num'] is not None:
                print(f"   Precio Viejo Num: {juego['precio_old_num']}")
            if juego['precio_descuento_num'] is not None:
                print(f"   Descuento %: {juego['precio_descuento_num']}")
            print(f"   Precio Texto: {juego['precio_texto']}")
            if juego['precio_cambio'] is not None:
                print(f"   Cambio de precio: {juego['precio_cambio']}\n")
            else:
                print(f"   Cambio de precio: null\n")

        if len(juegos) > 20:
            print(f"... y {len(juegos) - 20} más.")

        try:
            # Crear un objeto con la fecha actual y los juegos
            fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            datos_completos = {
                "fecha_creacion": fecha_actual,
                "juegos": juegos
            }
            
            with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                json.dump(datos_completos, f, ensure_ascii=False, indent=4)
            print(f"\nDatos guardados en {OUTPUT_FILENAME} con fecha: {fecha_actual}")
            
            # Preparar y enviar notificación de Telegram para juegos que bajaron de precio
            juegos_bajaron_precio = [j for j in juegos if j['precio_cambio'] == 'decreased']
            
            if juegos_bajaron_precio or DEBUG:
                # Construir el mensaje para Telegram
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
                
                # Enviar el mensaje a través de Telegram
                print("\nEnviando notificación a Telegram...")
                asyncio.run(enviar_mensaje_telegram(mensaje))
            else:
                print("\nNo se encontraron juegos que hayan bajado de precio. No se envía notificación.")
                
        except Exception as e:
            logger.error(f"Error al guardar los datos en JSON o al enviar notificación: {e}")
    else:
        logger.warning("No se pudieron obtener datos de los juegos o la lista está vacía.")