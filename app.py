import threading
import logging
from flask import Flask, request
from settings import TOKEN_SECRETO, URLS_TO_SCAN
from storage import Storage
from notifier import NtfyNotifier
from scraper import ProductScraper
from catalog_scraper import CatalogScraper

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(levelname)s] %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

db = Storage()
notifier = NtfyNotifier()
product_scraper = ProductScraper()

def procesar_scan():
  logger.info("Iniciando tarea de procesamiento de stock de URLs en segundo plano...")
  state = db.get_all_products()
  cambios_detectados = 0

  datos_actuales = product_scraper.scan_urls(URLS_TO_SCAN)

  for url, current_data in datos_actuales.items():
    title = current_data["title"]
    editorial = current_data["editorial"]
    current_stock = current_data["stock"]
    
    last_data = state.get(url, {})
    last_stock = last_data.get("stock")
    last_title = last_data.get("title", "Desconocido")
    last_editorial = last_data.get("editorial", "Desconocida")

    if title == "Página no encontrada" and last_title != "Desconocido":
      title = last_title
      editorial = last_editorial

    if last_stock is None:
      logger.info(f"Nuevo enlace rastreado: {title}")
      state[url] = {"title": title, "editorial": editorial, "stock": current_stock}
      
    elif current_stock != last_stock:
      logger.info(f"Cambio de stock detectado para '{last_title}': de {last_stock} ➔ a {current_stock}")
      notifier.send_stock_alert(last_title, last_editorial, last_stock, current_stock, url)
      state[url] = {"title": last_title, "editorial": last_editorial, "stock": current_stock}
      cambios_detectados += 1

  db.save_all_products(state)
  logger.info(f"Escaneo de stock completado. Cambios notificados: {cambios_detectados}")

def procesar_catalogo(editorial):
  logger.info(f"Iniciando tarea de procesamiento de catálogo ({editorial}) en segundo plano...")
  catalog_scraper = CatalogScraper(editorial_target=editorial)
  libros_actuales = catalog_scraper.scan_full_catalog()
  cambios = 0

  if libros_actuales:
    libros_anteriores = db.get_catalog(editorial)
    
    if not libros_anteriores:
      db.save_catalog(editorial, libros_actuales)
      logger.info(f"Catálogo inicial de {editorial} guardado.")
      return
        
    ids_actuales = set(libros_actuales.keys())
    ids_anteriores = set(libros_anteriores.keys())
    
    # 1. Libros completamente nuevos
    ids_nuevos = ids_actuales - ids_anteriores
    for id_nuevo in ids_nuevos:
      libro = libros_actuales[id_nuevo]
      titulo_alert = f"NUEVO LIBRO - {editorial}"
      mensaje = f"Título: {libro['titulo']}\nPrecio: {libro['precio']}\nStock: {libro.get('stock', 'N/A')}\nHandle: {libro.get('handle', 'N/A')}"
      notifier.send_catalog_alert(titulo_alert, mensaje)
      cambios += 1
        
    # 2. Libros que se mantienen (ACTUALIZACIÓN)
    ids_comunes = ids_actuales & ids_anteriores
    for id_comun in ids_comunes:
      libro_actual = libros_actuales[id_comun]
      libro_anterior = libros_anteriores[id_comun]
      
      precio_actual = libro_actual['precio']
      precio_anterior = libro_anterior['precio']
      
      stock_actual = libro_actual.get('stock', 'N/A')
      stock_anterior = libro_anterior.get('stock', 'N/A')
      
      cambios_detectados_lista = []
      if precio_actual != precio_anterior:
        cambios_detectados_lista.append(f"Precio: de {precio_anterior} ➔ a {precio_actual}")
      if stock_actual != stock_anterior:
        cambios_detectados_lista.append(f"Stock: de {stock_anterior} ➔ a {stock_actual}")
        
      if cambios_detectados_lista:
        titulo_alert = f"ACTUALIZACIÓN - {editorial}"
        mensaje_cambios = f"Título: {libro_actual['titulo']}\n" + "\n".join(cambios_detectados_lista)
        notifier.send_catalog_alert(titulo_alert, mensaje_cambios)
        cambios += 1

    # 3. Libros eliminados del catálogo
    ids_removidos = ids_anteriores - ids_actuales
    for id_removido in ids_removidos:
      libro = libros_anteriores[id_removido]
      handle = libro.get('handle')
      
      # Doble verificación delegada al scraper
      sigue_existiendo = catalog_scraper.verify_book_exists(handle)
      
      if sigue_existiendo:
        # Falso positivo: el buscador lo ignoró o le cambiaron el ISBN. 
        # Lo conservamos en nuestro diccionario actual para que no se borre de la DB.
        libros_actuales[id_removido] = libro
      else:
        # Eliminado real
        titulo_alert = f"ELIMINADO - {editorial}"
        mensaje_baja = f"El libro '{libro['titulo']}' ya no se encuentra en el catálogo."
        notifier.send_catalog_alert(titulo_alert, mensaje_baja)
        cambios += 1
        
    db.save_catalog(editorial, libros_actuales)
    
  logger.info(f"Escaneo de catálogo ({editorial}) completado. Cambios detectados: {cambios}")

@app.route('/')
def home():
  return "Servidor de monitoreo en línea activo."

@app.route('/ejecutar-scan')
def run_monitor():
  if request.args.get('token') != TOKEN_SECRETO:
    logger.warning("Intento de acceso denegado a /ejecutar-scan (Token inválido)")
    return "Acceso denegado.", 403

  hilo = threading.Thread(target=procesar_scan)
  hilo.start()
  
  return "Escaneo de stock iniciado en segundo plano.", 202

@app.route('/escanear-catalogo')
def scan_catalog():
  if request.args.get('token') != TOKEN_SECRETO:
    logger.warning("Intento de acceso denegado a /escanear-catalogo (Token inválido)")
    return "Acceso denegado.", 403

  editorial = "ALBA"
  hilo = threading.Thread(target=procesar_catalogo, args=(editorial,))
  hilo.start()

  return f"Escaneo de catálogo de {editorial} iniciado en segundo plano.", 202

if __name__ == '__main__':
  logger.info("Iniciando aplicación Flask...")
  app.run(host='0.0.0.0', port=5000)