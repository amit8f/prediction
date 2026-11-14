"""PM4 Step 2: event, day, trading-life and pull-size counts from the universe file (listing fields only)."""
import json, gzip, sys, collections as C
from datetime import datetime, timezone
U = [json.loads(l) for l in gzip.open(sys.argv[1], 'rt')]
day = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%d')
def life_bin(s):
    for lim, n in ((16*60, '<=15 min'), (3600+60, '15-60 min'), (2*3600, '1-2 h'), (24*3600+60, '2-24 h'), (48*3600, '1-2 days')):
        if s <= lim: return n
    return '>2 days'
print('markets', len(U)); lb = C.Counter(life_bin(r['close']-r['open']) for r in U)
print('trading life (markets):', dict(lb))
# trading end vs scheduled close: how far apart
gap = C.Counter()
for r in U:
    g = r['exp'] - r['close']
    gap['exp == close' if g == 0 else 'exp after close <=5 min' if 0 < g <= 300 else 'exp after close 5min-1h' if 0 < g <= 3600 else 'exp after close >1h' if g > 3600 else 'close AFTER exp'] += 1
print('scheduled close minus trading end:', dict(gap))
print('can_close_early:', C.Counter(r['early'] for r in U))
# events
E = C.defaultdict(list)
for r in U: E[r['e']].append(r)
print('events', len(E))
ev_days = {e: day(min(x['snap'] for x in rs)) for e, rs in E.items()}
split_ev = sum(1 for rs in E.values() if len({day(x['snap']) for x in rs}) > 1)
print('events whose markets span >1 snapshot day', split_ev)
ser = C.Counter(); sm = C.Counter()
for e, rs in E.items(): ser[rs[0]['s']] += 1
for r in U: sm[r['s']] += 1
print('series', len(ser)); print('top series by events:')
for s, n in ser.most_common(25): print(f'  {s:22s} events {n:>7,} markets {sm[s]:>9,}')
ED = C.Counter(ev_days.values()); days = sorted(ED); print('snapshot days', len(days), days[0], days[-1])
k = len(days) - round(len(days) * 0.25); cut = days[k]
print('holdout from', cut, 'days', len(days) - k)
tr = [e for e, d in ev_days.items() if d < cut]; ho = [e for e, d in ev_days.items() if d >= cut]
mk = lambda es: sum(len(E[e]) for e in es)
print('training events', len(tr), 'markets', mk(tr), '| holdout events', len(ho), 'markets', mk(ho))
cross = sum(1 for rs in E.values() if min(day(x['snap']) for x in rs) < cut <= max(day(x['snap']) for x in rs))
print('events straddling the cut', cross)
# events per month
mo = C.Counter(d[:7] for d in ev_days.values()); print('events by month:', dict(sorted(mo.items())))
print('markets settled before 12 Sep 2026 (historical, 1 call each):', sum(r['hist'] for r in U))
print('markets per event: median', sorted(len(v) for v in E.values())[len(E)//2], 'max', max(len(v) for v in E.values()))
# (series, hour) slots
print('distinct (series, close hour) slots', len({(r['s'], r['exp']//3600) for r in U}))
json.dump({'holdout_from': cut, 'days': len(days), 'holdout_days': len(days)-k}, open(sys.argv[2], 'w'))
