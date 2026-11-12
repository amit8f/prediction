"""Step 3: last hourly candle ending at or before T for every eligible market. Reads no result field."""
import json,sys,os,time,threading,urllib.request,urllib.error,collections as C
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
B='https://api.elections.kalshi.com/trade-api/v2'
P=lambda s: datetime.fromisoformat(s.replace('Z','+00:00'))
U=json.load(open(sys.argv[1])); which=sys.argv[2]; outf=sys.argv[3]; W=int(sys.argv[4]) if len(sys.argv)>4 else 8
HIST_BEFORE=int(P('2026-09-08T00:00:00Z').timestamp())
done=set()
if os.path.exists(outf):
    for l in open(outf): done.add(json.loads(l)['ticker'])
todo=[m for m in U if m['set']==which and m['ticker'] not in done]
print(which,'todo',len(todo),'done',len(done),flush=True)
lock=threading.Lock(); fo=open(outf,'a'); n=[0]; t0=time.time()
def get(u):
    for i in range(8):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (404,400): return None
            time.sleep(min(2**i,30))
        except Exception: time.sleep(min(2**i,30))
    return 'FAIL'
def val(c,k):
    x=c.get(k) or {}; v=x.get('close_dollars',x.get('close')); return None if v is None else float(v)
def last(cs,T):
    cs=[c for c in cs if c['end_period_ts']<=T]
    return cs[-1] if cs else None
def write(m,c,src):
    r={'ticker':m['ticker'],'T':m['T'],'src':src}
    if c: r.update(end=c['end_period_ts'],bid=val(c,'yes_bid'),ask=val(c,'yes_ask'))
    with lock:
        fo.write(json.dumps(r)+'\n'); n[0]+=1
        if n[0]%5000==0: fo.flush(); print(n[0],round(n[0]/(time.time()-t0),1),'/s',flush=True)
def single(m):
    st=int(P(m['open_time']).timestamp()); T=m['T']
    st=max(st,T-4900*3600)  # API window cap; anything older is reported as quote age
    q=f"candlesticks?start_ts={st}&end_ts={T}&period_interval=60"
    urls=[f"/historical/markets/{m['ticker']}/{q}",f"/series/{m['series']}/markets/{m['ticker']}/{q}"]
    if T>=HIST_BEFORE: urls.reverse()
    fail=False
    for u in urls:
        d=get(u)
        if d=='FAIL': fail=True; continue
        c=last((d or {}).get('candlesticks',[]),T)
        if c: return write(m,c,'single')
    write(m,None,'fail' if fail else 'none')
def batch(g):
    T=g[0]['T']; d=get(f"/markets/candlesticks?market_tickers={','.join(m['ticker'] for m in g)}&start_ts={T-7*86400}&end_ts={T}&period_interval=60")
    got={}
    if isinstance(d,dict):
        for x in d.get('markets',[]): got[x.get('market_ticker') or x.get('ticker')]=last(x.get('candlesticks',[]),T)
    for m in g:
        c=got.get(m['ticker'])
        if c: write(m,c,'batch')
        else: single(m)
hist=[m for m in todo if m['T']<HIST_BEFORE]; live=[m for m in todo if m['T']>=HIST_BEFORE]
byT=C.defaultdict(list)
for m in live: byT[m['T']].append(m)
groups=[v[i:i+50] for v in byT.values() for i in range(0,len(v),50)]
with ThreadPoolExecutor(W) as ex:
    list(ex.map(batch,groups)); list(ex.map(single,hist))
fo.close(); print('finished',which,n[0],flush=True)
