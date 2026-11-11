"""Step 2: quote coverage on a random sample of TRAINING-period sports markets.
Reads only candles ending at or before the snapshot T. No results are read."""
import json, random, sys, time, urllib.request, collections as C
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
B = 'https://api.elections.kalshi.com/trade-api/v2'
P = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
listings, series_file, split, n = sys.argv[1], sys.argv[2], P(sys.argv[3]), int(sys.argv[4])
ser = {s['ticker']: s['category'] for s in json.load(open(series_file))['series']}
rows = {}
for l in open(listings):
    m = json.loads(l)
    if ser.get(m['series']) != 'Sports' or m['market_type'] != 'binary' or not m.get('expected_expiration_time'): continue
    T = P(m['expected_expiration_time']) - timedelta(hours=24)
    if P(m['close_time']) <= T or T >= split or T < P('2025-01-02T00:00:00Z'): continue
    m['T'] = int(T.timestamp()); rows[m['ticker']] = m
random.seed(20261111); sample = random.sample(sorted(rows), n)
def get(u):
    for i in range(5):
        try: return json.load(urllib.request.urlopen(B + u, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 ** i)
        except Exception: time.sleep(2 ** i)
def one(t):
    m = rows[t]; q = f'candlesticks?start_ts={m["T"]-6*3600}&end_ts={m["T"]}&period_interval=60'
    for u in (f'/series/{m["series"]}/markets/{t}/{q}', f'/historical/markets/{t}/{q}'):
        d = get(u)
        cs = [c for c in (d or {}).get('candlesticks', []) if c['end_period_ts'] <= m['T']]
        if cs:
            c = cs[-1]; g = lambda side: c.get(side, {}).get('close_dollars') or c.get(side, {}).get('close')
            return m, g('yes_bid'), g('yes_ask'), float(c.get('volume_fp') or c.get('volume') or 0)
    return m, None, None, None
f = C.Counter(); spreads = []; buckets = C.Counter(); persr = C.Counter()
with ThreadPoolExecutor(5) as ex:
    for m, b, a, v in ex.map(one, sample):
        f['sampled'] += 1
        if b is None or a is None: f['no candle or no quote in the 6h before T'] += 1; continue
        b, a = float(b), float(a)
        if b <= 0 or a >= 1: f['bid 0 or ask 1.00 (empty book)'] += 1; continue
        mid = (a + b) / 2
        if mid == 0.5: f['mid exactly 0.50'] += 1; continue
        entry = a if mid > 0.5 else 1 - b
        f['tradeable quote'] += 1; spreads.append(a - b)
        k = '0.70-0.80' if 0.70 <= entry < 0.80 else '0.80-0.90' if 0.80 <= entry < 0.90 else '0.90-0.97' if 0.90 <= entry <= 0.97 else 'outside buckets'
        buckets[k] += 1
        if k != 'outside buckets': persr[m['series']] += 1
print('universe (training-period sports markets alive at T):', len(rows))
for k, v in f.items(): print(f'  {k}: {v}')
spreads.sort(); q = lambda p: round(spreads[int(p * (len(spreads) - 1))], 3)
print('spread at T, median / 75th / 90th pct:', q(.5), q(.75), q(.9))
print('favourite entry price bucket:', dict(buckets))
print('in-bucket by series (top 8):', persr.most_common(8))
