# funding-hyperliquid

Funding strategy demo for Hyperliquid: short-perp + long-spot hedge simulator.

Overview
- Script: `main.py` — fetches public info from Hyperliquid and simulates a short+spot hedge using funding rates.
- Workflow: `.github/workflows/trade.yml` — runs hourly (55th minute) via GitHub Actions.

Quick start (local)
1. Create and activate a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies and run:

```bash
pip install -r requirements.txt
python main.py
```

GitHub Actions
- The repository includes an example workflow at `.github/workflows/trade.yml` that runs hourly (UTC :55).
- No API keys are required for this script because it uses Hyperliquid's public Info API (`https://api.hyperliquid.xyz/info`).

Notes & safety
- This project is a simulation only — it does NOT place live orders.
- Monitor API rate limits and adjust frequency accordingly.
- Results are appended to `results.csv` by default. You can change this via the `OUTPUT_CSV` env var.

Next steps
- If you want, I can commit and push additional changes or add optional real-trading scaffolding (kept separate and disabled by default).
