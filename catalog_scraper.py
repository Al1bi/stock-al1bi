import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import html
import time
import re

# Configuración global de los logs (puedes ajustar el formato a tu gusto)
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(levelname)s] %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S'
)

class CatalogScraper:
  def __init__(self, editorial_target="ALBA"):
    # Instanciamos el logger para esta clase
    self.logger = logging.getLogger(__name__)
    
    self.editorial_target = editorial_target.upper()
    self.base_url = "https://libreriayachaywasi.com"
    self.search_url = f"{self.base_url}/search"
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    self.json_headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "Accept": "application/json"
    }

    self.session = requests.Session()

    retries = Retry(
      total=5,
      backoff_factor=2,
      status_forcelist=[429, 500, 502, 503, 504],
      allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    self.session.mount('http://', adapter)
    self.session.mount('https://', adapter)

  def scan_full_catalog(self, debug=False, max_debug_items=1) -> dict:
    if debug:
      self.logger.setLevel(logging.DEBUG)

    libros_totales = {}
    pagina = 1
    self.logger.info(f"Iniciando escaneo del catálogo para la editorial: {self.editorial_target}")

    while True:
      url = f"{self.search_url}?page={pagina}&q={self.editorial_target}"
      self.logger.info(f"Escaneando página {pagina}...")

      try:
        res = self.session.get(url, headers=self.headers, timeout=15)
        if res.status_code != 200:
          self.logger.warning(f"Status {res.status_code}. Deteniendo escaneo en página {pagina}.")
          break

        tree = html.fromstring(res.content)
        
        base_xpath = '/html/body/main/section/div/div[2]/div/div/ul/li'
        lista_libros = tree.xpath(base_xpath)
        
        if not lista_libros:
          self.logger.info(f"Fin del catálogo detectado en la página {pagina}.")
          break

        for idx, libro in enumerate(lista_libros):
          enlace_raw = libro.xpath('.//h3/a/@href')
          enlace = enlace_raw[0].strip() if enlace_raw else ""

          if not enlace:
            continue
          base_path = enlace.split('?')[0]
          
          json_url = f"{self.base_url}{base_path}.json"
          html_url = f"{self.base_url}{base_path}"

          try:
            res_json = self.session.get(json_url, headers=self.json_headers, timeout=15)
            if res_json.status_code == 200:
              data = res_json.json()
              product = data.get('product', {})
              
              titulo = product.get('title', '')
              editorial_texto = product.get('vendor', '').upper()
              handle = product.get('handle', '')
              
              variants = product.get('variants', [])
              barcode = ""
              precio = "Precio no visible"
              
              if variants:
                barcode = str(variants[0].get('barcode', '')).strip()
                precio = str(variants[0].get('price', 'Precio no visible')).strip()
                
              id_libro = barcode if barcode and barcode != "None" else f"sin-barcode-{handle}"

              stock = "Stock no disponible"
              try:
                time.sleep(1) 
                res_html = self.session.get(html_url, headers=self.headers, timeout=15)

                if res_html.status_code == 200:
                  tree_html = html.fromstring(res_html.content)
                 
                  stock_raw = tree_html.xpath('/html/body/main/section[1]/product-info/div/div/div[2]/section/text()')
                  
                  if not stock_raw or not "".join(stock_raw).strip():
                    stock_raw = tree_html.xpath('.//section[contains(@class, "product-info")]//text()')
                    
                  stock_str = " ".join([s.strip() for s in stock_raw if s.strip()])
                  if stock_str:
                     match_stock = re.search(r'(\d+)', stock_str)
                     if match_stock:
                        stock = match_stock.group(1)
                     else:
                        stock = stock_str[:50] 
                        
              except Exception as e_html:
                self.logger.error(f"Error procesando HTML para {html_url}: {e_html}")

              # --- Depuración con logs en nivel DEBUG ---
              if debug and pagina == 1 and idx < max_debug_items:
                self.logger.debug(
                  f"\n===== Item {idx} =====\n"
                  f"Título: {titulo}\n"
                  f"URL HTML: {html_url}\n"
                  f"URL JSON: {json_url}\n"
                  f"Handle: {handle}\n"
                  f"ID (Barcode): {id_libro}\n"
                  f"Editorial: '{editorial_texto}'\n"
                  f"Precio: {precio}\n"
                  f"Stock extraído: {stock}"
                )

              if editorial_texto and self.editorial_target in editorial_texto:
                libros_totales[id_libro] = {
                  "titulo": titulo,
                  "precio": precio,
                  "handle": handle,
                  "editorial": editorial_texto,
                  "stock": stock
                }
                
            time.sleep(1.5) 
            
          except Exception as e_json:
            self.logger.error(f"Error procesando JSON para {json_url}: {e_json}")

        pagina += 1
        time.sleep(2)

      except Exception as e:
        # exc_info=True imprime todo el rastreo del error en consola (Stack trace)
        self.logger.critical(f"Error crítico en página {pagina}: {e}", exc_info=True)
        break

    self.logger.info(f"Escaneo finalizado. Total de libros extraídos: {len(libros_totales)}")
    return libros_totales

  def verify_book_exists(self, handle: str) -> bool:
    """
    Hace una petición directa a la URL del producto para confirmar si sigue existiendo.
    Evita falsos positivos si el buscador interno de la tienda falla.
    """
    # Tiempo de espera breve solicitado
    time.sleep(2)
    
    # Reconstruimos la URL directa usando el handle
    url_json = f"{self.base_url}/products/{handle}.json"
    self.logger.info(f"Doble verificación: Comprobando existencia directa de {handle}...")
    
    try:
      res = self.session.get(url_json, headers=self.json_headers, timeout=15)
      
      # Si devuelve 200, el libro sigue existiendo.
      if res.status_code == 200:
        self.logger.info(f"[FALSO ELIMINADO] El libro '{handle}' sigue activo en la tienda.")
        return True
      else:
        self.logger.info(f"[ELIMINADO CONFIRMADO] El libro '{handle}' dio status {res.status_code}.")
        return False
        
    except Exception as e:
      self.logger.error(f"Error en doble verificación para {handle}: {e}")
      # Si hay error de red, asumimos que existe para no borrarlo por accidente
      return True 
