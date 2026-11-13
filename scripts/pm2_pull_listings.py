"""PM2 Step 2: pull settled-market LISTING fields for the eight PM2 series.
No prices and no result direction are saved. Only a flag saying whether the result
is a plain yes/no (for the funnel), and whether the rules-text time equals close_time."""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
B = 'https://api.elections.kalshi.com/trade-api/v2'
SERIES = ['KXBTCD','KXETHD','KXSOLD','KXXRPD','KXBTC15M','KXETH15M','KXSOL15M','KXXRP15M']
KEEP = ['ticker','event_ticker','status','open_time','close_time','expected_expiration_time',
        'floor_strike','cap_strike','strike_type','can_close_early']
NY = ZoneInfo('America/New_York')
MON = {m: i+1 for i, m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}
RX = re.compile(r'(?:before|at) (\d{1,2})(?::(\d\d))? ?([AP]M) E[DS]T on ([A-Za-z]+) (\d{1,2}), (\d{4})')
def get(path):
    for i in range(7):
        try: return json.load(urllib.request.urlopen(B + path, timeout=90))
        except Exception: time.sleep(2 ** i)
    raise RuntimeError('failed ' + path)
def rules_time(txt):
    # the first "before|at <time> on <date>" is the settlement time (15M rules name the open second)
    ms = RX.findall(txt or '')
    if not ms: return None
    h, mi, ap, mon, d, y = ms[0]
    h = int(h) % 12 + (12 if ap == 'PM' else 0)
    t = datetime(int(y), MON[mon[:3].lower()], int(d), h, int(mi or 0), tzinfo=NY)
    return t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def one(s):
    seen, rows = set(), []
    for base in (f'/markets?status=settled&series_ticker={s}&limit=1000',
                 f'/historical/markets?series_ticker={s}&limit=1000'):
        cur = ''
        while True:
            d = get(base + ('&cursor=' + cur if cur else ''))
            for m in d.get('markets', []):
                if m['ticker'] in seen: continue
                seen.add(m['ticker'])
                r = {k: m.get(k) for k in KEEP}; r['series'] = s
                r['yes_no'] = m.get('result') in ('yes', 'no')
                r['rules_time'] = rules_time(m.get('rules_primary'))
                rows.append(r)
            cur = d.get('cursor') or ''
            if not cur or not d.get('markets'): break
    print(s, len(rows), flush=True)
    return rows
with open(sys.argv[1], 'w') as f, ThreadPoolExecutor(8) as ex:
    for rows in ex.map(one, SERIES):
        for r in rows: f.write(json.dumps(r) + '\n')
print('done', flush=True)
