"""Step 3: settlement result for one set (train or hold). Run hold ONLY after the bucket is locked."""
import json,sys,os,time,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor
B='https://api.elections.kalshi.com/trade-api/v2'
U=json.load(open(sys.argv[1])); which=sys.argv[2]; outf=sys.argv[3]
if which=='hold' and not os.path.exists(sys.argv[4] if len(sys.argv)>4 else '/nonexistent'): sys.exit('bucket lock file missing')
todo=[m['ticker'] for m in U if m['set']==which]
def get(u):
    for i in range(8):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (400,404): return {}
            time.sleep(min(2**i,30))
        except Exception: time.sleep(min(2**i,30))
    return {}
K=('ticker','status','result','settlement_value_dollars','settlement_ts')
def grp(g):
    got={}
    for ep in ('/historical/markets','/markets'):
        miss=[t for t in g if t not in got]
        if not miss: break
        d=get(f"{ep}?tickers={','.join(miss)}&limit=100")
        for x in d.get('markets',[]): got[x['ticker']]={k:x.get(k) for k in K}
    return [got.get(t,{'ticker':t,'status':'missing'}) for t in g]
gs=[todo[i:i+100] for i in range(0,len(todo),100)]
with open(outf,'w') as fo, ThreadPoolExecutor(4) as ex:
    for rs in ex.map(grp,gs):
        for r in rs: fo.write(json.dumps(r)+'\n')
print('done',which,len(todo))
