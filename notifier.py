import requests

class SimplepushNotifier:
  def __init__(self, key):
    self.key = key.strip() # Tu llave de 6 letras de la app

  def send_stock_alert(self, title, editorial, old_stock, new_stock, product_url):
    url = f"https://api.simplepush.io/send"
      
    payload = {
        "key": self.key,
        "title": f"¡Stock actualizado! ({editorial})",
        "msg": f"{title}\nStock: {old_stock} ➔ {new_stock}\nLink: {product_url}"
    }
      
    try:
      response = requests.post(url, json=payload, timeout=15)
      response.raise_for_status()
      print("Notificación de Simplepush enviada con éxito")
    except Exception as e:
      print(f"Error enviando a Simplepush: {e}")