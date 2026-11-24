import os
import requests
import time

BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.status_code == 200
    except Exception:
        return False

if __name__ == "__main__":
    status = send_telegram_message("🚀 Motor XRPL: Ciclo de procesamiento iniciado. Buscando en nuevo lote de direcciones...")
    print(f"Status del envío: {status}")
