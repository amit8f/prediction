"""PM2 Step 2: Coinbase public 1-minute candles (time = START of the minute, verified 13 Nov 2026).
Output per coin: gzip CSV of start_ts,open,high,low,close,volume. Missing minutes are simply absent."""
import gzip, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
START = 1735682400  # 2024-12-31 22:00 UTC, so 1 Jan 2025 has 60+ minutes of history
END = int(sys.argv[2]) if len(sys.argv) > 2 else int(time.time()) // 60 * 60
def get(u):
    for i in range(8):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'research-script'}), timeout=60))
        except Exception:
            time.sleep(min(2 ** i, 60))
    raise RuntimeError(u)
def iso(t): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))
def chunk(args):
    pid, a = args
    time.sleep(0.4)  # stay well under the public rate limit (4 threads x ~2/s)
    return get(f'https://api.exchange.coinbase.com/products/{pid}/candles?granularity=60&start={iso(a)}&end={iso(a + 299 * 60)}')
for coin in ['BTC', 'ETH', 'SOL', 'XRP']:
    pid = coin + '-USD'; rows = {}
    jobs = [(pid, a) for a in range(START, END, 300 * 60)]
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(chunk, jobs):
            for c in r:
                if START <= c[0] < END: rows[c[0]] = c
    with gzip.open(f'{sys.argv[1]}/coinbase_{coin}_1m.csv.gz', 'wt') as f:
        f.write('start_ts,low,high,open,close,volume\n')
        for t in sorted(rows): f.write(','.join(str(x) for x in rows[t]) + '\n')
    print(coin, len(rows), 'minutes of', (END - START) // 60, flush=True)
