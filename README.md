# xrpl-engine-persistent

Monitor automatizado en tiempo real de **XRPL Mainnet** y mercado **XRP/USD** con notificaciones por Telegram cada 15 minutos (`*/15 * * * *`).

## Datos reales incluidos
- **Precio XRP/USD** con failover automático (`Kraken`, `CoinGecko`, `Coinbase`, `Binance`) + referencia en ARS.
- **Telemetría on-chain de XRPL Mainnet** (`xrplcluster.com` / `s1.ripple.com`): último ledger validado, ledgers cerrados desde el último aviso, cantidad real de transacciones por tipo, volumen de pagos XRP y mayor transferencia del ledger.
- **Seguridad:** las credenciales se leen únicamente desde GitHub Secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
