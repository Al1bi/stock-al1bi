import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import html
import time
import re

class CatalogScraper:
  def __init__(self, editorial_target="ALBA"):
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
    libros_totales = {}
    pagina = 1

    while True:
      url = f"{self.search_url}?page={pagina}&q={self.editorial_target}"
      print(f"Escaneando página {pagina}...")

      try:
        res = self.session.get(url, headers=self.headers, timeout=15)
        if res.status_code != 200:
          print(f"Status {res.status_code}. Deteniendo.")
          break

        tree = html.fromstring(res.content)
        
        base_xpath = '/html/body/main/section/div/div[2]/div/div/ul/li'
        lista_libros = tree.xpath(base_xpath)
        
        if not lista_libros:
          print(f"Fin del catálogo detectado en la página {pagina}.")
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
                  
                  # Si no lo encuentra con el estricto, buscamos un elemento que comience con 'Cantidad' o que contenga la info
                  if not stock_raw or not "".join(stock_raw).strip():
                    stock_raw = tree_html.xpath('.//section[contains(@class, "product-info")]//text()') # Fallback temporal
                    
                  stock_str = " ".join([s.strip() for s in stock_raw if s.strip()])
                  if stock_str:
                     match_stock = re.search(r'(\d+)', stock_str)
                     if match_stock:
                        stock = match_stock.group(1)
                     else:
                        stock = stock_str[:50] 
                        
              except Exception as e_html:
                print(f"Error procesando HTML para {html_url}: {e_html}")

              # --- Depuración ---
              if debug and pagina == 1 and idx < max_debug_items:
                print(f"\n===== Item {idx} =====")
                print(f"Título: {titulo}")
                print(f"URL HTML: {html_url}")
                print(f"URL JSON: {json_url}")
                print(f"Handle: {handle}")
                print(f"ID (Barcode): {id_libro}")
                print(f"Editorial: '{editorial_texto}'")
                print(f"Precio: {precio}")
                print(f"Stock extraído: {stock}")

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
            print(f"Error procesando JSON para {json_url}: {e_json}")

        pagina += 1
        time.sleep(2)

      except Exception as e:
        print(f"Error crítico en página {pagina}: {e}")
        break

    return libros_totales