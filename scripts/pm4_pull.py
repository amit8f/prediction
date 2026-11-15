"""PM4 Step 3 pull: per Financials market, the latest 1-minute yes_bid/yes_ask candle ending at or before the
snapshot (within 30 min), then, if the quote can carry an order (0.03 <= ask <= 0.97, spread >= 2c, needed for the
rule and the random control), the trade tape from the snapshot to trading end. Reads no result field.
Resumable: skips tickers already in OUT. Usage: pm4_pull.py uni.jsonl train|hold OUT.jsonl [threads]"""
import json,sys,os,time,threading,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor
B='https://api.elections.kalshi.com/trade-api/v2'
uf,which,outf=sys.argv[1:4]; W=int(sys.argv[4]) if len(sys.argv)>4 else 40
done=set()
if os.path.exists(outf):
    for l in open(outf):
        try: done.add(json.loads(l)['t'])
        except Exception: pass
todo=[m for m in map(json.loads,open(uf)) if m['sp']==which and m['t'] not in done]
print(which,'todo',len(todo),'done',len(done),flush=True)
lock=threading.Lock(); fo=open(outf,'a'); n=[0]; err=[0]; t0=time.time()
def get(u):
    for i in range(10):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (400,404): return None
            err[0]+=1; time.sleep(min(2**i,30))
        except Exception: err[0]+=1; time.sleep(min(2**i,30))
    return 'FAIL'
def px(c,k):
    x=c.get(k) or {}; v=x.get('close',x.get('close_dollars'))
    return None if v is None else round(float(v),4)
def quote(m):
    q=f"candlesticks?start_ts={m['snap']-1800}&end_ts={m['snap']}&period_interval=1"
    us=[f"/historical/markets/{m['t']}/{q}",f"/series/{m['s']}/markets/{m['t']}/{q}"]
    fail=False
    for i in ((0,1) if m['hist'] else (1,0)):
        d=get(us[i])
        if d=='FAIL': fail=True; continue
        if d and d.get('candlesticks'):
            cs=[c for c in d['candlesticks'] if m['snap']-1800<=c['end_period_ts']<=m['snap'] and px(c,'yes_bid') is not None and px(c,'yes_ask') is not None]
            if cs: c=max(cs,key=lambda c:c['end_period_ts']); return [c['end_period_ts'],px(c,'yes_bid'),px(c,'yes_ask')],'ok'
            return None,'none'
    return None,('fail' if fail else 'none')
def trades(m):
    got={}; fail=False
    for path in (['/historical/trades','/markets/trades'] if m['hist'] else ['/markets/trades','/historical/trades']):
        cur=''
        while True:
            d=get(f"{path}?ticker={m['t']}&min_ts={m['snap']}&max_ts={m['end']}&limit=1000"+(f"&cursor={cur}" if cur else ''))
            if d=='FAIL': fail=True; break
            if not d: break
            for t in d.get('trades',[]):
                got[t['trade_id']]=[t['created_time'],t['taker_side'],float(t['yes_price_dollars']),float(t['count_fp']),t.get('is_block_trade',False)]
            cur=d.get('cursor') or ''
            if not cur: break
        if got: break
    return sorted(got.values()),fail
def one(m):
    try:
        q,st=quote(m); r={'t':m['t'],'q':q,'st':st}
        if q and 0.03<=q[2]<=0.97 and q[2]-q[1]>=0.0199:
            r['tr'],f=trades(m)
            if f: r['st']='trfail'
    except Exception as e: r={'t':m['t'],'q':None,'st':'fail'}
    with lock:
        fo.write(json.dumps(r,separators=(',',':'))+'\n'); n[0]+=1
        if n[0]%5000==0: fo.flush(); print(n[0],round(n[0]/(time.time()-t0),1),'/s errs',err[0],flush=True)
with ThreadPoolExecutor(W) as ex: list(ex.map(one,todo))
fo.close(); print('finished',which,n[0],round(time.time()-t0),'s',flush=True)
