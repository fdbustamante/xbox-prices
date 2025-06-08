"""
Módulo de scraping para extraer los precios de juegos de Xbox.
"""

# =====================
# Imports
# =====================
import os
import re
import time
import asyncio
import logging
from pathlib import Path
from dataclasses import dataclass, field
from functools import wraps, lru_cache
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar, Union, cast
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)
from bs4 import BeautifulSoup, Tag

from scrap.utils import clean_price_to_float, extract_discount_percentage, comparar_precio
from scrap.config import logger, MAX_JUEGOS, MAX_RETRY_ATTEMPTS, REQUEST_TIMEOUT

# =====================
# Constantes de Configuración
# =====================
URL_XBOX_TIENDA = "https://www.xbox.com/es-AR/games/all-games/pc?PlayWith=PC&xr=shellnav&orderby=Title+Asc"
SELECTOR_CARD_WRAPPER = "div.ProductCard-module__cardWrapper___6Ls86"
SELECTOR_TITULO = "span.ProductCard-module__title___nHGIp"
SELECTOR_ENLACE = "a.commonStyles-module__basicButton___go-bX"
SELECTOR_IMAGEN = "img.ProductCard-module__boxArt___-2vQY"
SELECTOR_PRECIO_CONTAINER = "div.ProductCard-module__priceGroup___bACzG"
SELECTOR_PRECIO_ORIGINAL = "span.Price-module__originalPrice___XNCxs"
SELECTOR_PRECIO_ACTUAL = r"span.ProductCard-module__price___cs1xr, span.Price-module__listedDiscountPrice___A-\+d5"
SELECTOR_DESCUENTO_TAG = "div.ProductCard-module__discountTag___OjGFy"
SELECTOR_GRID_CONTAINER = "ol.SearchProductGrid-module__container___jew-i"
XPATH_BOTON_CARGAR_MAS = "//button[.//div[contains(text(),'Cargar más')]]"
XPATH_BOTON_COOKIES = "//button[@id='onetrust-accept-btn-handler']"
MAX_FALLOS_CONSECUTIVOS = 3

