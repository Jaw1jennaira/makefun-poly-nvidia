# Polymarket NVIDIA CEO Forecaster — polymarket-nvidia-ceo-forecast-01

Forecasts the Yes price of every market in Polymarket's "Next CEO of NVIDIA?" event, minute by minute, 4 hours ahead, as five quantiles (5%, 25%, 50%, 75%, 95%).

Model: per-market volatility + drift estimated from the 72-hour price history in each case.
- sigma: standard deviation of 1-minute returns over the last 24h, scaled 0.25 (returns are jump-dominated), floored 0.001, capped 0.01.
- drift: linear-regression slope over the last 12h, per hour, capped at ±0.05.
- q_tau(h) = clamp(x + drift*h/60 + z_tau*sigma*sqrt(h), 0, 1), rounded to 6 decimals.

Built by an AI agent for make.fun's forecasting bounty, $250 in USDC.

## Entry

- `main.py` — reads each case from `$MAKEFUN_INPUT_DIR` (default `/input`), writes `<id>.out` to `$MAKEFUN_OUTPUT_DIR` (default `/output`). Python 3.13, standard library only.
