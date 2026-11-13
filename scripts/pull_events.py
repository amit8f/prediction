"""Step 3: mutually_exclusive flag per event (listing field, no outcomes)."""
import json,sys,time,urllib.request,urllib.error,urllib.parse
from concurrent.futures import ThreadPoolExecutor
B='https://api.elections.kalshi.com/trade-api/v2'
U=json.load(open(sys.argv[1])); need={m['event_ticker'] for m in U}; S=sorted({m['series'] for m in U})
def get(u):
    for i in range(8):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (400,404): return {}
            time.sleep(min(2**i,30))
        except Exception: time.sleep(min(2**i,30))
    return {}
def one(s):
    out={};c=''
    while True:
        d=get(f"/events?series_ticker={s}&limit=200"+(f"&cursor={urllib.parse.quote(c)}" if c else ''))
        for e in d.get('events',[]): out[e['event_ticker']]=e.get('mutually_exclusive')
        c=d.get('cursor')
        if not c or not d.get('events'): return out
R={}
with ThreadPoolExecutor(3) as ex:
    for o in ex.map(one,S): R.update(o)
json.dump({k:v for k,v in R.items() if k in need},open(sys.argv[2],'w'))
print('events found',len(set(R)&need),'of',len(need))
