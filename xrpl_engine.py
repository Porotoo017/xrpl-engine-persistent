import os
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
    art_tz = timezone(timedelta(hours=-3))
    return datetime.now(art_tz).strftime("%Y-%m-%d %H:%M:%S ART")

def send_telegram_alert(message: str):
    token = "9208908265:AAEk_fQT8IxwtNfOLVWdxX_kxLl-JoG_uQQ"
    chat_id = "1962540997"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    
    # FORZAR Headers de navegador para evitar bloqueo de seguridad
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode('utf-8')
            if response.status == 200:
                print(f"[*] Alerta enviada con éxito: {res_body[:50]}")
            else:
                print(f"[!] Error Telegram HTTP {response.status}: {res_body}")
    except Exception as e:
        print(f"[!] Excepción crítica enviando Telegram: {e}")

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
    targets = {"rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"} 
    last_priv = get_last_state()
    print(f"[*] XRPL Engine iniciado. Puntero: {last_priv.hex()}")
    
    # Envío de inicio para confirmar conectividad
    send_telegram_alert("🚀 *Motor XRPL Iniciado:* Procesando bloque de 500k...")
    
    start_time = time.time()
    count = 0
    current_priv_int = int.from_bytes(last_priv, 'big')
    batch_size = 500000
    match_found = False
    
    for _ in range(batch_size):
        current_priv_int += 1
        priv_bytes = current_priv_int.to_bytes(32, 'big')
        addr = derive_xrpl_address(priv_bytes)
        count += 1
        if addr in targets:
            match_found = True
            break
            
    duration = time.time() - start_time
    final_hex = current_priv_int.to_bytes(32, 'big').hex()
    save_state(final_hex)
    
    if match_found:
        send_telegram_alert("🚨 COINCIDENCIA ENCONTRADA")
    else:
        msg = f"📊 *[XRPL ENGINE] Ciclo OK*\nLote: `{count:,}` | Velocidad: `{int(count/max(duration, 1)):,} keys/s` | Hora: `{get_argentina_time()}`"
        send_telegram_alert(msg)

if __name__ == "__main__":
    import hashlib
    main()
