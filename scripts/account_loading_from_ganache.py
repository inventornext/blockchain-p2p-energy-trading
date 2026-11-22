import json
from eth_account import Account
import os

# Enable HD wallet features
Account.enable_unaudited_hdwallet_features()

# 🔑 Your Ganache mnemonic
mnemonic = "YOUR_GANACHE_MNEMONIC"  # paste the mnemonic shown by your local Ganache
base_path = "m/44'/60'/0'/0/"

# Number of accounts to derive
num_accounts = 100

accounts = []

for i in range(num_accounts):
    acct = Account.from_mnemonic(mnemonic, account_path=base_path + str(i))
    accounts.append({
        "index": i,
        "address": acct.address,
        "private_key": acct.key.hex()
    })

# ✅ Save to project folder
script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(script_path))  # one level up from /scripts
output_path = os.path.join(project_root, "data/accounts.json")

with open(output_path, "w") as f:
    json.dump(accounts, f, indent=4)

print(f"✅ Saved {num_accounts} accounts to {output_path}")