# =====================
# Tipos y Decoradores
# =====================
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class GameData:
    """Representación de un juego de Xbox con sus datos."""
    titulo: str = "Título no encontrado"
    link: str = "Enlace no encontrado"
    imagen_url: str = "Imagen no encontrada"
    precio_num: Optional[float] = None
    precio_old_num: Optional[float] = None
    precio_descuento_num: Optional[float] = None
    precio_texto: str = "Precio no disponible"
    precio_cambio: Optional[str] = None
    precio_anterior_num: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a un diccionario."""
        return {k: v for k, v in self.__dict__.items()}


def retry(max_attempts: int = MAX_RETRY_ATTEMPTS, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)) -> Callable[[F], F]:
    """
    Decorador para reintentar una función en caso de excepción.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            current_delay = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Función {func.__name__} falló después de {max_attempts} intentos: {e}")
                        raise
                    logger.warning(f"Intento {attempts} fallido en {func.__name__}: {e}. Reintentando en {current_delay:.2f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
        return cast(F, wrapper)
    return decorator


@contextmanager
def create_driver() -> Iterator[webdriver.Chrome]:
    """
    Context manager para la creación y cierre del driver de Selenium.
    """
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
    
    logger.info("Iniciando el navegador...")
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        yield driver
    except Exception as e:
        logger.error(f"Error al iniciar ChromeDriver: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador cerrado correctamente.")


class XboxScraper:
    """
    Clase principal para manejar el scraping de juegos de Xbox.
    Se encarga de cargar la página, extraer los datos y comparar precios.
    """
    
    def __init__(self, url: str = URL_XBOX_TIENDA, max_juegos: int = MAX_JUEGOS):
        self.url = url
        self.max_juegos = max_juegos
        self.juegos_sin_info = 0  # Contador para juegos sin información completa

    @retry(max_attempts=MAX_RETRY_ATTEMPTS, delay=5.0)
    def cargar_pagina_inicial(self, driver: webdriver.Chrome) -> bool:
        """
        Carga la página inicial y configura la navegación.
        """
        logger.info(f"Cargando página: {self.url}")
        driver.get(self.url)
        WebDriverWait(driver, REQUEST_TIMEOUT/2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        # Intentar aceptar cookies si aparece el banner
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_BOTON_COOKIES))
            ).click()
            logger.info("Banner de cookies aceptado.")
        except TimeoutException:
            logger.info("No se encontró el banner de cookies o ya fue aceptado.")
        except Exception as e:
            logger.warning(f"Error al aceptar cookies: {e}")
        # Esperar a que cargue la grilla de juegos
        try:
            WebDriverWait(driver, REQUEST_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_GRID_CONTAINER))
            )
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER))
            )
            logger.info("Grilla de juegos cargada correctamente.")
            return True
        except TimeoutException:
            logger.error("Timeout: Contenedor de grilla o primer item no encontrado.")
            from scrap.config import HTML_DEBUG_DIR, get_formatted_datetime
            timestamp = get_formatted_datetime("%Y%m%d_%H%M%S")
            error_html_path = HTML_DEBUG_DIR / f"xbox_page_source_error_{timestamp}.html"
            error_html_path.write_text(driver.page_source, encoding="utf-8")
            logger.error(f"HTML guardado en {error_html_path}")
            return False

    def scrape_xbox_games(self, datos_previos: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Realiza el scraping de los juegos de PC en la tienda de Xbox.
        """
        self.juegos_sin_info = 0
        try:
            with create_driver() as driver:
                if not self.cargar_pagina_inicial(driver):
                    logger.error("No se pudo cargar la página inicial.")
                    return []
                games_data = self._cargar_mas_juegos(driver)
                if datos_previos:
                    logger.info(f"Comparando con datos previos... (formato: {'con clave juegos' if 'juegos' in datos_previos else 'diccionario por título'})")
                    self._comparar_con_datos_previos_bulk(games_data, datos_previos)
                    self._debug_comparacion_precios(games_data, datos_previos)
                else:
                    logger.info("No hay datos previos para comparar")
                if self.juegos_sin_info > 0:
                    logger.info(f"No se pudo obtener información completa de {self.juegos_sin_info} juegos de un total de {len(games_data)}.")
                return [game.to_dict() for game in games_data]
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}", exc_info=True)
            return []

    def _cargar_mas_juegos(self, driver: webdriver.Chrome) -> List[GameData]:
        """
        Hace clic en 'Cargar más' hasta alcanzar el máximo de juegos o agotar los intentos.
        """
        consecutive_failures = 0
        last_item_count = 0
        adaptive_wait_time = 1.5
        while consecutive_failures < MAX_FALLOS_CONSECUTIVOS:
            try:
                current_items_count = len(driver.find_elements(By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER))
                logger.info(f"Items actualmente cargados: {current_items_count}")
            except StaleElementReferenceException:
                time.sleep(adaptive_wait_time)
                continue
            if current_items_count >= self.max_juegos:
                logger.info(f"Límite de {self.max_juegos} juegos alcanzado. Deteniendo carga.")
                break
            if current_items_count > 0 and current_items_count == last_item_count:
                consecutive_failures += 1
                adaptive_wait_time *= 1.5
            else:
                consecutive_failures = 0
                adaptive_wait_time = max(1.5, adaptive_wait_time * 0.8)
            last_item_count = current_items_count
            try:
                load_more_button = self._encontrar_boton_cargar_mas(driver)
                if load_more_button:
                    self._hacer_click_seguro(driver, load_more_button)
                    logger.info("Botón 'Cargar más' presionado.")
                    self._esperar_nuevos_elementos(driver, last_item_count)
                else:
                    logger.info("Botón 'Cargar más' no encontrado. Posiblemente se cargaron todos los juegos.")
                    consecutive_failures += 1
            except TimeoutException:
                logger.info("Timeout al buscar/presionar 'Cargar más'.")
                consecutive_failures += 1
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(adaptive_wait_time)
            except Exception as e:
                logger.error(f"Error en bucle 'Cargar más': {e}")
                consecutive_failures += 1
                time.sleep(adaptive_wait_time)
            if consecutive_failures >= MAX_FALLOS_CONSECUTIVOS:
                break
        # Guardar el HTML para depuración
        page_source = driver.page_source
        from scrap.config import HTML_DEBUG_DIR, get_formatted_datetime
        timestamp = get_formatted_datetime("%Y%m%d_%H%M%S")
        html_path = HTML_DEBUG_DIR / f"xbox_page_source_{timestamp}.html"
        html_path.write_text(page_source if page_source else "", encoding="utf-8")
        Path("xbox_page_source.html").write_text(page_source if page_source else "", encoding="utf-8")
        logger.info(f"HTML guardado en {html_path}")
        return self._procesar_datos_juegos(page_source)

    def _encontrar_boton_cargar_mas(self, driver: webdriver.Chrome) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        Encuentra el botón 'Cargar más' y hace scroll hacia él.
        """
        try:
            load_more_button = WebDriverWait(driver, REQUEST_TIMEOUT/3).until(
                EC.presence_of_element_located((By.XPATH, XPATH_BOTON_CARGAR_MAS))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'nearest'});", 
                load_more_button
            )
            return WebDriverWait(driver, REQUEST_TIMEOUT/6).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_BOTON_CARGAR_MAS))
            )
        except (TimeoutException, NoSuchElementException):
            return None

    def _hacer_click_seguro(self, driver: webdriver.Chrome, elemento: webdriver.remote.webelement.WebElement) -> None:
        """
        Intenta hacer click en un elemento de forma segura.
        """
        try:
            elemento.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", elemento)

    def _esperar_nuevos_elementos(self, driver: webdriver.Chrome, ultimo_conteo: int) -> None:
        """
        Espera a que se carguen nuevos elementos tras hacer clic en 'Cargar más'.
        """
        try:
            WebDriverWait(driver, REQUEST_TIMEOUT / 2).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER)) > ultimo_conteo
            )
            logger.info(f"Nuevos items cargados. Total ahora: {len(driver.find_elements(By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER))}")
            time.sleep(1)
        except TimeoutException:
            logger.warning("No se detectaron nuevos elementos después de hacer clic en 'Cargar más'")

    def _procesar_datos_juegos(self, page_source: str) -> List[GameData]:
        """
        Procesa el HTML de la página para extraer información de los juegos.
        Utiliza ThreadPoolExecutor para procesamiento paralelo.
        """
        soup = BeautifulSoup(page_source, 'html.parser')
        juegos_procesados = []
        items = soup.select(SELECTOR_CARD_WRAPPER)
        logger.info(f"Procesando {len(items)} juegos encontrados en el HTML")
        with ThreadPoolExecutor(max_workers=min(10, os.cpu_count() * 2)) as executor:
            futures = {executor.submit(self._extraer_datos_juego, item): item for item in items}
            for future in as_completed(futures):
                try:
                    game_data = future.result()
                    if game_data:
                        juegos_procesados.append(game_data)
                except Exception as exc:
                    item = futures[future]
                    logger.error(f"Error procesando juego: {exc}", exc_info=True)
                    self.juegos_sin_info += 1
        logger.info(f"Total de juegos procesados: {len(juegos_procesados)} | Juegos sin información completa: {self.juegos_sin_info}")
        return juegos_procesados

    # =====================
    # Métodos de extracción y utilidades privadas
    # =====================
    PRECIO_PATTERN = re.compile(r"Precio original:\s*(ARS\$\s*[\d\.,]+);\s*en oferta por\s*(ARS\$\s*[\d\.,]+)", re.IGNORECASE)

    @staticmethod
    @lru_cache(maxsize=32)
    def _extract_element_text(element, selector):
        """
        Extrae el texto de un elemento usando un selector CSS. Usa caché para mejorar el rendimiento.
        """
        if not element:
            return None
        selected = element.select_one(selector)
        return selected.text.strip() if selected else None

    def _extraer_datos_juego(self, item: Tag) -> GameData:
        """
        Extrae los datos de un elemento de juego individual.
        """
        game = GameData()
        titulo = self._extract_element_text(item, SELECTOR_TITULO)
        if titulo:
            game.titulo = titulo
        link_tag = item.select_one(SELECTOR_ENLACE)
        if link_tag and link_tag.get('href'):
            game.link = link_tag.get('href')
        img_tag = item.select_one(SELECTOR_IMAGEN)
        if img_tag and img_tag.get('src'):
            game.imagen_url = img_tag.get('src')
        self._extraer_info_precios(item, game, link_tag)
        if game.precio_texto == "Precio no disponible" or game.titulo == "Título no encontrado":
            self.juegos_sin_info += 1
        return game

    def _extraer_info_precios(self, item: Tag, game: GameData, link_tag: Optional[Tag] = None) -> None:
        """
        Extrae la información de precios de un item de juego.
        """
        price_container = item.select_one(SELECTOR_PRECIO_CONTAINER)
        if not price_container:
            return
        original_price_span = price_container.select_one(SELECTOR_PRECIO_ORIGINAL)
        current_price_span = price_container.select_one(SELECTOR_PRECIO_ACTUAL)
        discount_tag_span = price_container.select_one(SELECTOR_DESCUENTO_TAG)
        if original_price_span and current_price_span:
            self._procesar_precio_con_descuento(
                game, original_price_span, current_price_span, discount_tag_span, link_tag
            )
        elif current_price_span:
            current_price_text = current_price_span.text.strip()
            game.precio_num = clean_price_to_float(current_price_text)
            game.precio_texto = current_price_text
        self._detectar_precios_especiales(game, price_container)
        if (game.precio_texto == "Precio no disponible" or 
            (game.precio_num is None and "ARS$" not in game.precio_texto and 
             game.precio_texto != "Incluido con Game Pass")):
            self._detectar_precios_en_texto_completo(game, item)

    def _procesar_precio_con_descuento(self, 
                                      game: GameData, 
                                      original_price_span: Tag, 
                                      current_price_span: Tag, 
                                      discount_tag_span: Optional[Tag], 
                                      link_tag: Optional[Tag]) -> None:
        """
        Procesa los precios cuando hay un descuento aplicado.
        """
        original_price_text = original_price_span.text.strip()
        current_price_text = current_price_span.text.strip()
        game.precio_old_num = clean_price_to_float(original_price_text)
        game.precio_num = clean_price_to_float(current_price_text)
        if discount_tag_span:
            game.precio_descuento_num = extract_discount_percentage(discount_tag_span.text.strip())
        if link_tag and link_tag.get('aria-label'):
            aria_label = link_tag.get('aria-label')
            match_aria = self.PRECIO_PATTERN.search(aria_label)
            if match_aria:
                game.precio_texto = f"Antes: {match_aria.group(1).strip()}, Ahora: {match_aria.group(2).strip()}"
                if game.precio_descuento_num:
                    game.precio_texto += f" (-{game.precio_descuento_num}%)"
            elif "ARS$" in aria_label:
                game.precio_texto = aria_label.split(',', 1)[-1].strip()
            else:
                game.precio_texto = f"Antes: {original_price_text}, Ahora: {current_price_text}"
        else:
            game.precio_texto = f"Antes: {original_price_text}, Ahora: {current_price_text}"

    def _detectar_precios_especiales(self, game: GameData, price_container: Tag) -> None:
        """
        Detecta precios especiales como 'Gratis' o 'Game Pass'.
        """
        if game.precio_num is None and (game.precio_texto == "Precio no disponible" or "ARS$" not in game.precio_texto):
            container_text_lower = price_container.text.lower()
            if "gratis" in container_text_lower:
                game.precio_texto = "Gratis"
                game.precio_num = 0.0
            elif "incluido con" in container_text_lower or "game pass" in container_text_lower:
                game.precio_texto = "Incluido con Game Pass"

    def _detectar_precios_en_texto_completo(self, game: GameData, item: Tag) -> None:
        """
        Busca precios en todo el texto del elemento cuando no se detectó en el contenedor principal.
        """
        item_text_lower = item.text.lower()
        if "gratis" in item_text_lower:
            game.precio_texto = "Gratis"
            game.precio_num = 0.0
        elif "incluido con game pass" in item_text_lower or "game pass" in item_text_lower:
            game.precio_texto = "Incluido con Game Pass"

    def _comparar_con_datos_previos_bulk(self, 
                                        games_data: List[GameData], 
                                        datos_previos: Dict[str, Any]) -> None:
        """
        Compara los datos de múltiples juegos con los datos previos en paralelo.
        """
        if not datos_previos:
            logger.info("No hay datos previos para comparar precios.")
            return
        if "juegos" in datos_previos and isinstance(datos_previos["juegos"], list):
            juegos_prev = datos_previos.get("juegos", [])
            juegos_prev_dict = {juego.get("titulo", ""): juego for juego in juegos_prev}
            logger.info(f"Comparando precios con datos previos (formato antiguo) de {len(juegos_prev)} juegos...")
        else:
            juegos_prev_dict = datos_previos
            logger.info(f"Comparando precios con datos previos de {len(juegos_prev_dict)} juegos...")
        juegos_con_titulo = [game for game in games_data if game.titulo != "Título no encontrado"]
        if len(juegos_con_titulo) < len(games_data):
            logger.info(f"Se omitieron {len(games_data) - len(juegos_con_titulo)} juegos sin título en la comparación de precios.")
        with ThreadPoolExecutor(max_workers=min(10, os.cpu_count() * 2)) as executor:
            futures_to_games = {
                executor.submit(
                    self._comparar_juego_individual, 
                    game, 
                    juegos_prev_dict.get(game.titulo)
                ): game for game in juegos_con_titulo
            }
            for future in as_completed(futures_to_games):
                try:
                    future.result()
                except Exception as exc:
                    game = futures_to_games[future]
                    logger.error(f"Error comparando juego '{game.titulo}': {exc}")

    def _comparar_juego_individual(self, game: GameData, juego_previo: Optional[Dict[str, Any]]) -> None:
        """
        Compara un juego individual con los datos previos.
        """
        if game.titulo == "Título no encontrado":
            logger.debug("Omitiendo comparación para juego sin título")
            return
        if not juego_previo:
            logger.debug(f"Juego '{game.titulo}' nuevo, no hay datos previos para comparar")
            return
        precio_anterior = juego_previo.get("precio_num")
        precio_actual = game.precio_num
        if precio_anterior is not None and precio_actual is not None:
            game.precio_anterior_num = precio_anterior
            game.precio_cambio = comparar_precio(precio_actual, precio_anterior)
            logger.debug(f"Comparando precio del juego '{game.titulo}': anterior={precio_anterior}, actual={precio_actual}, cambio={game.precio_cambio}")

    def _debug_comparacion_precios(self, games_data: List[GameData], datos_previos: Dict[str, Any]) -> None:
        """
        Método de diagnóstico para depurar problemas con la comparación de precios.
        """
        if not datos_previos:
            logger.debug("No hay datos previos para depurar comparación")
            return
        total_juegos = len(games_data)
        juegos_con_datos_previos = 0
        juegos_con_cambio_precio = 0
        juegos_sin_titulo = sum(1 for game in games_data if game.titulo == "Título no encontrado")
        if juegos_sin_titulo > 0:
            logger.info(f"Diagnóstico: {juegos_sin_titulo} juegos sin título detectados (serán omitidos en la comparación)")
        tiene_clave_juegos = "juegos" in datos_previos and isinstance(datos_previos["juegos"], list)
        if tiene_clave_juegos:
            formato = "antiguo (con clave 'juegos')"
            juegos_previos_count = len(datos_previos["juegos"])
        else:
            formato = "nuevo (diccionario por título)"
            juegos_previos_count = len(datos_previos)
        for game in games_data[:10]:
            titulo = game.titulo
            encontrado = False
            if tiene_clave_juegos:
                for juego in datos_previos["juegos"]:
                    if juego.get("titulo") == titulo:
                        encontrado = True
                        break
            else:
                encontrado = titulo in datos_previos
            if encontrado:
                juegos_con_datos_previos += 1
                if game.precio_cambio:
                    juegos_con_cambio_precio += 1
        logger.info(f"Diagnóstico de comparación: formato {formato}, {juegos_previos_count} juegos previos, "
                    f"{juegos_con_datos_previos}/10 tienen datos previos, "
                    f"{juegos_con_cambio_precio}/10 tienen cambio de precio detectado")


@lru_cache(maxsize=1)
def get_scraper(url: str = URL_XBOX_TIENDA, max_juegos: int = MAX_JUEGOS) -> XboxScraper:
    """
    Obtiene una instancia única del scraper (patrón Singleton con cache).
    """
    return XboxScraper(url, max_juegos)


def scrape_xbox_games(datos_previos: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Función principal de scraping para mantener compatibilidad con código existente.
    """
    scraper = get_scraper()
    return scraper.scrape_xbox_games(datos_previos)
