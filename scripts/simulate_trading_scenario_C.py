import json
import os
import random
from web3 import Web3
import pandas as pd

# --- Setup ---
ganache_url = os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")
w3 = Web3(Web3.HTTPProvider(ganache_url))
assert w3.is_connected(), "❌ Web3 not connected to Ganache!"

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
build_path = os.path.join(base_path, "build")
results_path = os.path.join(base_path, "results")
data_path = os.path.join(base_path, "data")

# Fixed seed so the small price noise is repeatable (override with SEED env var)
random.seed(int(os.environ.get("SEED", "42")))

with open(os.path.join(build_path, "contract_abi.json"), "r") as f:
    abi = json.load(f)
with open(os.path.join(build_path, "contract_address.txt"), "r") as f:
    contract_address = f.read().strip()
contract = w3.eth.contract(address=contract_address, abi=abi)

# Load data
with open(os.path.join(data_path, "fixed_demand.json"), "r") as f:
    consumer_demand = json.load(f)
with open(os.path.join(data_path, "fixed_solar_profile.json"), "r") as f:
    fixed_solar_profile = json.load(f)
with open(os.path.join(data_path, "accounts.json"), "r") as f:
    accounts = json.load(f)

prosumer_accounts = accounts[:20]
consumer_accounts = accounts[20:]

# --- Pricing Functions ---
total_hourly_demand = [sum(float(consumer_demand[c][h]) for c in consumer_demand) for h in range(24)]
min_d = min(total_hourly_demand)
max_d = max(total_hourly_demand)
normalized_demand = [(d - min_d) / (max_d - min_d) for d in total_hourly_demand]

def get_prosumer_price(hour):
    base, peak = 0.08, 0.26
    noise = random.uniform(-0.005, 0.005)
    return round(base + (peak - base) * normalized_demand[hour] + noise, 4)

def get_government_price(hour):
    base, peak = 0.12, 0.32
    return round(base + (peak - base) * normalized_demand[hour], 4)

# --- Parameters ---
ETH_USD = 2000
HOURS = 24
hourly_logs = []

# --- State Variables ---
energy_gen_prosumer = {acc["address"]: 0.0 for acc in prosumer_accounts}
energy_supplied_pTg = {acc["address"]: 0.0 for acc in prosumer_accounts}
energy_supplied_pTc = {acc["address"]: 0.0 for acc in prosumer_accounts}
grid_energy_supplied_to_customers = {acc["address"]: 0.0 for acc in consumer_accounts}
revenue_rec_pFg = {acc["address"]: 0.0 for acc in prosumer_accounts}
revenue_rec_pFc = {acc["address"]: 0.0 for acc in prosumer_accounts}
revenue_paid_c2g = {acc["address"]: 0.0 for acc in consumer_accounts}
revenue_paid_c2p = {acc["address"]: 0.0 for acc in prosumer_accounts}

# --- Simulation ---
print("\n🔁 Starting 24-hour simulation (Scenario C: sell leftover to govt)...\n")

eth_transferred = 0.0
remaining=0


