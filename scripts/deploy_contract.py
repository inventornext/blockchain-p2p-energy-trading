import json
import os
from web3 import Web3

# Step 1: Connect to Ganache
ganache_url = os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")
web3 = Web3(Web3.HTTPProvider(ganache_url))
assert web3.is_connected(), "❌ Web3 is not connected to Ganache"

# Step 2: Set default deployer account
deployer_address = web3.eth.accounts[0]
web3.eth.default_account = deployer_address

# Step 3: Load ABI and Bytecode from build folder (in root directory)
build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build"))

with open(os.path.join(build_path, "contract_abi.json"), "r") as f:
    abi = json.load(f)

with open(os.path.join(build_path, "contract_bytecode.txt"), "r") as f:
    bytecode = f.read()

# Step 4: Create contract instance and deploy
EnergyTrading = web3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = EnergyTrading.constructor().transact()
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Step 5: Save contract address
with open(os.path.join(build_path, "contract_address.txt"), "w") as f:
    f.write(tx_receipt.contractAddress)

print("✅ Contract deployed successfully.")
print("📍 Contract Address:", tx_receipt.contractAddress)
print("📁 Saved to: build/contract_address.txt")
