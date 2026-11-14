"""PM2 test: pull Kalshi 1-minute yes_bid/yes_ask candles for every kept market in one set.
Reads no result field. Saves per market: [minutes before close, bid close, ask close] per candle.
Usage: pm2_pull_quotes.py train|hold OUT.txt [threads]"""
import json,sys,os,time,gzip,random,threading,urllib.request,urllib.error,collections as C
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
B='https://api.elections.kalshi.com/trade-api/v2'
SPLIT='2026-05-27'; LIVE_FROM='2026-09-13'   # markets settled before ~12 Sep 2026 sit in /historical only
which,outf=sys.argv[1],sys.argv[2]; W=int(sys.argv[3]) if len(sys.argv)>3 else 40
ts=lambda s:int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
done=set()
if os.path.exists(outf):
    for l in open(outf):
        try: done.add(json.loads(l)['t'])
        except Exception: pass
todo=[]
for l in gzip.open('/mnt/project-files/data/pm2/pm2_listings_slim.jsonl.gz'):
    m=json.loads(l)
    if (m['close_time']>=SPLIT)==(which=='hold') and m['ticker'] not in done: todo.append(m)
if os.environ.get('LIM'): random.seed(0); todo=random.sample(todo,int(os.environ['LIM']))
print(which,'todo',len(todo),'done',len(done),flush=True)
lock=threading.Lock(); fo=open(outf,'a'); n=[0]; t0=time.time()
def get(u):
    for i in range(9):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (400,404): return None
            time.sleep(min(2**i,20))
        except Exception: time.sleep(min(2**i,20))
    return 'FAIL'
def px(c,k):
    x=c.get(k) or {}; v=x.get('close',x.get('close_dollars'))
    return None if v is None else round(float(v),4)
def window(m):
    E=ts(m['close_time']); S=ts(m['open_time']) if m['series'].endswith('15M') else E-3600
    return max(S,E-3600)-60,E
def write(m,cs,src):
    E=ts(m['close_time'])
    r={'t':m['ticker'],'s':src,'c':[[(E-c['end_period_ts'])//60,px(c,'yes_bid'),px(c,'yes_ask')] for c in (cs or []) if c['end_period_ts']<=E]}
    with lock:
        fo.write(json.dumps(r,separators=(',',':'))+'\n'); n[0]+=1
        if n[0]%20000==0: fo.flush(); print(n[0],round(n[0]/(time.time()-t0),1),'/s',flush=True)
def single(m):
    S,E=window(m); q=f"candlesticks?start_ts={S}&end_ts={E}&period_interval=1"
    us=[f"/historical/markets/{m['ticker']}/{q}",f"/series/{m['series']}/markets/{m['ticker']}/{q}"]
    if m['close_time']>=LIVE_FROM: us.reverse()
    fail=False
    for u in us:
        d=get(u)
        if d=='FAIL': fail=True; continue
        if d is not None and 'candlesticks' in d: return write(m,d['candlesticks'],'single')
    write(m,None,'fail' if fail else 'none')
def batch(g):
    S,E=window(g[0]); d=get(f"/markets/candlesticks?market_tickers={','.join(m['ticker'] for m in g)}&start_ts={S}&end_ts={E}&period_interval=1")
    got={}
    if isinstance(d,dict):
        for x in d.get('markets',[]): got[x.get('market_ticker') or x.get('ticker')]=x.get('candlesticks')
    for m in g:
        if got.get(m['ticker']) is not None: write(m,got[m['ticker']],'batch')
        else: single(m)
live=[m for m in todo if m['close_time']>=LIVE_FROM]; hist=[m for m in todo if m['close_time']<LIVE_FROM]
byE=C.defaultdict(list)
for m in live: byE[(m['event_ticker'],m['open_time'] if m['series'].endswith('15M') else '')].append(m)
groups=[v[i:i+50] for v in byE.values() for i in range(0,len(v),50)]
with ThreadPoolExecutor(W) as ex:
    list(ex.map(batch,groups)); list(ex.map(single,hist))
fo.close(); print('finished',which,n[0],round(time.time()-t0),'s',flush=True)
