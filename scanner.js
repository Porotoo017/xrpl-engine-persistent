import { Wallet, Client } from 'xrpl';
import fs from 'fs';

async function scan() {
  const client = new Client('wss://xrplcluster.com');
  await client.connect();

  const wallet = Wallet.generate();
  const address = wallet.address;
  const seed = wallet.seed;

  try {
    const response = await client.request({
      command: 'account_info',
      account: address,
      ledger_index: 'validated'
    });

    const balance = response.result.account_data.Balance;
    console.log(`Verificado: ${address} | Balance: ${balance}`);
    
    if (parseInt(balance) > 0) {
      const log = `HALLAZGO REAL: ${address} | SEED: ${seed} | BALANCE: ${balance}\n`;
      fs.appendFileSync('hallazgos_reales.txt', log);
    }
  } catch (e) {
    console.log(`Cuenta nueva: ${address}`);
  }

  await client.disconnect();
}

scan().catch(console.error);
