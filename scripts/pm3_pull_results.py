"""PM3 test: Kalshi results for one split only (other split's results are never written).
Usage: pm3_pull_results.py universe.jsonl train|hold OUT.json"""
import json,sys,time,urllib.request
B='https://api.elections.kalshi.com/trade-api/v2'
uf,which,outf=sys.argv[1:4]
U=[m for m in map(json.loads,open(uf)) if m['sp']==which]; want={m['t'] for m in U}
def get(u):
    for i in range(8):
        try: return json.load(urllib.request.urlopen(B+u,timeout=60))
        except Exception: time.sleep(2**i)
res={}
for s in sorted({m['s'] for m in U}):
    for path in (f'/historical/markets?series_ticker={s}',f'/markets?series_ticker={s}&status=settled'):
        cur=''
        while True:
            d=get(path+'&limit=1000'+(f'&cursor={cur}' if cur else ''))
            for m in d.get('markets',[]):
                if m['ticker'] in want: res[m['ticker']]=[m.get('result'),m.get('settlement_value_dollars',m.get('settlement_value'))]
            cur=d.get('cursor') or ''
            if not cur: break
json.dump(res,open(outf,'w')); print(which,'wanted',len(want),'got',len(res))
