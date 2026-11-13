"""PM2 test: settlement result for one set. The holdout set is refused until the margin lock file exists.
Usage: pm2_pull_results.py train|hold OUT.jsonl [LOCKFILE]"""
import json,sys,os,time,gzip,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor
B='https://api.elections.kalshi.com/trade-api/v2'; SPLIT='2026-05-27'
which,outf=sys.argv[1],sys.argv[2]
if which=='hold' and not (len(sys.argv)>3 and os.path.exists(sys.argv[3])): sys.exit('margin lock file missing')
todo=[json.loads(l)['ticker'] for l in gzip.open('/mnt/project-files/data/pm2/pm2_listings_slim.jsonl.gz')]
todo=[t for t,l in zip(todo,gzip.open('/mnt/project-files/data/pm2/pm2_listings_slim.jsonl.gz'))
      if (json.loads(l)['close_time']>=SPLIT)==(which=='hold')]
def get(u):
    for i in range(8):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (400,404): return {}
            time.sleep(min(2**i,30))
        except Exception: time.sleep(min(2**i,30))
    return {}
K=('ticker','status','result','settlement_value_dollars','settlement_value')
def grp(g):
    got={}
    for ep in ('/historical/markets','/markets'):
        miss=[t for t in g if t not in got]
        if not miss: break
        d=get(f"{ep}?tickers={','.join(miss)}&limit=100")
        for x in d.get('markets',[]): got[x['ticker']]={k:x.get(k) for k in K}
    return [got.get(t,{'ticker':t,'status':'missing'}) for t in g]
gs=[todo[i:i+100] for i in range(0,len(todo),100)]
with open(outf,'w') as fo, ThreadPoolExecutor(6) as ex:
    for rs in ex.map(grp,gs):
        for r in rs: fo.write(json.dumps(r)+'\n')
print('done',which,len(todo),flush=True)
