import requests
from settings import PUSHBULLET_TOKEN

class PushbulletNotifier:
  def __init__(self):
    self.token = PUSHBULLET_TOKEN
    self.url = "https://api.pushbullet.com/v2/pushes"
    self.headers = {
      "Access-Token": self.token,
      "Content-Type": "application/json"
    }

  def send_stock_alert(self, title, editorial, old_stock, new_stock, product_url):
    payload = {
      "type": "link",
      "title": f"¡Stock actualizado! ({editorial})",
      "body": f"{title}\nStock: {old_stock} ➔ {new_stock}",
      "url": product_url
    }
    try:
      requests.post(self.url, json=payload, headers=self.headers, timeout=15)
    except Exception as e:
      print(f"Error enviando a Pushbullet: {e}")

  def send_catalog_alert(self, editorial, new_book_title):
    payload = {
      "type": "note",
      "title": f"Nuevo libro en {editorial}",
      "body": f"Se ha agregado al catálogo: {new_book_title}"
    }
    try:
      requests.post(self.url, json=payload, headers=self.headers, timeout=15)
    except Exception as e:
      print(f"Error enviando alerta de catálogo a Pushbullet: {e}")