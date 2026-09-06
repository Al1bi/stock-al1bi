import requests
from lxml import html
import time
import re

class CatalogScraper:
  def __init__(self, editorial_target="ALBA"):
    self.editorial_target = editorial_target.upper()
    self.base_url = "https://libreriayachaywasi.com/search"
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

  def scan_full_catalog(self, debug=False, max_debug_items=1) -> dict:
    libros_totales = {}
    pagina = 1

    while True:
      url = f"{self.base_url}?page={pagina}&q={self.editorial_target}"
      print(f"Escaneando página {pagina}...")

      try:
        res = requests.get(url, headers=self.headers, timeout=15)
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
          
          titulo_raw = libro.xpath('./div/div/div[2]/div[1]/h3/a/text()')
          titulo_limpio = " ".join([t.strip() for t in titulo_raw if t.strip()])
          
          enlace_raw = libro.xpath('./div/div/div[2]/div[1]/h3/a/@href')
          enlace = enlace_raw[0].strip() if enlace_raw else ""

          id_raw = libro.xpath('./div/div/div[2]/div[1]/h3/@id')
          id_libro = ""
          
          if id_raw:
            id_attr = id_raw[0]
            if '--' in id_attr:
              id_libro = id_attr.split('--')[-1].strip()
            else:
              id_libro = id_attr.strip()
              
          if not id_libro and enlace:
            match = re.search(r'/products/([^/?#]+)', enlace)
            if match:
              id_libro = match.group(1)
              
          if not id_libro:
            id_libro = f"sin-id-{titulo_limpio[:15].replace(' ', '-')}"

          # --- Editorial ---
          editorial_raw = libro.xpath('./div/div/div[2]/div[1]/div/div[1]//text()')
          editorial_texto = " ".join([e.strip() for e in editorial_raw if e.strip()]).upper()

          # --- Precio ---
          precio_raw = libro.xpath('./div/div/div[2]/div[1]/div/div[2]/div/div[1]/span[2]//text()')
          if precio_raw:
            precio_limpio = " ".join([p.strip() for p in precio_raw if p.strip()])
          else:
            precio_limpio = "Precio no visible"

          # --- Depuración ---
          if debug and pagina == 1 and idx < max_debug_items:
            print(f"\n===== Item {idx} =====")
            print(f"Título: {titulo_limpio}")
            print(f"Enlace: {enlace}")
            print(f"ID: {id_libro}")
            print(f"Editorial: '{editorial_texto}'")
            print(f"Precio: {precio_limpio}")

          # --- Filtrar ---
          if editorial_texto and self.editorial_target in editorial_texto:
            libros_totales[id_libro] = {
              "titulo": titulo_limpio,
              "precio": precio_limpio
            }

        pagina += 1
        time.sleep(1)

      except Exception as e:
        print(f"Error crítico en página {pagina}: {e}")
        break

    return libros_totales