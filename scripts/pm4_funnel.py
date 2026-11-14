"""PM4 Step 2: Financials funnel from listing fields only (no prices, no result direction).
Input: PM3 Step 2 slim listing (pulled 14 Nov 2026). Output: counts + universe file."""
import json, gzip, sys, collections as C
from datetime import datetime, timezone, timedelta
def ts(s): return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None
LO, HI = datetime(2025,1,1,tzinfo=timezone.utc), datetime(2026,11,14,tzinfo=timezone.utc)
CUT = datetime(2026,9,12,tzinfo=timezone.utc)
f = C.Counter(); keep = []; seen = set()
for line in gzip.open(sys.argv[1], 'rt'):
    m = json.loads(line)
    if m['category'] != 'Financials': continue
    f['pulled'] += 1
    if m['ticker'] in seen: f['dup ticker (live+historical)'] += 1; continue
    seen.add(m['ticker'])
    ex, op, cl = ts(m['expected_expiration_time']), ts(m['open_time']), ts(m['close_time'])
    if not ex or not (LO <= ex < HI): f['drop: scheduled close outside 1 Jan 2025-13 Nov 2026'] += 1; continue
    if m['mve']: f['drop: combo (mve)'] += 1; continue
    if m['market_type'] != 'binary' or m['res_kind'] == 'other': f['drop: not binary / no yes-no or settlement value'] += 1; continue
    if not op or not cl or cl <= op: f['drop: bad open/close times'] += 1; continue
    life = cl - op
    snap = (cl - timedelta(hours=24)) if life > timedelta(hours=48) else op + life / 2
    snap = snap.replace(second=0, microsecond=0)
    if cl <= snap: f['drop: trading over at snapshot'] += 1; continue
    if cl - snap < timedelta(minutes=2): f['drop: under 2 min between snapshot and trading end'] += 1; continue
    f['kept'] += 1
    keep.append(dict(t=m['ticker'], e=m['event_ticker'], s=m['series'], snap=int(snap.timestamp()),
                     open=int(op.timestamp()), close=int(cl.timestamp()), exp=int(ex.timestamp()),
                     early=m['can_close_early'], hist=cl < CUT))
for k, v in f.items(): print(f'{k:55s} {v:>10,}')
with gzip.open(sys.argv[2], 'wt') as g:
    for r in keep: g.write(json.dumps(r) + '\n')
