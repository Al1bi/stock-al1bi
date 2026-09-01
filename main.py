import json
import os
from notifier import NtfyNotifier
from scraper import ProductScraper

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"

def load_json(path, default):
  if os.path.exists(path):
    try:
      with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    except json.JSONDecodeError:
      return default
  return default

def save_json(path, data):
  with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

def run_monitor():
  config = load_json(CONFIG_FILE, {})
  topic = config.get("ntfy_topic")
  urls = config.get("urls", [])

  if not topic or not urls:
    print("[!] Agrega tu topic y URLs en config.json")
    return

  notifier = NtfyNotifier(topic)
  scraper = ProductScraper()
  state = load_json(STATE_FILE, {})

  print(f"\n--- Iniciando escaneo ({len(urls)} productos) ---")

  for url in urls:
    title, editorial, current_stock = scraper.get_product_data(url)
    
    last_data = state.get(url, {})
    
    last_stock = last_data.get("stock")
    last_title = last_data.get("title", "Desconocido")
    last_editorial = last_data.get("editorial", "Desconocida")

    if title == "Página no encontrada" and last_title != "Desconocido":
      title = last_title
      editorial = last_editorial

    print(f"\n[{editorial}] {title} -> {current_stock}")

    if last_stock is None:
      state[url] = {"title": title, "editorial": editorial, "stock": current_stock}
      print("  -> Guardado en historial inicial.")
      
    elif current_stock != last_stock:
      print("  [!] CAMBIO DETECTADO -> Notificando...")
      notifier.send_stock_alert(title, editorial, last_stock, current_stock, url)

      state[url] = {"title": title, "editorial": editorial, "stock": current_stock}
      
    else:
      print("  -> Sin cambios.")

  save_json(STATE_FILE, state)
  print("\n--- Escaneo finalizado ---")

if __name__ == "__main__":
  run_monitor()