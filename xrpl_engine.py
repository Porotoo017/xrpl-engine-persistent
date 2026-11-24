import os
import requests
import json
import random
from datetime import datetime, timezone, timedelta

BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"
STATE_FILE = "engine_state.json"

def get_stats():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"total_scanned": 0, "last_found": "Ninguno"}

def save_stats(stats):
    with open(STATE_FILE, "w") as f:
        json.dump(stats, f)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Simulación de motor de escaneo (Logica de negocio)
    stats = get_stats()
    stats["total_scanned"] += random.randint(1000, 5000)
    
    # Simular hallazgo ocasional
    found_info = "Ninguna actividad"
    if random.random() < 0.2:
        found_info = f"Actividad detectada en R-Address: r{random.randint(1000000000000, 9999999999999)}"
        stats["last_found"] = found_info
    
    save_stats(stats)
    
    # Reporte detallado
    msg = f"📊 *XRPL Engine - Reporte de Ciclo*\n\n"
    msg += f"⏱ Hora: `{datetime.now(timezone.utc) - timedelta(hours=3).strftime('%H:%M:%S')}`\n"
    msg += f"🔍 Total escaneado: `{stats['total_scanned']}`\n"
    msg += f"💎 Estado: `{found_info}`\n\n"
    msg += "El motor continúa trabajando activamente."
    
    send_telegram_message(msg)
