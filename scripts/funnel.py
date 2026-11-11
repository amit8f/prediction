"""Step 2 funnel from listing fields only (no results, no prices)."""
import json, re, sys, collections as C
from datetime import datetime, timedelta, timezone
listings, series_file, pull_day = sys.argv[1], sys.argv[2], sys.argv[3]
ser = {s['ticker']: s for s in json.load(open(series_file))['series']}
P = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
START, END = P('2025-01-01T00:00:00Z'), P(pull_day + 'T00:00:00Z')
seen, f, drop = {}, C.Counter(), C.Counter()
for line in open(listings):
    m = json.loads(line); seen[m['ticker']] = m
short = sum(int(l.split('\t')[1]) for l in open(listings + '.short'))
f['pulled (close >= 1 Jan 2025)'] = len(seen) + short
drop['open < 48h before scheduled close'] = short  # counted during the pull, not stored
kept = []
for m in seen.values():
    if m['market_type'] != 'binary': drop['not binary'] += 1; continue
    if not m.get('expected_expiration_time'): drop['no scheduled time'] += 1; continue
    sched = P(m['expected_expiration_time'])
    if not (START <= sched < END): drop['scheduled close outside 1 Jan 2025 .. pull day'] += 1; continue
    T = sched - timedelta(hours=24)
    if P(m['open_time']) > sched - timedelta(hours=48): drop['open < 48h before scheduled close'] += 1; continue
    if P(m['close_time']) <= T: drop['closed before snapshot T'] += 1; continue
    m['T'] = T; m['cat'] = ser.get(m['series'], {}).get('category', '?'); kept.append(m)
print('FUNNEL'); [print(f'  {k}: {v}') for k, v in f.items()]
[print(f'  dropped, {k}: {v}') for k, v in drop.most_common()]
print('  kept markets:', len(kept))
ev = C.defaultdict(set); mk = C.Counter()
for m in kept: ev[m['cat']].add(m['event_ticker']); mk[m['cat']] += 1
print('\nCATEGORY  events  markets')
for c, e in sorted(ev.items(), key=lambda x: -len(x[1])): print(f'  {c}: {len(e)}  {mk[c]}')
cat = max(ev, key=lambda c: len(ev[c])); K = [m for m in kept if m['cat'] == cat]
print('\nCHOSEN:', cat)
# ladder fingerprint across event tickers
thr = re.compile(r'(\$?\d[\d,]*\.?\d*\s*(°[CF]|%|or (higher|lower|more|above|below|fewer)|\+))|between \S+ and \S+|above \S+|below \S+', re.I)
fp = C.defaultdict(set)
for m in K: fp[(thr.sub('#', m['title'] or ''), m['T'].date())].add(m['event_ticker'])
multi = {k: v for k, v in fp.items() if len(v) > 1 and '#' in k[0]}
print('threshold templates spanning >1 event ticker on the same day (possible hidden ladders):', len(multi))
for k, v in sorted(multi.items(), key=lambda x: -len(x[1]))[:5]: print('   ', len(v), k[1], k[0][:80], sorted(v)[:3])
# event-level dates and split
evT = {}
for m in K: evT[m['event_ticker']] = min(evT.get(m['event_ticker'], m['T']), m['T'])
days = sorted(evT.values()); n = len(days)
split = days[int(n * 0.75)]
print(f'events {n}, distinct snapshot days {len({d.date() for d in days})}, markets {len(K)}, series {len({m["series"] for m in K})}')
print('first/last snapshot', days[0], days[-1])
print('holdout split: events with earliest snapshot >=', split, '->', sum(d >= split for d in days), 'holdout events,',
      len({d.date() for d in days if d >= split}), 'days')
fee = C.Counter((ser[m['series']]['fee_type'].replace('_with_maker_fees','').replace('_with_combo_maker_fees',''), ser[m['series']]['fee_multiplier']) for m in K)
print('fee (type, multiplier) by market:', fee.most_common())
top = C.Counter(m['series'] for m in K); ten = C.Counter()
for m in K: ten[m['series']]
print('top series by markets:', top.most_common(8))
# same real-world game listed under several series (winner, totals, props): key = event suffix
game = {m['event_ticker'].split('-', 1)[-1] for m in K}
print('distinct game keys (event ticker minus series prefix):', len(game), 'vs events', n)
