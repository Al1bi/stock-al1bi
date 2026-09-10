import lxml.html
import requests
import logging
import time

TITLE_XPATH = "/html/body/main/section[1]/product-info/div/div/div[2]/section/div[1]/h1"
EDITORIAL_XPATH = "/html/body/main/section[1]/product-info/div/div/div[2]/section/p"
STOCK_XPATH = "/html/body/main/section[1]/product-info/div/div/div[2]/section/text()"

class ProductScraper:
  def __init__(self):
    self.logger = logging.getLogger(__name__)
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      "Accept-Language": "es-ES,es;q=0.9",
    }

  def extract_text(self, tree, xpath_query, default="No encontrado"):
    """Función auxiliar para extraer texto de un XPath de forma segura."""
    elements = tree.xpath(xpath_query)
    
    if not elements:
      return default

    if isinstance(elements[0], str):
      raw_text = " ".join(str(t) for t in elements)
      clean_text = " ".join(raw_text.split())
      return clean_text if clean_text else default

    node = elements[0]
    text = node.text_content() if hasattr(node, "text_content") else str(node)
    return " ".join(text.split()) if text.strip() else default

  def get_product_data(self, url: str) -> tuple[str, str, str]:
    """Descarga la página y extrae Título, Editorial y Stock."""
    try:
      response = requests.get(url, headers=self.headers, timeout=15)
      
      if response.status_code == 404:
        return "Página no encontrada", "Desconocida", "Eliminado de la tienda (404)"
        
      response.raise_for_status()
      tree = lxml.html.fromstring(response.content)

      title = self.extract_text(tree, TITLE_XPATH, default="Título desconocido")
      editorial = self.extract_text(tree, EDITORIAL_XPATH, default="Editorial desconocida")
      stock = self.extract_text(tree, STOCK_XPATH, default="Agotado / No visible")

      return title, editorial, stock

    except Exception as e:
      self.logger.error(f"Error procesando URL {url}: {e}")
      return "Error", "Error", f"Fallo de conexión"

  def scan_urls(self, urls: list) -> dict:
    """Escanea una lista de URLs y devuelve un diccionario con los resultados."""
    self.logger.info(f"Iniciando escaneo de {len(urls)} URLs específicas.")
    resultados = {}
    
    for url in urls:
      self.logger.info(f"Extrayendo datos de: {url}")
      time.sleep(1.5)  # Retraso para no saturar el servidor
      title, editorial, stock = self.get_product_data(url)
      
      resultados[url] = {
        "title": title,
        "editorial": editorial,
        "stock": stock
      }
      
    self.logger.info("Escaneo de URLs específicas finalizado.")
    return resultados