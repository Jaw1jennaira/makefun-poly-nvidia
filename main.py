import os, json, math
# Polymarket NVIDIA CEO forecaster: per-market volatility + drift from price history.
# q_tau(h) = clamp(x + drift*h/60 + z_tau*sigma*sqrt(h), 0, 1), 6 decimals.
# sigma: std of 1-min returns over last 24h, scaled 0.25 (returns are jump-dominated;
# raw std overstates typical movement), floor 0.001, cap 0.01.
# The scale 0.25 was chosen so the spread stays near the house baseline's 0.0025
# for quiet markets while widening for genuinely volatile ones.
# drift: linear-regression slope over last 12h, per hour, cap +-0.05.
INDIR = os.environ.get('MAKEFUN_INPUT_DIR', '/input')
OUTDIR = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]
SIGMA_SCALE = 0.25  # down-weight jump-dominated std
DRIFT_CAP = 0.05  # max |drift| in price units per hour
def price6(x):
    return round(min(1.0, max(0.0, x)) * 1e6) / 1e6 + 0.0
def forecast_market(prices, horizon):
    n = len(prices)
    if n == 0:
        raise ValueError('no prices')
    x = prices[-1]
    # sigma from 1-min returns, last 24h, scaled down (jump-dominated)
    w = prices[-1441:] if n > 1441 else prices
    rets = [w[i+1]-w[i] for i in range(len(w)-1)]
    if len(rets) >= 30:
        m = sum(rets)/len(rets)
        var = sum((r-m)**2 for r in rets)/(len(rets)-1)
        sigma = math.sqrt(max(var, 0.0)) * SIGMA_SCALE
    else:
        sigma = 0.0025
    sigma = min(max(sigma, 0.001), 0.01)
    # drift: linear regression over last 12h (720 min), per hour
    seg = prices[-721:] if n > 721 else prices
    k = len(seg)
    if k >= 60:
        xm = (k-1)/2.0
        ym = sum(seg)/k
        num = sum((i-xm)*(seg[i]-ym) for i in range(k))
        den = sum((i-xm)**2 for i in range(k))
        slope = num/den if den else 0.0
        drift = slope*60.0
    else:
        drift = 0.0
    drift = min(max(drift, -DRIFT_CAP), DRIFT_CAP)
    rows = []
    for h in range(1, horizon+1):
        s = math.sqrt(h)
        rows.append([price6(x + drift*h/60.0 + z*sigma*s) for z in Z])
    return rows
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    for fn in sorted(os.listdir(INDIR)):
        if not fn.endswith('.in'):
            continue
        with open(os.path.join(INDIR, fn)) as f:
            case = json.load(f)
        horizon = case['horizon_minutes']
        out = {'forecasts': []}
        for m in case['markets']:
            out['forecasts'].append({'id': m['id'], 'q': forecast_market(m['prices'], horizon)})
        outname = fn[:-3] + '.out'
        with open(os.path.join(OUTDIR, outname), 'w') as f:
            json.dump(out, f, separators=(',', ':'))
if __name__ == '__main__':
    main()
