"""PM3 Step 2: Kalshi settled-market LISTING fields only, series by series.
Every series except categories Sports, Crypto, Exotics, all frequencies.
No prices and no result direction are saved: `res_kind` only says whether the
result is a plain yes/no ('yn'), has a settlement value ('sv'), or neither."""
import json, sys, time, gzip, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
B = 'https://api.elections.kalshi.com/trade-api/v2'
START, CUTOFF = '2025-01-01T00:00:00Z', 1757635200  # live endpoint holds markets settled after 2026-09-12
KEEP = ['ticker', 'event_ticker', 'market_type', 'open_time', 'close_time',
        'expected_expiration_time', 'can_close_early', 'strike_type']
def get(path):
    for i in range(8):
        try:
            return json.load(urllib.request.urlopen(B + path, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): return {}
            time.sleep(min(2 ** i, 30))
        except Exception:
            time.sleep(min(2 ** i, 30))
    raise RuntimeError('failed ' + path)
def pages(path):
    cur = ''
    while True:
        d = get(path + ('&cursor=' + urllib.parse.quote(cur) if cur else ''))
        ms = d.get('markets', [])
        yield ms
        cur = d.get('cursor') or ''
        if not cur or not ms: return
def slim(m, s, cat):
    r = {k: m.get(k) for k in KEEP}
    r['series'], r['category'] = s, cat
    r['mve'] = bool(m.get('mve_collection_ticker'))
    res = m.get('result')
    r['res_kind'] = 'yn' if res in ('yes', 'no') else ('sv' if m.get('settlement_value_dollars') is not None else 'other')
    return r
def one(s, cat):
    rows = []
    for base in (f'/markets?status=settled&series_ticker={s}&limit=1000&min_close_ts={CUTOFF}',
                 f'/historical/markets?series_ticker={s}&limit=1000'):
        for ms in pages(base):
            for m in ms:
                if max(m.get('close_time') or '', m.get('expected_expiration_time') or '') >= START:
                    rows.append(slim(m, s, cat))
    return s, rows
series = json.load(gzip.open(sys.argv[1]))['series']
todo = [(x['ticker'], x['category']) for x in series if x['category'] not in ('Sports', 'Crypto', 'Exotics')]
print('series to pull', len(todo), flush=True)
n = 0; t0 = time.time()
with gzip.open(sys.argv[2], 'wt') as f, ThreadPoolExecutor(8) as ex:
    futs = [ex.submit(one, *t) for t in todo]
    for i, fu in enumerate(as_completed(futs)):
        s, rows = fu.result()
        for r in rows: f.write(json.dumps(r) + '\n')
        n += len(rows)
        if i % 250 == 0: print(i, n, round(time.time() - t0), flush=True)
print('done', n, round(time.time() - t0), flush=True)
