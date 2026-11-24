import os
import requests
import time
import json
from datetime import datetime, timezone, timedelta

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
    for i in range(3):
        try:
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                return True
            time.sleep(2)
        except Exception as e:
            time.sleep(5)
    return False

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"cycles_run": 0}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except:
        pass

if __name__ == "__main__":
    state = load_state()
    state["cycles_run"] += 1
    save_state(state)
    
    msg = (
        f"🟢 *XRPL Engine Activo*\n"
        f"⏱ Hora ART: `{get_argentina_time()}`\n"
        f"🔄 Ciclo N°: `{state['cycles_run']}`\n"
        f"🚀 Estado: Procesando búsqueda de direcciones..."
    )
    
    send_telegram_message(msg)
