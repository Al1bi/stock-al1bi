import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN_SECRETO = os.getenv("TOKEN_SECRETO")

NTFY_TOKEN = os.getenv("NTFY_TOKEN")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")

JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_API_KEY = os.getenv("JSONBIN_API_KEY")

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_urls():
  if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
      return json.load(f).get("urls", [])
  return []

URLS_TO_SCAN = load_urls()