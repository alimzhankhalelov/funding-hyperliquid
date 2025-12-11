import requests
import pandas as pd
import time
from datetime import datetime
import os

# --- CONFIG ---
LEVERAGE = 10           # leverage
COLLATERAL = 10         # margin on perp ($)
POSITION_SIZE = COLLATERAL * LEVERAGE  # $100
SPOT_AMOUNT = POSITION_SIZE            # $100 on spot
TAKER_FEE_RATE = 0.00035  # ~0.035% (adjust as needed)

# Public Hyperliquid info API
API_URL = "https://api.hyperliquid.xyz/info"


def get_top_funding_coins(limit=5):
    """Fetch top coins by funding (descending).
    Returns a pandas.DataFrame with columns: symbol, funding_rate_hourly, price
    """
    payload = {"type": "metaAndAssetCtxs"}
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"API error: {e}")
        return pd.DataFrame()

    try:
        universe = data[0].get('universe', [])
        asset_ctxs = data[1]
    except Exception as e:
        print(f"Unexpected API response format: {e}")
        return pd.DataFrame()

    rows = []
    for i, asset in enumerate(universe):
        try:
            name = asset.get('name')
            funding = float(asset_ctxs[i].get('funding', 0))
            price = float(asset_ctxs[i].get('markPx', 0))
            rows.append({'symbol': name, 'funding_rate_hourly': funding, 'price': price})
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(by='funding_rate_hourly', ascending=False)
    return df.head(limit)


def simulate_trade(coin_data):
    """Simulate entering a short + spot hedge for one coin.
    coin_data may be a pandas.Series or dict with keys: symbol, price, funding_rate_hourly
    """
    if isinstance(coin_data, pd.Series):
        coin = coin_data.to_dict()
    else:
        coin = dict(coin_data)

    symbol = coin.get('symbol')
    price = float(coin.get('price', 0))
    funding_rate = float(coin.get('funding_rate_hourly', 0))

    print(f"\n--- SIMULATE ENTRY: {symbol} ---")
    print(f"Price: ${price}")
    print(f"Current funding (hourly): {funding_rate:.6%}")

    # 1) Short (Perp)
    short_size_usd = POSITION_SIZE
    short_tokens = short_size_usd / price if price else 0
    fee_short_entry = short_size_usd * TAKER_FEE_RATE

    # 2) Spot buy
    spot_size_usd = SPOT_AMOUNT
    spot_tokens = spot_size_usd / price if price else 0
    fee_spot_entry = spot_size_usd * TAKER_FEE_RATE

    total_spent = COLLATERAL + SPOT_AMOUNT
    total_fees = fee_short_entry + fee_spot_entry

    print(f"Open SHORT: ${short_size_usd} (x{LEVERAGE}) -> {short_tokens:.6f} tokens")
    print(f"Buy SPOT: ${spot_size_usd} -> {spot_tokens:.6f} tokens")
    print(f"Entry fees (spot+perp): ${total_fees:.4f}")

    expected_funding_profit = short_size_usd * funding_rate
    print(f"Expected funding payout per hour: ${expected_funding_profit:.4f}")

    net_pnl_1h = expected_funding_profit - total_fees
    print(f"P&L after 1 hour (w/ entry fees): ${net_pnl_1h:.4f}")

    if net_pnl_1h < 0:
        print("⚠️ WARNING: Fees consume first-hour profit; hold longer to be profitable.")
    else:
        print("✅ Profit in the first hour (uncommon).")

    # Return dict for possible logging
    return {
        'symbol': symbol,
        'price': price,
        'funding_rate_hourly': funding_rate,
        'expected_funding_1h': expected_funding_profit,
        'entry_fees': total_fees,
        'net_pnl_1h': net_pnl_1h,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def main():
    top_coins = get_top_funding_coins()
    if top_coins.empty:
        print("No data available from API.")
        return

    print("Top coins by funding:")
    print(top_coins[['symbol', 'funding_rate_hourly', 'price']].to_string(index=False))

    best = top_coins.iloc[0]
    result = simulate_trade(best)

    # Optional: append results to CSV for history
    out_file = os.environ.get('OUTPUT_CSV', 'results.csv')
    df = pd.DataFrame([result])
    header = not os.path.exists(out_file)
    df.to_csv(out_file, mode='a', header=header, index=False)
    print(f"Logged result to {out_file}")


if __name__ == '__main__':
    main()
