"""PM3 Step 2 funnel: listing fields only (no prices, no result direction).
Usage: pm3_funnel.py listings.jsonl.gz [close_field]"""
import gzip, json, sys, collections
from datetime import datetime, timedelta, timezone
P = lambda x: datetime.fromisoformat(x.replace('Z', '+00:00'))
CF = sys.argv[2] if len(sys.argv) > 2 else 'expected_expiration_time'
LO, HI = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2026, 11, 14, tzinfo=timezone.utc)
H = timedelta(hours=1)
COMBO_SERIES = {'KXCITIESWEATHER'}  # each event is a pair of cities' highs on one day
def snap(o, c):
    s = c.replace(minute=0, second=0, microsecond=0) - 24 * H if c.minute or c.second else c - 24 * H
    first = o.replace(minute=0, second=0, microsecond=0) + H   # start of first full hour
    first_end = first + H
    return max(s, first_end)
drop = collections.Counter(); kept = []
for line in gzip.open(sys.argv[1], 'rt'):
    m = json.loads(line); drop['pulled'] += 1
    if not m.get(CF) or not m.get('open_time'): drop['no close/open time'] += 1; continue
    c, o = P(m[CF]), P(m['open_time'])
    if not (LO <= c < HI): drop['scheduled close outside 1 Jan 2025 to 13 Nov 2026'] += 1; continue
    if m['market_type'] != 'binary': drop['not binary'] += 1; continue
    if m['mve']: drop['combo (multivariate) market'] += 1; continue
    if m['res_kind'] == 'other': drop['result not yes/no and no settlement value'] += 1; continue
    if m['series'] in COMBO_SERIES: drop['combo series (city-pair weather)'] += 1; continue
    s = snap(o, c)
    if s >= c - H: drop['no time to rest an order (snapshot not before close minus 1h)'] += 1; continue
    if CF != 'close_time' and m.get('close_time') and s >= P(m['close_time']):
        drop['trading ends (close_time) before the snapshot'] += 1; continue
    kept.append((m['category'], m['series'], m['event_ticker'], s.date().isoformat(), m['res_kind']))
print('close field:', CF)
for k, v in drop.items(): print(f'{k:65s} {v:>9,}')
print(f"{'kept markets':65s} {len(kept):>9,}  (settlement value only: {sum(k[4]=='sv' for k in kept):,})")
ev = collections.defaultdict(set); days = collections.defaultdict(set); mk = collections.Counter(); ser = collections.defaultdict(set)
for cat, s, e, d, _ in kept:
    ev[cat].add(e); days[cat].add(d); mk[cat] += 1; ser[cat].add(s)
print(f"\n{'category':25s} {'events':>9s} {'markets':>10s} {'days':>5s} {'series':>6s}")
for cat in sorted(ev, key=lambda c: -len(ev[c])):
    print(f'{cat:25s} {len(ev[cat]):>9,} {mk[cat]:>10,} {len(days[cat]):>5} {len(ser[cat]):>6}')
json.dump([k[:4] for k in kept], open(sys.argv[1] + f'.kept.{CF}.json', 'w'))
