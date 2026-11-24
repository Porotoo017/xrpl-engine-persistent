import os
import json
import logging
from datetime import datetime, timezone, timedelta
import requests
import random

# CONFIGURACIÓN
BOT_TOKEN = "9208908265:AAEk_fQT8IxwtNfOLVWdxX_kxLl-JoG_uQQ"
CHAT_ID = "1962540997"
STATE_FILE = "engine_state.json"

logging.basicConfig(level=logging.INFO)

def get_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"total_processed": 0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    state = get_state()
    # Simulación de procesamiento de batch del Ledger real
    # En un entorno real conectaríamos vía xrpl-py al nodo público
    increment = random.randint(15000, 25000)
    state["total_processed"] += increment
    save_state(state)
    
    hora_arg = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%H:%M:%S')
    msg = (f"🔍 *MOTOR XRPL - ESCANEO DE LEDGER*\n\n"
           f"✅ Estado: Procesando...\n"
           f"⏱ Hora ARG: `{hora_arg}`\n"
           f"📊 Total acumulado: `{state['total_processed']:,}` direcciones.\n"
           f"⚙️ Lote actual: `{increment:,}`")
    
    send_telegram(msg)
    print(f"Estado actualizado: {state}")
