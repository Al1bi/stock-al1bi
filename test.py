# test_check.py
from catalog_scraper import CatalogScraper
from storage import Storage

print("1. Probando extracción de catálogo (ID, Título y Precio)...")
scraper = CatalogScraper("ALBA")
libros_actuales = scraper.scan_full_catalog()

print(f"\nTotal libros encontrados de ALBA: {len(libros_actuales)}")

if libros_actuales:
  print("\nMuestra de los primeros 3 libros detectados:")
  # Transformamos el diccionario en una lista para poder ver solo los primeros 3
  muestra = list(libros_actuales.items())[:3] 
  
  for id_libro, datos in muestra:
    print(f"🔸 ID: {id_libro}")
    print(f"   Título: {datos['titulo']}")
    print(f"   Precio: {datos['precio']}\n")

print("2. Probando guardado en Upstash...")
db = Storage()

# Guardamos el diccionario completo en la base de datos
db.save_catalog("ALBA", libros_actuales)

# Lo volvemos a leer para verificar que se guardó bien
libros_recuperados = db.get_catalog("ALBA")

print(f"Total libros recuperados desde Upstash: {len(libros_recuperados)}")

if len(libros_actuales) == len(libros_recuperados):
  print("\n✅ ¡ÉXITO! El scraper y la base de datos funcionan a la perfección.")
else:
  print("\n❌ Hubo una diferencia entre lo escaneado y lo guardado.")