import json
import os
import pandas as pd

# =========================================================
# Base Path
# =========================================================
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# =========================================================
# Load Ethereum Accounts
# =========================================================
accounts_path = os.path.join(base_path, "data", "accounts.json")

with open(accounts_path, "r") as f:
    accounts = json.load(f)

# =========================================================
# Role Assignment
# =========================================================
prosumer_accounts = accounts[:20]
consumer_accounts = accounts[20:]

# =========================================================
# Data Directory
# =========================================================
data_path = os.path.join(base_path, "data")
os.makedirs(data_path, exist_ok=True)

# =========================================================
# Fixed Consumer Demand
# =========================================================
fixed_demand_path = os.path.join(data_path, "fixed_demand.json")

# Rebuild the demand file if it was made with a different set of accounts
current_consumers = [acc["address"] for acc in consumer_accounts[:80]]
if os.path.exists(fixed_demand_path):
    with open(fixed_demand_path, "r") as f:
        saved_consumers = list(json.load(f).keys())
    if saved_consumers != current_consumers:
        print("♻️  Accounts changed, rebuilding fixed demand from CSV...")
        os.remove(fixed_demand_path)

if os.path.exists(fixed_demand_path):

    print("🔁 Loading fixed consumer demand from file...")

    with open(fixed_demand_path, "r") as f:
        consumer_demand = json.load(f)

    # Convert values to float
    consumer_demand = {
        k: [float(val) for val in v]
        for k, v in consumer_demand.items()
    }

else:

    print("📊 Loading real consumer load data from CSV...")

    # CSV File Path
    csv_demand_path = os.path.join(
        data_path,
        "load_profile_dec1_2013_80_customers_hourly.csv"
    )

    # Read CSV
    df_load = pd.read_csv(csv_demand_path)

    # Convert timestamp column
    df_load['timestamp'] = pd.to_datetime(df_load['timestamp'])

    # First 80 consumer addresses
    consumer_addresses = [
        acc["address"]
        for acc in consumer_accounts[:80]
    ]

    # CSV columns for 80 customers
    csv_columns = df_load.columns[1:81]

    # Build demand dictionary
    consumer_demand = {
        consumer_addresses[i]: df_load[csv_columns[i]].tolist()
        for i in range(len(consumer_addresses))
    }

    # Save fixed demand
    with open(fixed_demand_path, "w") as f:
        json.dump(consumer_demand, f, indent=2)

    print("✅ Fixed consumer demand saved.")

# =========================================================
# Fixed Solar Generation Profile
# =========================================================
fixed_solar_path = os.path.join(
    data_path,
    "fixed_solar_profile.json"
)

if os.path.exists(fixed_solar_path):

    print("🔁 Loading real solar generation profile from file...")

    with open(fixed_solar_path, "r") as f:
        fixed_solar_profile = json.load(f)

    # Convert to float
    fixed_solar_profile = [
        float(val)
        for val in fixed_solar_profile
    ]

else:

    print("🆕 Saving provided July 24 solar generation data...")

    fixed_solar_profile = [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.125,
        0.5,
        1.875,
        3.125,
        3.375,
        4.375,
        5.0,
        5.0,
        4.625,
        4.0,
        2.5,
        1.875,
        0.625,
        0.25,
        0.0,
        0.0,
        0.0
    ]

    # Save solar profile
    with open(fixed_solar_path, "w") as f:
        json.dump(fixed_solar_profile, f, indent=2)

    print("✅ Fixed solar profile saved.")

# =========================================================
# Summary
# =========================================================
print("\n======================================")
print("✅ Data initialization completed.")
print("======================================")
print(f"Consumers Loaded : {len(consumer_demand)}")
print(f"Solar Profile hrs: {len(fixed_solar_profile)}")
print("======================================")