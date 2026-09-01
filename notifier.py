import requests
import socket
import urllib3.util.connection as urllib3_cn

# --- PARCHE DE RED PARA RENDER ---
# Obliga a Python a usar IPv4 y evita el error "Network is unreachable" con IPv6
def allowed_gai_family():
  return socket.AF_INET

urllib3_cn.allowed_gai_family = allowed_gai_family
# ---------------------------------

class NtfyNotifier:
  def __init__(self, topic):
    self.topic = topic.strip()

  def send_stock_alert(self, title, editorial, old_stock, new_stock, product_url):
    url = "https://ntfy.sh/"
    
    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
      "topic": self.topic,
      "title": f"¡Stock actualizado! ({editorial})",
      "message": f"{title}\n {old_stock} ➔ {new_stock}",
      "click": product_url,
      "tags": ["blue_book"]
    }
    
    try:
      response = requests.post(url, json=payload, headers=headers, timeout=15)
      response.raise_for_status()
      print(f"Notificación enviada con éxito (Status: {response.status_code})")
    except Exception as e:
      print(f"Error crítico enviando notificación: {e}")
