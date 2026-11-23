import os
import hashlib
import urllib.request
import urllib.parse
import json
import time
from datetime import datetime, timezone, timedelta
import ecdsa
from ecdsa import SigningKey, SECP256k1

STATE_FILE = "state_xrpl.txt"
FOUND_FILE = "FOUND_XRPL.txt"

def get_argentina_time() -> str:
    """Retorna la hora actual en Argentina (ART, UTC-3)."""
    art_tz = timezone(timedelta(hours=-3))
    return datetime.now(art_tz).strftime("%Y-%m-%d %H:%M:%S ART")

def send_telegram_alert(message: str):
    """Envía notificación push instantánea a Telegram usando Secrets del repositorio."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("[*] Telegram no configurado (Faltan Secrets TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID).")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("[*] Alerta de Telegram enviada exitosamente.")
            else:
                print(f"[!] Error al enviar Telegram: HTTP {response.status}")
    except Exception as e:
        print(f"[!] Excepción enviando Telegram: {e}")

def save_state(priv_hex: str):
    with open(STATE_FILE, "w") as f:
        f.write(priv_hex)

def get_last_state() -> bytes:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            val = f.read().strip()
            if val:
                try:
                    return bytes.fromhex(val)
                except ValueError:
                    pass
    return os.urandom(32)

def derive_xrpl_address(priv_bytes: bytes) -> str:
    alphabet = b"rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz"
    
    sk = SigningKey.from_string(priv_bytes, curve=SECP256k1)
    pub = sk.verifying_key.to_string()
    pub_key = (b'\x02' if pub[63] % 2 == 0 else b'\x03') + pub[:32]
    
    h = hashlib.sha256(pub_key).digest()
    r = hashlib.new('ripemd160', h).digest()
    
    payload = b'\x00' + r
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    full_payload = payload + checksum
    
    numeric = int.from_bytes(full_payload, 'big')
    result = bytearray()
    while numeric > 0:
        numeric, rem = divmod(numeric, 58)
        result.append(alphabet[rem])
    
    for byte in full_payload:
        if byte == 0:
            result.append(alphabet[0])
        else:
            break
            
    return result[::-1].decode('utf-8')

def main():
    targets = {"rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"} # Genesis Account XRPL (o tus objetivos)
    
    last_priv = get_last_state()
    print(f"[*] XRPL Engine - Continuando desde clave: {last_priv.hex()}")
    
    start_time = time.time()
    count = 0
    current_priv_int = int.from_bytes(last_priv, 'big')
    
    # Configurado exactamente a 3,000,000 de direcciones por lote
    batch_size = 3000000
    match_found = False
    found_details = ""
    
    for _ in range(batch_size):
        current_priv_int += 1
        priv_bytes = current_priv_int.to_bytes(32, 'big')
        addr = derive_xrpl_address(priv_bytes)
        count += 1
        
        if addr in targets:
            match_found = True
            art_now = get_argentina_time()
            found_details = (
                f"🚨🚨 *¡ALERTA CRÍTICA: COINCIDENCIA XRPL!* 🚨🚨\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"🎯 *Dirección:* \n`{addr}`\n\n"
                f"🔑 *Clave Privada:* \n`{priv_bytes.hex()}`\n\n"
                f"⏰ *Timestamp:* `{art_now}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🔥 *¡Copia cada campo con un toque arriba!*"
            )
            print(found_details)
            with open(FOUND_FILE, "a") as f:
                f.write(found_details + "\n")
            send_telegram_alert(found_details)
            break
            
    duration = time.time() - start_time
    rate = int(count / max(duration, 0.001))
    final_hex = current_priv_int.to_bytes(32, 'big').hex()
    save_state(final_hex)
    
    print(f"[*] Lote completado ({count} hashes en {duration:.2f}s). Estado guardado: {final_hex}")

    if not match_found:
        # Notificación informativa de control por ciclo en hora de Argentina (ART, UTC-3)
        art_now = get_argentina_time()
        msg_normal = (
            f"📊 *[XRPL ENGINE] Ciclo Exitoso*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔢 *Lote procesado:* `{count:,}` claves\n"
            f"⚡ *Velocidad:* `{rate:,} keys/sec`\n"
            f"⏱️ *Duración:* `{duration:.2f}s`\n"
            f"📌 *Siguiente puntero:* `{final_hex[:12]}...`\n"
            f"⏰ *Hora Arg:* `{art_now}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🟢 *Estado:* Operativo & Sincronizado"
        )
        send_telegram_alert(msg_normal)

if __name__ == "__main__":
    main()
