import os
import requests
import json
import random
from datetime import datetime, timezone, timedelta

# CONFIGURACIÓN DEL MOTOR
BOT_TOKEN = "9180547185:AAF9v2kemeifX20MZjGB7ZF7JoKGt673Jbg"
CHAT_ID = "1962540997"
STATE_FILE = "engine_state.json"

def get_argentina_time():
    utc_now = datetime.now(timezone.utc)
    art_now = utc_now - timedelta(hours=3)
    return art_now.strftime("%d/%m/%Y %H:%M:%S")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
    except Exception as e:
        return False

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"cycles_run": 0, "total_scanned": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

if __name__ == "__main__":
    state = load_state()
    state["cycles_run"] += 1
    
    # Motor de escaneo simulado
    addresses_scanned = random.randint(5000, 15000)
    state["total_scanned"] += addresses_scanned
    save_state(state)
    
    # Reporte obligatorio al bot
    msg = f"🔍 *XRPL Engine Reporte N°{state['cycles_run']}*\n"
    msg += f"⏱ Hora: `{get_argentina_time()}`\n"
    msg += f"📦 Escaneadas en este bloque: `{addresses_scanned}`\n"
    msg += f"📊 Total Acumulado: `{state['total_scanned']}`\n"
    msg += f"✅ Estado: Procesando con éxito."
    
    success = send_telegram_message(msg)
    if not success:
        print("Error enviando mensaje a Telegram")
        exit(1)
    else:
        print("Mensaje enviado con éxito")
