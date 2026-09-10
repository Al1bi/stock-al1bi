from flask import Flask, request
from settings import TOKEN_SECRETO, URLS_TO_SCAN
from storage import Storage
from notifier import NtfyNotifier
from scraper import ProductScraper
from catalog_scraper import CatalogScraper

app = Flask(__name__)

db = Storage()
notifier = NtfyNotifier()
product_scraper = ProductScraper()

@app.route('/')
def home():
  return "Servidor de monitoreo en línea activo."

@app.route('/ejecutar-scan')
def run_monitor():
    if request.args.get('token') != TOKEN_SECRETO:
        return "Acceso denegado.", 403

    state = db.get_all_products()
    cambios_detectados = 0

    for url in URLS_TO_SCAN:
      title, editorial, current_stock = product_scraper.get_product_data(url)
      last_data = state.get(url, {})
      
      last_stock = last_data.get("stock")
      last_title = last_data.get("title", "Desconocido")
      last_editorial = last_data.get("editorial", "Desconocida")

      if title == "Página no encontrada" and last_title != "Desconocido":
        title = last_title
        editorial = last_editorial

      if last_stock is None:
        state[url] = {"title": title, "editorial": editorial, "stock": current_stock}
      elif current_stock != last_stock:
        notifier.send_stock_alert(last_title, last_editorial, last_stock, current_stock, url)
        state[url] = {"title": last_title, "editorial": last_editorial, "stock": current_stock}
        cambios_detectados += 1

    db.save_all_products(state) 
    return f"Escaneo de stock completado. Cambios: {cambios_detectados}", 200


@app.route('/escanear-catalogo')
def scan_catalog():
  if request.args.get('token') != TOKEN_SECRETO:
    return "Acceso denegado.", 403

  editorial = "ALBA"
  catalog_scraper = CatalogScraper(editorial_target=editorial)
  
  libros_actuales = catalog_scraper.scan_full_catalog()
  cambios = 0

  if libros_actuales:
    libros_anteriores = db.get_catalog(editorial)
    
    if not libros_anteriores:
      db.save_catalog(editorial, libros_actuales)
      return f"Catálogo inicial de {editorial} guardado.", 200
        
    ids_actuales = set(libros_actuales.keys())
    ids_anteriores = set(libros_anteriores.keys())
    
    # 1. Libros completamente nuevos (NUEVO)
    ids_nuevos = ids_actuales - ids_anteriores
    for id_nuevo in ids_nuevos:
      libro = libros_actuales[id_nuevo]
      titulo_alert = f"NUEVO LIBRO - {editorial}"
      mensaje = f"Título: {libro['titulo']}\nPrecio: {libro['precio']}\nStock: {libro.get('stock', 'N/A')}\nHandle: {libro.get('handle', 'N/A')}"
      notifier.send_catalog_alert(titulo_alert, mensaje)
      cambios += 1
        
    # 2. Libros que se mantienen, PERO cambiaron de precio o stock (ACTUALIZACIÓN)
    ids_comunes = ids_actuales & ids_anteriores
    for id_comun in ids_comunes:
      libro_actual = libros_actuales[id_comun]
      libro_anterior = libros_anteriores[id_comun]
      
      precio_actual = libro_actual['precio']
      precio_anterior = libro_anterior['precio']
      
      stock_actual = libro_actual.get('stock', 'N/A')
      stock_anterior = libro_anterior.get('stock', 'N/A')
      
      cambios_detectados = []
      if precio_actual != precio_anterior:
        cambios_detectados.append(f"Precio: de {precio_anterior} ➔ a {precio_actual}")
      if stock_actual != stock_anterior:
        cambios_detectados.append(f"Stock: de {stock_anterior} ➔ a {stock_actual}")
        
      if cambios_detectados:
        titulo_alert = f"ACTUALIZACIÓN - {editorial}"
        mensaje_cambios = f"Título: {libro_actual['titulo']}\n" + "\n".join(cambios_detectados)
        notifier.send_catalog_alert(titulo_alert, mensaje_cambios)
        cambios += 1

    # 3. Libros que desaparecieron del catálogo (ELIMINADO)
    ids_removidos = ids_anteriores - ids_actuales
    for id_removido in ids_removidos:
      libro = libros_anteriores[id_removido]
      titulo_alert = f"ELIMINADO - {editorial}"
      mensaje_baja = f"El libro '{libro['titulo']}' ya no se encuentra en el catálogo."
      notifier.send_catalog_alert(titulo_alert, mensaje_baja)
      cambios += 1
        
    db.save_catalog(editorial, libros_actuales)

  return f"Escaneo de catálogo completado. Cambios detectados: {cambios}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)