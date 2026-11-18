import os
import hashlib
import base58
import ecdsa
from ecdsa import SigningKey, SECP256k1

STATE_FILE = "state_xrpl.txt"
FOUND_FILE = "FOUND_XRPL.txt"

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
    """
    Derivación estándar de dirección XRPL (Ripple) a partir de clave privada secp256k1.
    1. Public Key (compressed 33 bytes)
    2. SHA256 -> RIPEMD160
    3. Prefijo 0x00 (account ID)
    4. Base58Check con Alphabet XRPL (rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz)
    """
    alphabet = b"rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz"
    
    sk = SigningKey.from_string(priv_bytes, curve=SECP256k1)
    pub = sk.verifying_key.to_string()
    pub_key = (b'\x02' if pub[63] % 2 == 0 else b'\x03') + pub[:32]
    
    h = hashlib.sha256(pub_key).digest()
    r = hashlib.new('ripemd160', h).digest()
    
    # XRPL account ID prefix = 0x00
    payload = b'\x00' + r
    
    # Checksum: primer 4 bytes del doble SHA256
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    full_payload = payload + checksum
    
    # Conversión a base58 con alfabeto XRPL
    # Implementación manual base58 check custom alphabet
    numeric = int.from_bytes(full_payload, 'big')
    result = bytearray()
    while numeric > 0:
        numeric, rem = divmod(numeric, 58)
        result.append(alphabet[rem])
    
    # Añadir ceros a la izquierda
    for byte in full_payload:
        if byte == 0:
            result.append(alphabet[0])
        else:
            break
            
    return result[::-1].decode('utf-8')

def main():
    # Ejemplo de cuentas target o saldo conocido en XRPL
    targets = {"rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"} # Genesis Account XRPL
    
    last_priv = get_last_state()
    print(f"[*] XRPL Engine - Continuando desde clave: {last_priv.hex()}")
    
    # Lote optimizado para ejecución de 5 minutos en GitHub Actions
    count = 0
    current_priv_int = int.from_bytes(last_priv, 'big')
    
    for _ in range(400000):
        current_priv_int += 1
        priv_bytes = current_priv_int.to_bytes(32, 'big')
        addr = derive_xrpl_address(priv_bytes)
        count += 1
        
        if addr in targets:
            msg = f"[!] ¡ÉXITO XRPL! Dirección: {addr} | PrivKey: {priv_bytes.hex()}\n"
            print(msg)
            with open(FOUND_FILE, "a") as f:
                f.write(msg)
            break
            
    final_hex = current_priv_int.to_bytes(32, 'big').hex()
    save_state(final_hex)
    print(f"[*] Lote completado ({count} hashes). Estado guardado: {final_hex}")

if __name__ == "__main__":
    main()
