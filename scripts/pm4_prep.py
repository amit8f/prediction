"""PM4 Step 3: add split (train/hold, by event's earliest snapshot day vs 2026-05-29) and cluster day
(UTC day of scheduled close) to the universe. Listing fields only. Usage: pm4_prep.py universe.jsonl.gz OUT.jsonl"""
import json,gzip,sys,collections as C
from datetime import datetime,timezone
day=lambda t:datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
CUT=json.load(open('research/pm4_step2/split.json'))['holdout_from']
U=[json.loads(l) for l in gzip.open(sys.argv[1],'rt')]
first=C.defaultdict(lambda:9e18)
for m in U: first[m['e']]=min(first[m['e']],m['snap'])
n=C.Counter()
with open(sys.argv[2],'w') as f:
    for m in U:
        m['sp']='hold' if day(first[m['e']])>=CUT else 'train'; m['cday']=day(m['exp']); m['end']=m['close']; n[m['sp']]+=1
        f.write(json.dumps(m,separators=(',',':'))+'\n')
print(dict(n),'events',len(first),'cut',CUT)
