# Blockchain-Enabled P2P Energy Trading

[![Paper](https://img.shields.io/badge/Paper-SEGAN%202026-blue)](https://doi.org/10.1016/j.segan.2026.102606)
[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fj.segan.2026.102606-orange)](https://doi.org/10.1016/j.segan.2026.102606)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Code and data for the paper:

> **End-to-end blockchain-enabled peer-to-peer energy trading with storage, utility fallback, and grid impact analysis**
> Ganesh Kumar Pandey, Debapriya Das
> *Sustainable Energy, Grids and Networks*, Vol. 48, 102606, 2026 (Elsevier)
> [DOI: 10.1016/j.segan.2026.102606](https://doi.org/10.1016/j.segan.2026.102606) | [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2352467726004881)

---

## Overview

Rooftop solar and home batteries are turning passive consumers into prosumers who can trade energy locally. Most existing P2P trading studies stay conceptual, or treat market design separately from grid operation, storage behaviour and real settlement.

This work brings these together in one end-to-end framework:

- **Executable Ethereum smart contract** that enforces price bounds, manages energy offers and settles trades
- **Prosumer battery storage dispatch** built into the trading process
- **Utility fallback** with Time-of-Use pricing for unmatched demand and supply
- **Market-level analysis** of costs, revenues and grid import across scenarios

Physical energy exchange and utility transactions are modelled off-chain, while P2P settlement happens on-chain.

## Case study

- 24-hour local market with **20 prosumers** and **80 consumers** (100 Ethereum accounts)
- Real residential demand data (80 customers, hourly) and a measured rooftop solar profile
- Four scenarios:

| Script | Scenario |
|---|---|
| `simulate_trading_scenario_A.py` | Utility only: all consumers buy from the utility |
| `simulate_trading_scenario_B.py` | Prosumers sell surplus to the utility, consumers buy from the utility |
| `simulate_trading_scenario_C.py` | P2P trading on-chain, leftover energy traded with the utility |
| `simulate_trading_scenario_D.py` | P2P trading on-chain with prosumer battery storage and utility fallback |

## Key results (from the paper)

| Metric | P2P + storage vs. baseline |
|---|---|
| Total grid energy import | **36.56% lower** |
| Average consumer energy cost | **10.85% lower** |
| Prosumer revenue | **58.0% higher** |
| Gas overhead | Negligible |

## Repository structure

```
contracts/   EnergyTrading.sol (Solidity smart contract)
build/       Compiled ABI, bytecode and last deployed address
data/        Demand data (CSV), solar profile and generated demand file
scripts/     Account setup, data initialization, compile, deploy and the four scenario scripts
results/     Hourly logs and summaries for scenarios A to D
```

## Requirements

- Python 3.10 or newer
- [Node.js](https://nodejs.org/) (to run Ganache), or the Ganache desktop app
- Python packages: `pip install -r requirements.txt`

## Step-by-step reproduction

### 1. Clone and install

```bash
git clone https://github.com/inventornext/blockchain-p2p-energy-trading.git
cd blockchain-p2p-energy-trading
pip install -r requirements.txt
```

### 2. Start a local blockchain with 100 funded accounts

```bash
npx ganache --wallet.totalAccounts 100 --wallet.defaultBalance 1000 --server.port 7545
```

Ganache prints a 12-word mnemonic at startup. Keep this terminal open.

Using the Ganache desktop app instead? Create a workspace with **100 accounts** on port **7545**, and copy its mnemonic.

The scripts connect to `http://127.0.0.1:7545` by default. To use another address, set the `GANACHE_URL` environment variable.

### 3. Generate the account file

Open `scripts/account_loading_from_ganache.py` and paste your Ganache mnemonic in place of `YOUR_GANACHE_MNEMONIC`. Then run all scripts from the `scripts/` folder:

```bash
cd scripts
python account_loading_from_ganache.py
```

This writes `data/accounts.json`. Accounts 0 to 19 act as prosumers and 20 to 99 as consumers. The file holds private keys for your local test chain only, and is ignored by git.

### 4. Prepare the input data

```bash
python data_initialization.py
```

This maps the 80-customer demand data to your consumer accounts (`data/fixed_demand.json`) and loads the solar profile.

### 5. Compile and deploy the smart contract

```bash
python compile_contract.py     # optional: build/ already contains the compiled contract
python deploy_contract.py
```

`compile_contract.py` downloads solc 0.8.0 on its first run.

### 6. Run the four scenarios

```bash
python simulate_trading_scenario_A.py
python simulate_trading_scenario_B.py
python simulate_trading_scenario_C.py
python simulate_trading_scenario_D.py
```

Each script writes `scenario_X_summary.csv` and `scenario_X_hourly_log.csv` to `results/`.

### Notes on reproducibility

- Account addresses depend on your Ganache mnemonic, so they will differ from the provided result files. Totals for costs, revenues and energy do not depend on the addresses.
- Scenarios C and D add a small random term to the P2P price. The seed is fixed at 42 (set the `SEED` environment variable to change it), so reruns give identical results, while totals can differ very slightly from the provided CSVs.

## Citation

If you use this work, please cite:

```bibtex
@article{PANDEY2026102606,
  title   = {End-to-end blockchain-enabled peer-to-peer energy trading with storage, utility fallback, and grid impact analysis},
  author  = {Ganesh Kumar Pandey and Debapriya Das},
  journal = {Sustainable Energy, Grids and Networks},
  volume  = {48},
  pages   = {102606},
  year    = {2026},
  issn    = {2352-4677},
  doi     = {10.1016/j.segan.2026.102606},
  url     = {https://www.sciencedirect.com/science/article/pii/S2352467726004881}
}
```

## Keywords

Blockchain-enabled energy markets, Peer-to-peer energy trading, Prosumer storage, Utility fallback, Grid load impact, Smart grids

## Contact

**Ganesh Kumar Pandey**
PhD Scholar, Department of Electrical Engineering, IIT Kharagpur
GitHub: [@inventornext](https://github.com/inventornext)
Email: ganeshpandey.ee@gmail.com

For questions, collaboration or industry use, please get in touch by email.

## License

Released under the [MIT License](LICENSE).
