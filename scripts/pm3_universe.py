"""PM3 test universe: Climate and Weather markets kept by the Step 2 funnel, with snapshot, cancel time and split.
Listing fields only. Usage: pm3_universe.py OUT.jsonl"""
import gzip,json,sys,collections
from datetime import datetime,timedelta,timezone
P=lambda x: datetime.fromisoformat(x.replace('Z','+00:00'))
H=timedelta(hours=1);LO,HI=datetime(2025,1,1,tzinfo=timezone.utc),datetime(2026,11,14,tzinfo=timezone.utc)
def snap(o,c):   # same as scripts/pm3_funnel.py
    s=c.replace(minute=0,second=0,microsecond=0)-24*H if c.minute or c.second else c-24*H
    return max(s,o.replace(minute=0,second=0,microsecond=0)+2*H)
out=open(sys.argv[1],'w');n=collections.Counter()
for l in gzip.open('/mnt/project-files/data/pm3/pm3_listings_slim.jsonl.gz','rt'):
    m=json.loads(l)
    if m['category']!='Climate and Weather' or not m.get('expected_expiration_time') or not m.get('open_time'): continue
    c,o=P(m['expected_expiration_time']),P(m['open_time'])
    if not(LO<=c<HI) or m['market_type']!='binary' or m['mve'] or m['res_kind']=='other' or m['series']=='KXCITIESWEATHER': continue
    s=snap(o,c)
    if s>=c-H or (m.get('close_time') and s>=P(m['close_time'])): continue
    end=min(c-H,P(m['close_time']))   # cancel 1h before scheduled close, or when trading stops
    sp='hold' if s.date().isoformat()>='2026-05-27' else 'train'; n[sp]+=1
    out.write(json.dumps(dict(t=m['ticker'],e=m['event_ticker'],s=m['series'],snap=int(s.timestamp()),end=int(end.timestamp()),
        ct=m['close_time'],day=s.date().isoformat(),cday=c.date().isoformat(),sp=sp))+'\n')
print(n)
