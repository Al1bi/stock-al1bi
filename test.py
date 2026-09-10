import requests

headers = {
  "Authorization": "tk_scdmuupplmh0s41boyaey1x2ywd25"
}
requests.post("https://ntfy.sh/book-tracker-al1bi", data="Mensaje de prueba", headers=headers)