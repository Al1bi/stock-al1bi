from upstash_redis import Redis
import json
import requests
from settings import (
  JSONBIN_ID, JSONBIN_API_KEY,
  UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN
)
class Storage:
  def __init__(self, filepath="db_local.json"):
    self.bin_url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    self.bin_headers = {
      "X-Master-Key": JSONBIN_API_KEY,
      "Content-Type": "application/json"
    }

    # --- Configuración Upstash Redis REST (Catálogos) ---
    try:
      self.redis = Redis(
        url=UPSTASH_REDIS_REST_URL,
        token=UPSTASH_REDIS_REST_TOKEN
      )
    except Exception as e:
      print(f"Error inicializando cliente Upstash: {e}")
      self.redis = None

  def get_catalog(self, editorial: str) -> dict:
    """Obtiene el catálogo como un diccionario."""
    if not self.redis:
      return {}

    redis_key = f"catalogo_{editorial.lower()}"
    try:
      datos = self.redis.get(redis_key)
      # Upstash devuelve un string JSON, lo convertimos a diccionario Python
      return json.loads(datos) if datos else {}
    except Exception as e:
      print(f"Error leyendo catálogo en Upstash: {e}")
      return {}

  def save_catalog(self, editorial: str, catalog_dict: dict):
    """Guarda el diccionario entero como JSON."""
    if not self.redis or not catalog_dict:
      return

    redis_key = f"catalogo_{editorial.lower()}"
    try:
      self.redis.set(redis_key, json.dumps(catalog_dict))
    except Exception as e:
      print(f"Error guardando catálogo en Upstash: {e}")

  # --- Lógica de Stocks Individuales ---
  def get_all_products(self) -> dict:
    """Descarga el historial desde JSONBin."""
    try:
      res = requests.get(self.bin_url, headers=self.bin_headers)
      if res.status_code == 200:
        return res.json().get("record", {})
    except Exception as e:
      print(f"Error cargando estado desde JSONBin: {e}")
    return {}

  def save_all_products(self, products_dict: dict):
    """Sube el historial actualizado a JSONBin."""
    try:
      requests.put(self.bin_url, json=products_dict, headers=self.bin_headers)
    except Exception as e:
      print(f"Error guardando estado en JSONBin: {e}")