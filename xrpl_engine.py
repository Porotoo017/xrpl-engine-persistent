import argparse
import html
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

STATE_FILE = "engine_state.json"
ARG_TZ = timezone(timedelta(hours=-3))
USER_AGENT = "xrpl-monitor/2.0"

XRPL_NODES = [
    "https://xrplcluster.com",
    "https://s1.ripple.com:51234",
    "https://s2.ripple.com:51234",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)


def http_get_json(url: str, timeout: int = 12) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_state() -> dict:
    defaults = {
        "cycles_run": 0,
        "last_ledger_index": None,
        "last_price_usd": None,
        "last_run_utc": None,
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                defaults.update(
                    {
                        "cycles_run": int(loaded.get("cycles_run") or 0),
                        "last_ledger_index": loaded.get("last_ledger_index"),
                        "last_price_usd": loaded.get("last_price_usd"),
                        "last_run_utc": loaded.get("last_run_utc"),
                    }
                )
        except Exception as exc:
            logging.warning("No se pudo leer %s (%s); usando estado limpio.", STATE_FILE, exc)
    return defaults


def save_state(state: dict) -> None:
    tmp_file = f"{STATE_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, STATE_FILE)


def fetch_xrp_market() -> dict:
    """Obtiene cotización real de XRP con failover multi-fuente."""
    errors = []

    # 1. Kraken (confiable desde runners US y global)
    try:
        d = http_get_json("https://api.kraken.com/0/public/Ticker?pair=XRPUSD")
        pair = d["result"]["XXRPZUSD"]
        price = float(pair["c"][0])
        open_24h = float(pair["o"])
        high_24h = float(pair["h"][1])
        low_24h = float(pair["l"][1])
        vol_24h_xrp = float(pair["v"][1])
        chg_24h = ((price - open_24h) / open_24h * 100.0) if open_24h > 0 else None
        if price > 0:
            return {
                "price_usd": price,
                "change_24h_pct": chg_24h,
                "high_24h": high_24h,
                "low_24h": low_24h,
                "vol_24h_xrp": vol_24h_xrp,
                "source": "Kraken",
            }
    except Exception as exc:
        errors.append(f"Kraken: {exc}")

    # 2. CoinGecko
    try:
        d = http_get_json(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=ripple&vs_currencies=usd&include_24hr_change=true"
        )
        r = d["ripple"]
        price = float(r["usd"])
        if price > 0:
            return {
                "price_usd": price,
                "change_24h_pct": float(r.get("usd_24h_change")) if r.get("usd_24h_change") is not None else None,
                "high_24h": None,
                "low_24h": None,
                "vol_24h_xrp": None,
                "source": "CoinGecko",
            }
    except Exception as exc:
        errors.append(f"CoinGecko: {exc}")

    # 3. Coinbase
    try:
        d = http_get_json("https://api.coinbase.com/v2/prices/XRP-USD/spot")
        price = float(d["data"]["amount"])
        if price > 0:
            return {
                "price_usd": price,
                "change_24h_pct": None,
                "high_24h": None,
                "low_24h": None,
                "vol_24h_xrp": None,
                "source": "Coinbase",
            }
    except Exception as exc:
        errors.append(f"Coinbase: {exc}")

    # 4. Binance (puede devolver HTTP 451 en IPs de EE. UU.)
    try:
        d = http_get_json("https://api.binance.com/api/v3/ticker/24hr?symbol=XRPUSDT")
        price = float(d["lastPrice"])
        if price > 0:
            return {
                "price_usd": price,
                "change_24h_pct": float(d["priceChangePercent"]),
                "high_24h": float(d["highPrice"]),
                "low_24h": float(d["lowPrice"]),
                "vol_24h_xrp": float(d["volume"]),
                "source": "Binance",
            }
    except Exception as exc:
        errors.append(f"Binance: {exc}")

    raise RuntimeError("Todas las fuentes de precio fallaron: " + " | ".join(errors))


def fetch_usd_ars_crypto() -> float | None:
    """Consulta cotización real USD cripto en ARS (opcional, no bloqueante)."""
    try:
        d = http_get_json("https://dolarapi.com/v1/dolares/cripto", timeout=8)
        venta = float(d.get("venta") or 0)
        return venta if venta > 0 else None
    except Exception:
        return None


def fetch_xrpl_telemetry() -> dict:
    """Consulta estado real del último ledger validado en XRPL Mainnet."""
    errors = []
    for node in XRPL_NODES:
        try:
            info_res = http_post_json(node, {"method": "server_info", "params": [{}]})
            info = info_res["result"]["info"]
            v_ledger = info.get("validated_ledger", {})
            base_fee_xrp = float(v_ledger.get("base_fee_xrp", 0.00001))
            base_fee_drops = int(round(base_fee_xrp * 1_000_000))
            reserve_base = float(v_ledger.get("reserve_base_xrp", 1.0))

            led_res = http_post_json(
                node,
                {
                    "method": "ledger",
                    "params": [
                        {"ledger_index": "validated", "transactions": True, "expand": True}
                    ],
                },
            )
            led_wrap = led_res["result"]
            led = led_wrap.get("ledger", {})
            ledger_index = int(led_wrap.get("ledger_index") or v_ledger.get("seq"))
            txs = led.get("transactions", [])

            counts = {"Payment": 0, "OfferCreate": 0, "OfferCancel": 0, "TrustSet": 0, "Other": 0}
            total_xrp_transferred = 0.0
            xrp_payments = []

            for tx in txs:
                tx_type = tx.get("TransactionType", "Other")
                if tx_type in counts:
                    counts[tx_type] += 1
                else:
                    counts["Other"] += 1

                if tx_type == "Payment" and isinstance(tx.get("Amount"), str):
                    try:
                        xrp_amt = int(tx["Amount"]) / 1_000_000.0
                        total_xrp_transferred += xrp_amt
                        xrp_payments.append((xrp_amt, tx.get("hash", "")))
                    except ValueError:
                        pass

            xrp_payments.sort(reverse=True)
            top_payment = xrp_payments[0] if xrp_payments else None

            return {
                "node": node.replace("https://", ""),
                "ledger_index": ledger_index,
                "close_time_human": led.get("close_time_human", "N/A"),
                "tx_total": len(txs),
                "counts": counts,
                "xrp_payment_count": len(xrp_payments),
                "total_xrp_transferred": total_xrp_transferred,
                "top_payment": top_payment,
                "base_fee_drops": base_fee_drops,
                "reserve_base_xrp": reserve_base,
            }
        except Exception as exc:
            errors.append(f"{node}: {exc}")

    raise RuntimeError("Nodos XRPL inaccesibles: " + " | ".join(errors))


def format_message(state: dict, market: dict, xrpl: dict, usd_ars: float | None) -> str:
    now_arg = datetime.now(ARG_TZ).strftime("%d/%m/%Y %H:%M:%S ART")
    price = market["price_usd"]

    prev_price = state.get("last_price_usd")
    delta_line = ""
    if isinstance(prev_price, (int, float)) and prev_price > 0:
        diff_pct = ((price - prev_price) / prev_price) * 100.0
        arrow = "📈" if diff_pct >= 0 else "📉"
        delta_line = f"\n{arrow} <b>Vs. último reporte:</b> {diff_pct:+.3f}%"

    chg_24h = market.get("change_24h_pct")
    chg_24h_txt = f"{chg_24h:+.2f}%" if chg_24h is not None else "N/D"

    range_line = ""
    if market.get("high_24h") and market.get("low_24h"):
        range_line = f"\n📏 <b>Rango 24h:</b> ${market['low_24h']:.4f} — ${market['high_24h']:.4f}"

    vol_line = ""
    if market.get("vol_24h_xrp"):
        vol_line = f"\n📦 <b>Volumen 24h:</b> {market['vol_24h_xrp']:,.0f} XRP"

    ars_line = ""
    if usd_ars:
        ars_line = f"\n🇦🇷 <b>Ref. XRP en ARS:</b> ${price * usd_ars:,.2f} ARS (USD cripto ${usd_ars:,.0f})"

    prev_ledger = state.get("last_ledger_index")
    ledger_delta = ""
    if isinstance(prev_ledger, int) and xrpl["ledger_index"] > prev_ledger:
        ledger_delta = f" (<b>+{xrpl['ledger_index'] - prev_ledger:,}</b> desde el último aviso)"

    top_line = ""
    if xrpl.get("top_payment"):
        amt, tx_hash = xrpl["top_payment"]
        top_line = f"\n🐋 <b>Mayor pago del ledger:</b> {amt:,.2f} XRP (<code>{html.escape(tx_hash[:12])}…</code>)"

    c = xrpl["counts"]
    return (
        f"💎 <b>XRP / XRPL MONITOR — DATOS REALES</b>\n\n"
        f"💵 <b>Precio XRP:</b> <code>${price:.4f} USD</code> (24h: <b>{chg_24h_txt}</b>)"
        f"{delta_line}{range_line}{vol_line}{ars_line}\n"
        f"🏦 <b>Fuente mercado:</b> {html.escape(market['source'])}\n\n"
        f"⛓️ <b>XRPL Mainnet (On-Chain Real)</b>\n"
        f"• <b>Ledger validado:</b> <code>#{xrpl['ledger_index']:,}</code>{ledger_delta}\n"
        f"• <b>Cierre:</b> <code>{html.escape(xrpl['close_time_human'])}</code>\n"
        f"• <b>Tx en este ledger:</b> <b>{xrpl['tx_total']}</b> "
        f"(Pagos: {c['Payment']} | DEX: {c['OfferCreate'] + c['OfferCancel']} | Trust: {c['TrustSet']})\n"
        f"• <b>XRP movido en pagos:</b> {xrpl['total_xrp_transferred']:,.2f} XRP "
        f"({xrpl['xrp_payment_count']} pagos XRP){top_line}\n"
        f"• <b>Fee base:</b> {xrpl['base_fee_drops']} drops | <b>Reserva:</b> {xrpl['reserve_base_xrp']:.0f} XRP\n"
        f"• <b>Nodo RPC:</b> <code>{html.escape(xrpl['node'])}</code>\n\n"
        f"⏱ <b>Hora ARG:</b> <code>{now_arg}</code>\n"
        f"🔄 <b>Ciclo:</b> #{state['cycles_run']} | Automático cada 15 min"
    )


def send_telegram(bot_token: str, chat_id: str, html_text: str) -> dict:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    last_err = None
    for attempt in range(1, 4):
        try:
            res = http_post_json(url, payload, timeout=15)
            if res.get("ok"):
                return res
            last_err = f"Telegram ok=false: {res}"
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_err = f"HTTP {exc.code}: {body}"
        except Exception as exc:
            last_err = str(exc)
        logging.warning("Reintento %d/3 envío Telegram fallido: %s", attempt, last_err)
        time.sleep(2 * attempt)
    raise RuntimeError(f"No se pudo enviar mensaje a Telegram tras 3 intentos: {last_err}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor real XRP/XRPL para Telegram")
    parser.add_argument("--dry-run", action="store_true", help="No envía a Telegram ni guarda estado")
    args = parser.parse_args()

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not args.dry_run and (not bot_token or not chat_id):
        logging.error("Faltan variables de entorno TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID.")
        return 1

    state = load_state()
    state["cycles_run"] += 1

    market = fetch_xrp_market()
    xrpl = fetch_xrpl_telemetry()
    usd_ars = fetch_usd_ars_crypto()

    msg = format_message(state, market, xrpl, usd_ars)

    if args.dry_run:
        print(msg)
        return 0

    tg_res = send_telegram(bot_token, chat_id, msg)
    msg_id = tg_res.get("result", {}).get("message_id")
    logging.info("Mensaje enviado correctamente a Telegram (message_id=%s).", msg_id)

    state["last_ledger_index"] = xrpl["ledger_index"]
    state["last_price_usd"] = round(market["price_usd"], 6)
    state["last_run_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(state)
    logging.info("Estado persistido: ledger=%s price=$%.4f", state["last_ledger_index"], state["last_price_usd"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