for hour in range(HOURS):
    print(f"🕒 Hour {hour}...")
    gov_price = get_government_price(hour)

    # Step 1: Initialize hourly prosumer supply
    prosumer_supply = {}
    for prosumer in prosumer_accounts:
        addr = prosumer["address"]
        gen = fixed_solar_profile[hour]
        prosumer_supply[addr] = gen
        energy_gen_prosumer[addr] += gen

    # Step 2: Loop over consumers
    for consumer in consumer_accounts:
        c_addr = consumer["address"]
        c_key = consumer["private_key"]
        demand = float(consumer_demand[c_addr][hour])
        remaining = demand

        sorted_prosumers = sorted(prosumer_accounts, key=lambda p: get_prosumer_price(hour))

        for prosumer in sorted_prosumers:
            p_addr = prosumer["address"]
            p_key = prosumer["private_key"]
            price = get_prosumer_price(hour)
            supply = prosumer_supply[p_addr]


            trade = min(supply, remaining)
            if trade <= 0:
                continue

            usd_cost = trade * price
            eth_cost = usd_cost / ETH_USD

            try:
                txn = {
                    "from": c_addr,
                    "to": p_addr,
                    "value": w3.to_wei(eth_cost, 'ether'),
                    "gas": 21000,
                    "gasPrice": w3.to_wei('1', 'gwei'),
                    "nonce": w3.eth.get_transaction_count(c_addr),
                }
                signed_txn = w3.eth.account.sign_transaction(txn, c_key)
                w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                w3.eth.wait_for_transaction_receipt(signed_txn.hash)

                # Update state
                prosumer_supply[p_addr] -= trade
                remaining -= trade
                revenue_rec_pFc[p_addr] += usd_cost
                revenue_paid_c2p[p_addr] += usd_cost
                energy_supplied_pTc[p_addr] += trade
                eth_transferred += eth_cost

                hourly_logs.append({
                    "hour": hour,
                    "consumer_address": c_addr,
                    "demand_kwh": trade,
                    "from_prosumer": p_addr,
                    "usd_cost": usd_cost,
                    "price_usd": price,
                    "energy_from_prosumer_to_customer": trade,
                    "eth_paid": round(eth_cost, 6),
                    "tx_hash": signed_txn.hash.hex()
                })

            except Exception as e:
                print(f"⚠️ ETH transfer failed: {e}")
                continue

            if remaining <= 0:
                break

        # Step 3: Government supplies unmet demand
        if remaining > 0:
            usd_cost = remaining * gov_price
            revenue_paid_c2g[c_addr] += usd_cost
            grid_energy_supplied_to_customers[c_addr] += remaining

            hourly_logs.append({
                "hour": hour,
                "consumer_address": c_addr,
                "demand_kwh": remaining,
                "usd_cost": usd_cost,
                "energy_from_gov": remaining,
                "price_usd": gov_price
            })

    # Step 4: Sell leftover energy to government at 50% rate
    for prosumer in prosumer_accounts:
        p_addr = prosumer["address"]
        leftover = prosumer_supply[p_addr]
        if leftover > 0:
            payout = leftover * 0.5 * gov_price
            revenue_rec_pFg[p_addr] += payout
            energy_supplied_pTg[p_addr] += leftover

            hourly_logs.append({
                "hour": hour,
                "from_prosumer": p_addr,

                "energy_from_prosumer": leftover,
                "Revenue_received_prosumer_govt":payout,
            })


# --- Summary ---
print("\n✅ Scenario C Simulation complete.\n")
print(f" Energy generated by Prosumers: {sum(energy_gen_prosumer.values()):.2f} kWh")
print(f" Energy supplied by Prosumers to government: {sum(energy_supplied_pTg.values()):.2f} kWh")
print(f" Energy supplied by Prosumers to customers: {sum(energy_supplied_pTc.values()):.2f} kWh")
print(f" Grid Energy supplied to customers: {sum(grid_energy_supplied_to_customers.values()):.2f} kWh")
print(f" Revenue received by prosumers from government: {sum(revenue_rec_pFg.values()):.2f} USD")
print(f" Revenue received by prosumers from customers: {sum(revenue_rec_pFc.values()):.2f} USD")
print(f" Revenue paid by customers to government: {sum(revenue_paid_c2g.values()):.2f} USD")
print(f" Total ETH transferred in P2P trades: {round(eth_transferred, 6)} ETH")

# --- Save Summary Results ---
summary = []

# Consumers: total USD paid to government
for acc in consumer_accounts:
    summary.append({
        "address": acc["address"],
        "role": "consumer",
        "total_cost_usd": round(revenue_paid_c2g[acc["address"]], 2)
    })

# Prosumers: total USD received from government + customers
for acc in prosumer_accounts:
    total_revenue = revenue_rec_pFg[acc["address"]] + revenue_rec_pFc[acc["address"]]
    summary.append({
        "address": acc["address"],
        "role": "prosumer",
        "total_revenue_usd": round(total_revenue, 2)
    })

# Save to CSV
pd.DataFrame(summary).to_csv(os.path.join(results_path, "scenario_C_summary.csv"), index=False)

# --- Save Hourly Logs ---
pd.DataFrame(hourly_logs).to_csv(os.path.join(results_path, "scenario_C_hourly_log.csv"), index=False)

print("\n📁 Results saved to:")
print("   scenario_C_summary.csv")
print("   scenario_C_hourly_log.csv")
