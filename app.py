from flask import Flask
import os
import requests
from notifier import SimplepushNotifier
from scraper import ProductScraper
import json

app = Flask(__name__)

# --- CREDENCIALES DE JSONBIN ---
BIN_ID = "6a9721f0f5f4af5e295de20e"
API_KEY = "$2a$10$eXLp.Q/WzrN8J5JE4ikLu.21D0K6XodjijoYbiTWFJKG9HgFrrZJm"
BIN_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

# El config.json sí lo dejamos local porque no cambia, solo se lee.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_local_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_cloud_state():
    """Descarga el historial desde JSONBin."""
    try:
        res = requests.get(BIN_URL, headers=HEADERS)
        if res.status_code == 200:
            return res.json().get("record", {})
    except Exception as e:
        print(f"Error cargando estado: {e}")
    return {}

def save_cloud_state(state):
    """Sube el historial actualizado a JSONBin."""
    try:
        requests.put(BIN_URL, json=state, headers=HEADERS)
    except Exception as e:
        print(f"Error guardando estado: {e}")

@app.route('/')
def home():
    return "Servidor de monitoreo en línea. Internet sin restricciones."

@app.route('/ejecutar-scan')
def run_monitor():
    config = load_local_config()
    simplepush_key = config.get("simplepush_key")
    urls = config.get("urls", [])

    if not simplepush_key or not urls:
        return "Error: Faltan URLs en el config", 400

    notifier = SimplepushNotifier(simplepush_key)
    scraper = ProductScraper()
    state = load_cloud_state() 
    
    cambios_detectados = 0

    for url in urls:
        title, editorial, current_stock = scraper.get_product_data(url)
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
            notifier.send_stock_alert(title, editorial, last_stock, current_stock, url)
            state[url] = {"title": title, "editorial": editorial, "stock": current_stock}
            cambios_detectados += 1

    save_cloud_state(state) # <-- Guarda en la nube
    return f"Escaneo completado. Cambios detectados: {cambios_detectados}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)