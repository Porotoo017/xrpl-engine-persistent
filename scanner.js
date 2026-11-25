import { Wallet, Client } from 'xrpl';
import fs from 'fs';

const XRPL_SERVER = 'wss://xrplcluster.com';
const BATCH_SIZE = 50; // Cantidad de wallets a generar por ejecución de GitHub Action

async function run() {
    console.log('[*] Conectando a XRPL Mainnet para escaneo autónomo...');
    const client = new Client(XRPL_SERVER);
    
    try {
        await client.connect();
        console.log('[+] Conectado exitosamente al nodo.');

        let hallazgos = [];
        if (fs.existsSync('hallazgos_reales.json')) {
            hallazgos = JSON.parse(fs.readFileSync('hallazgos_reales.json', 'utf8'));
        }

        for (let i = 0; i < BATCH_SIZE; i++) {
            // Generación de wallet real criptográfica
            const wallet = Wallet.generate();
            const address = wallet.address;
            const seed = wallet.seed;

            try {
                // Consulta de balance en la red real
                const response = await client.request({
                    command: 'account_info',
                    account: address,
                    ledger_index: 'validated'
                });

                const balanceDrops = response.result.account_data.Balance;
                const balanceXRP = Number(balanceDrops) / 1_000_000;

                console.log(`[Revisado] ${address} | Balance: ${balanceXRP} XRP`);

                if (balanceXRP > 0) {
                    console.log(`[¡HALLAZGO!] Cuenta con saldo encontrada: ${address}`);
                    hallazgos.push({
                        address,
                        seed,
                        balance: balanceXRP,
                        timestamp: new Date().toISOString()
                    });
                }
            } catch (err) {
                // Si la cuenta no existe en el ledger (Error 'actNotFound'), da 0 balance
                if (err.data && err.data.error === 'actNotFound') {
                    // Cuenta nueva sin activar (0 XRP)
                    continue;
                } else {
                    console.warn(`[!] Nota en ${address}:`, err.message || err);
                }
            }
        }

        fs.writeFileSync('hallazgos_reales.json', JSON.stringify(hallazgos, null, 2));
        console.log('[*] Lote de escaneo completado y guardado.');

    } catch (error) {
        console.error('[X] Error crítico en el motor:', error);
        process.exit(1);
    } finally {
        await client.disconnect();
    }
}

run();
