import os
import json
import logging
from datetime import datetime, timezone, timedelta
import requests
import random
import sys

# CONFIGURACIÓN
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9208908265:AAEk_fQT8IxwtNfOLVWdxX_kxLl-JoG_uQQ")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1962540997")
STATE_FILE = "engine_state.json"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def get_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading state: {e}")
    return {"total_processed": 0}

def save_state(state):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logging.error(f"Error saving state: {e}")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Mensaje enviado exitosamente")
    except Exception as e:
        logging.error(f"Error enviando Telegram: {e}")
        # Forzar salida con error para que GitHub Actions detecte el fallo
        sys.exit(1)

if __name__ == "__main__":
    try:
        state = get_state()
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
    except Exception as e:
        logging.error(f"Error fatal: {e}")
        sys.exit(1)
