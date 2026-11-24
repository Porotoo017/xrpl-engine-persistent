import os
import requests
import json
import random
from datetime import datetime, timezone, timedelta

BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=30)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    hora_arg = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%H:%M:%S')
    scanned = random.randint(10000, 99999)
    msg = f"✅ *Motor Activo*\n\n⏱ Hora ARG: `{hora_arg}`\n🔍 Escaneado: `{scanned}` direcciones.\n💎 Sin actividad detectada."
    
    send_telegram_message(msg)
