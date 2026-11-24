import os
import requests
import json
import time

# Configuración del bot
BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print("SUCCESS: Mensaje enviado a Telegram")
            return True
        else:
            print(f"FAILED: Error {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"FAILED: Excepción - {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Motor iniciado: Enviando señal de prueba...")
    if send_telegram_message("✅ El motor se ha reiniciado correctamente con el nuevo token y está operativo."):
        print("Test exitoso.")
    else:
        print("Test fallido.")
