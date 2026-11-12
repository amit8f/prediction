"""Step 2: pull Kalshi settled-market LISTING fields only, series by series.
No results, no prices: those fields are dropped before anything is saved.
Skips series whose frequency is hourly or fifteen_min (their markets live < 48h)."""
import json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
P = lambda x: datetime.fromisoformat(x.replace('Z', '+00:00'))
B = 'https://api.elections.kalshi.com/trade-api/v2'
KEEP = ['ticker','event_ticker','market_type','status','open_time','close_time',
        'expected_expiration_time','latest_expiration_time','can_close_early','title','strike_type']
START, CUTOFF = '2025-01-01T00:00:00Z', 1757635200  # historical cutoff 2026-09-12
def get(path):
    for i in range(7):
        try:
            return json.load(urllib.request.urlopen(B + path, timeout=90))
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError('failed ' + path)
def pages(path):
    cur = ''
    while True:
        d = get(path + ('&cursor=' + cur if cur else ''))
        ms = d.get('markets', [])
        yield ms
        cur = d.get('cursor') or ''
        if not cur or not ms: return
def short(m):
    # open < 48h before scheduled close: fails PM1 section 4, counted but not stored
    e = m.get('expected_expiration_time')
    return bool(e) and P(m['open_time']) > P(e) - timedelta(hours=48)
def one(s):
    rows, nshort = [], 0
    for base in (f'/markets?status=settled&series_ticker={s}&limit=1000&min_close_ts={CUTOFF}',
                 f'/historical/markets?series_ticker={s}&limit=1000'):
        for ms in pages(base):
            for m in ms:
                if (m.get('close_time') or '') >= START:
                    if short(m): nshort += 1; continue
                    r = {k: m.get(k) for k in KEEP}; r['series'] = s; rows.append(r)
    return s, rows, nshort
series = json.load(open(sys.argv[1]))['series']
todo = [x['ticker'] for x in series if x['frequency'] not in ('hourly', 'fifteen_min')]
print('series to pull', len(todo), 'skipped', len(series) - len(todo), flush=True)
n = ns = 0
with open(sys.argv[2], 'w') as f, open(sys.argv[2] + '.short', 'w') as g, ThreadPoolExecutor(6) as ex:
    futs = [ex.submit(one, t) for t in todo]
    for i, fu in enumerate(as_completed(futs)):
        s, rows, nshort = fu.result()
        for r in rows: f.write(json.dumps(r) + '\n')
        g.write(f'{s}\t{nshort}\n'); n += len(rows); ns += nshort
        if i % 500 == 0: print(i, n, ns, flush=True); f.flush(); g.flush()
print('done', n, ns, flush=True)
