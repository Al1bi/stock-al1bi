import requests

class NtfyNotifier:
  def __init__(self, topic: str):
    self.endpoint = f"https://ntfy.sh/{topic}"

  def send_stock_alert(self, title: str, editorial: str, old_stock: str, new_stock: str, url: str):
    message = (
      f"Título: {title}\n"
      f"Editorial: {editorial}\n"
      f"Cambio de stock: [{old_stock}] a [{new_stock}]\n\n"
      f"Toca para abrir la tienda."
    )

    headers = {
      "Title": f"¡Cambio de Stock!".encode("utf-8"),
      "Priority": "high",
      "Tags": "books",
      "Click": url,
    }

    try:
      requests.post(self.endpoint, data=message.encode("utf-8"), headers=headers, timeout=10)
    except Exception as e:
      print(f"[Error ntfy] {e}")