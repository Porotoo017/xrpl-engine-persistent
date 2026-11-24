import os
import requests
import json
from datetime import datetime, timezone, timedelta

# CONFIGURACIÓN DEL BOT Y CHAT (VALIDADOS)
BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"
STATE_FILE = "engine_state.json"

def log_debug(message):
    print(f"[DEBUG] {message}")
    with open("engine_debug.log", "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

def send_telegram_message(text):
    log_debug(f"Intentando enviar: {text[:50]}...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=30)
        log_debug(f"Status Telegram: {response.status_code}, Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        log_debug(f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    log_debug("Iniciando motor XRPL...")
    
    # Reporte de diagnóstico
    msg = f"🚀 *XRPL Engine - Diagnóstico Activado*\n"
    msg += f"⏱ Hora: `{datetime.now(timezone.utc) - timedelta(hours=3)}`\n"
    msg += f"✅ Estado: Sistema de comunicación en línea."
    
    success = send_telegram_message(msg)
    if success:
        log_debug("Reporte enviado correctamente.")
    else:
        log_debug("Fallo al enviar reporte.")
        exit(1)
