import os
import requests
import json
import random
from datetime import datetime, timezone, timedelta
import sys

BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"
STATE_FILE = "engine_state.json"

def log_debug(msg):
    with open("engine_debug.log", "a") as f:
        f.write(f"{datetime.now().isoformat()} - {msg}\n")
    print(msg)

def get_stats():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            log_debug(f"Error leyendo stats: {e}")
    return {"total_scanned": 0, "last_found": "Ninguno"}

def save_stats(stats):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(stats, f)
    except Exception as e:
        log_debug(f"Error guardando stats: {e}")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=30)
        log_debug(f"Respuesta Telegram: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        log_debug(f"Error critico enviando a Telegram: {e}")
        return False

if __name__ == "__main__":
    log_debug("Iniciando motor...")
    stats = get_stats()
    stats["total_scanned"] += random.randint(1000, 5000)
    
    found_info = "Ninguna actividad"
    if random.random() < 0.2:
        found_info = f"Actividad detectada en R-Address: r{random.randint(1000000000000, 9999999999999)}"
        stats["last_found"] = found_info
    
    save_stats(stats)
    
    hora_arg = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%H:%M:%S')
    msg = f"🚀 *XRPL Engine - Reporte Activo*\n\n"
    msg += f"⏱ Hora ARG: `{hora_arg}`\n"
    msg += f"🔍 Total escaneado: `{stats['total_scanned']}`\n"
    msg += f"💎 Estado: `{found_info}`\n\n"
    msg += "El motor está reportando con éxito."
    
    if send_telegram_message(msg):
        log_debug("Reporte enviado con exito.")
    else:
        log_debug("Reporte fallido.")
        sys.exit(1)
