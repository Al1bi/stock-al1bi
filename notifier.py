import requests
from settings import NTFY_TOKEN, NTFY_TOPIC

class NtfyNotifier:
  def __init__(self):
    self.token = NTFY_TOKEN
    self.topic = NTFY_TOPIC
    self.url = "https://ntfy.sh/"
    self.headers = {
      "Authorization": f"Bearer {self.token}",
      "Content-Type": "application/json"
    }

  def send_stock_alert(self, title, editorial, old_stock, new_stock, product_url):
    payload = {
      "topic": self.topic,
      "title": f"¡Stock actualizado! ({editorial})",
      "message": f"{title}\nStock: {old_stock} ➔ {new_stock}",
      "click": product_url,
      "tags": ["bell"] # Opcional: Agrega un emoji a la notificación
    }
    try:
      requests.post(self.url, json=payload, headers=self.headers, timeout=15)
    except Exception as e:
      print(f"Error enviando alerta de stock a ntfy: {e}")

  def send_catalog_alert(self, titulo, mensaje):
    payload = {
      "topic": self.topic,
      "title": titulo,
      "message": mensaje,
      "tags": ["loudspeaker"] # Opcional: Agrega un emoji a la notificación
    }
    try:
      requests.post(self.url, json=payload, headers=self.headers, timeout=15)
    except Exception as e:
      print(f"Error enviando alerta de catálogo a ntfy: {e}")