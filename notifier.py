import requests
from settings import NTFY_TOKEN, NTFY_TOPIC

class NtfyNotifier:
  def __init__(self):
    self.token = NTFY_TOKEN
    self.topic = NTFY_TOPIC
    self.url = "https://ntfy.sh/"
    
    self.headers = {
      "Content-Type": "application/json"
    }
    # Solo inyectar la cabecera si el token existe
    if self.token:
      self.headers["Authorization"] = f"Bearer {self.token}"

  def send_catalog_alert(self, titulo, mensaje):
    payload = {
      "topic": self.topic,
      "title": titulo,
      "message": mensaje,
      "tags": ["loudspeaker"]
    }
    try:
      res = requests.post(self.url, json=payload, headers=self.headers, timeout=15)
      res.raise_for_status()
    except requests.exceptions.HTTPError as e:
      print(f"Error HTTP enviando alerta a ntfy: {e.response.status_code} - {e.response.text}")
    except Exception as e:
      print(f"Error de red enviando alerta de catálogo a ntfy: {e}")