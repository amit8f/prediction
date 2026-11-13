"""PM2 Step 2 funnel: listing fields and spot TIMESTAMPS only. No price is read."""
import gzip, json, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
import numpy as np
D = sys.argv[1]
P = lambda s: int(datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp())
day = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%d')
LO, HI = P('2025-01-01T00:00:00Z'), P('2026-11-13T00:00:00Z')  # scheduled close from 1 Jan 2025 to the pull day (13 Nov, exclusive)
# spot presence by minute, as a prefix sum, per coin (timestamps only)
S0 = 1735682400; have = {}
for c in ['BTC', 'ETH', 'SOL', 'XRP']:
    ts = np.loadtxt(gzip.open(f'{D}/coinbase_{c}_1m.csv.gz', 'rt'), delimiter=',', skiprows=1, usecols=0, dtype=np.int64)
    a = np.zeros((HI + 86400 - S0) // 60 + 2, dtype=np.int32); a[(ts - S0) // 60] = 1
    have[c] = np.concatenate([[0], np.cumsum(a)])
def full(c, a, b):  # spot candles starting in [a, b] all present?
    i, j = (a - S0) // 60, (b - S0) // 60 + 1
    return have[c][j] - have[c][i] == j - i
f = Counter(); ser = defaultdict(Counter); ev = {}; evdays = defaultdict(set); dur = Counter(); exp = Counter(); late = Counter()
for line in open(f'{D}/listings.jsonl'):
    m = json.loads(line); s = m['series']; f['pulled'] += 1; ser[s]['pulled'] += 1
    hourly = not s.endswith('15M'); coin = s[2:5]
    ct = P(m['close_time']); op = P(m['open_time'])
    if not (LO <= ct < HI): f['drop: close outside 1 Jan 2025 to pull day'] += 1; continue
    if m['rules_time'] is None: f['check: rules time not parsed'] += 1
    elif P(m['rules_time']) != ct: f['check: rules time != close_time'] += 1
    exp[(P(m['expected_expiration_time']) - ct) // 60 if m.get('expected_expiration_time') else None] += 1
    if not m['yes_no']: f['drop: result not yes/no (voided or other)'] += 1; continue
    if hourly and m.get('floor_strike') is None: f['drop: no strike'] += 1; continue
    dur[('H' if hourly else '15M', (ct - op) // 60)] += 1
    first = ct - 55 * 60 if hourly else op + 60
    last = ct - 120
    if last < first: f['drop: no signal minutes'] += 1; continue
    if hourly and op > first: late['opened after first signal minute'] += 1
    need_a = first - 61 * 60 if hourly else min(first - 61 * 60, op - 60)
    if not full(coin, need_a, last - 60):
        # count minutes that still have a full 60-minute spot history; drop market only if none
        ok = any(full(coin, t - 61 * 60, t - 60) for t in range(first, last + 1, 60)) and (hourly or full(coin, op - 60, op - 60))
        if not ok: f['drop: no signal minute with full spot history'] += 1; continue
        f['kept with some spot gaps (those minutes skipped)'] += 1
    f['kept markets'] += 1; ser[s]['kept'] += 1
    e = m['event_ticker']; ev[e] = (s, first); d = day(first); ser[s + '_days'][d] = 1; evdays[d].add(e)
for e, (s, first) in ev.items(): ser[s]['events'] += 1
print('FUNNEL'); [print(f'  {k}: {v:,}') for k, v in f.items()]
print('expected_expiration - close (min):', dict(exp.most_common(5)))
print('market length (min), top:', dur.most_common(8)); print(dict(late))
print('PER SERIES  pulled  kept  events  days  first  last')
for s in ['KXBTCD','KXETHD','KXSOLD','KXXRPD','KXBTC15M','KXETH15M','KXSOL15M','KXXRP15M']:
    ds = sorted(ser[s + '_days']); print(f'  {s} {ser[s]["pulled"]:,} {ser[s]["kept"]:,} {ser[s]["events"]:,} {len(ds)} {ds[0] if ds else "-"} {ds[-1] if ds else "-"}')
days = sorted(evdays); n = len(days); k = n - round(n * 0.25); split = days[k]
hold = [d for d in days if d >= split]; train = days[:k]
ne = lambda ds: sum(len(evdays[d]) for d in ds)
print(f'DAYS {n} ({days[0]} to {days[-1]}); events {len(ev):,}')
print(f'HOLDOUT from {split}: {len(hold)} days, {ne(hold):,} events; TRAIN {len(train)} days, {ne(train):,} events')
hrs = {(ev[e][1] // 3600) for e in ev}; print('distinct first-signal hours across coins:', len(hrs))
by_m = Counter(d[:7] for d in days for _ in evdays[d]); print('events by month:', dict(sorted(by_m.items())))
