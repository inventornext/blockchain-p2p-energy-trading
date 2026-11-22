from solcx import compile_standard, install_solc
import json
import os

# Step 1: Read Solidity contract
contract_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contracts", "EnergyTrading.sol"))
with open(contract_path, "r") as file:
    source_code = file.read()

# Step 2: Install and select Solidity compiler version
install_solc("0.8.0")

# Step 3: Compile contract
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"EnergyTrading.sol": {"content": source_code}},
    "settings": {
        "outputSelection": {
            "*": {
                "*": ["abi", "evm.bytecode"]
            }
        }
    }
}, solc_version="0.8.0")

# Step 4: Extract ABI and Bytecode0.
contract_data = compiled_sol["contracts"]["EnergyTrading.sol"]["EnergyTrading"]
abi = contract_data["abi"]
bytecode = contract_data["evm"]["bytecode"]["object"]

# Dynamically get path to project root and create 'build' there
build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build"))
os.makedirs(build_path, exist_ok=True)

# Save ABI
with open(os.path.join(build_path, "contract_abi.json"), "w") as abi_file:
    json.dump(abi, abi_file)

# Save Bytecode
with open(os.path.join(build_path, "contract_bytecode.txt"), "w") as bytecode_file:
    bytecode_file.write(bytecode)

print("✅ Compilation successful. ABI and bytecode saved in 'build/' folder.")
