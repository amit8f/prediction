"""Step 3 PM1 analysis. mode: funnel <set> | train | hold <lockfile>"""
import json,sys,math,gzip,collections as C
from datetime import datetime,timezone
import numpy as np
W='/tmp/claude-0/w/'; mode=sys.argv[1]
P=lambda s: datetime.fromisoformat(s.replace('Z','+00:00'))
U={m['ticker']:m for m in json.load(open(W+'universe.json'))}
ser={s['ticker']:s for s in json.load(gzip.open('/mnt/project-files/data/kalshi_series_2026-11-11.json.gz'))['series']}
chg=C.defaultdict(list)
for c in json.load(open(W+'fee_changes.json'))['series_fee_change_arr']: chg[c['series_ticker']].append((P(c['scheduled_ts']).timestamp(),c['fee_multiplier']))
def mult(s,T):
    h=sorted(chg.get(s,[]))
    if not h: return ser[s].get('fee_multiplier',1)
    past=[v for t,v in h if t<=T]
    return past[-1] if past else 1  # before the first recorded change: assume the standard 1
ME=json.load(open(W+'events_me.json'))
BK={'0.70-0.80':(0.70,0.80,False),'0.80-0.90':(0.80,0.90,False),'0.90-0.97':(0.90,0.97,True)}
def inb(p,b): lo,hi,inc=BK[b]; return lo<=p<hi or (inc and abs(p-hi)<1e-9)
def day(T): return datetime.fromtimestamp(T,timezone.utc).date().isoformat()
def load_quotes(s):
    Q={}
    for l in open(W+f'q_{s}.jsonl'): r=json.loads(l); Q[r['ticker']]=r
    return Q
def funnel(s):
    Q=load_quotes(s); f=C.Counter(); f['eligible markets']=sum(1 for m in U.values() if m['set']==s)
    f['quote rows pulled']=len(Q); T={}
    for t,r in Q.items():
        if r.get('bid') is None or r.get('ask') is None: f['drop: no candle or no quote at/before T' if r['src']!='fail' else 'drop: API failure']+=1; continue
        b,a=r['bid'],r['ask']
        if b<=0 or a>=1: f['drop: bid 0 or ask 1.00']+=1; continue
        mid=(a+b)/2
        if abs(mid-0.5)<1e-9: f['drop: mid exactly 0.50']+=1; continue
        m=U[t]; T[t]=dict(ticker=t,ev=m['event_ticker'],series=m['series'],T=m['T'],day=day(m['T']),bid=b,ask=a,mid=mid,
            fav='yes' if mid>0.5 else 'no',entry=a if mid>0.5 else round(1-b,4),age_h=(m['T']-r['end'])/3600)
    # ladder check on mutually exclusive events
    sm=C.defaultdict(list)
    for x in T.values(): sm[x['ev']].append(x['mid'])
    bad={e for e,v in sm.items() if ME.get(e) and len(v)>=2 and sum(v)>1.25}
    nb=sum(len(sm[e]) for e in bad)
    T={t:x for t,x in T.items() if x['ev'] not in bad}
    f['drop: mutually exclusive ladder, mids sum > 1.25 (events %d)'%len(bad)]=nb
    f['tradeable markets']=len(T)
    for b in BK:
        tr=[x for x in T.values() if inb(x['entry'],b)]
        f[f'in bucket {b}: markets / events / days / games']='%d / %d / %d / %d'%(len(tr),len({x['ev'] for x in tr}),len({x['day'] for x in tr}),len({x['ev'].split('-',1)[-1] for x in tr}))
    a=sorted(x['age_h'] for x in T.values()); f['quote age at T (hours) median/90th/99th']='%.1f / %.1f / %.1f'%(a[len(a)//2],a[int(.9*len(a))],a[int(.99*len(a))])
    f['events with ME flag known']='%d of %d'%(sum(1 for e in sm if e in ME),len(sm))
    return f,T
def fee(P_,s,T):
    return math.ceil(round(0.07*mult(s,T)*10*P_*(1-P_)*100,6))/100/10
def results(s):
    R={}
    for l in open(W+f'r_{s}.jsonl'): r=json.loads(l); R[r['ticker']]=r
    return R
def payout_yes(r,void_loss=False):
    if r.get('result') in ('yes','no'): return 1.0 if r['result']=='yes' else 0.0
    if void_loss: return 'loss'
    v=r.get('settlement_value_dollars'); return None if v in (None,'') else float(v)
def trades(T,R,b,void_loss=False):
    out=[];f=C.Counter()
    for x in T.values():
        if not inb(x['entry'],b): continue
        py=payout_yes(R.get(x['ticker'],{}),void_loss)
        if R.get(x['ticker'],{}).get('result') not in ('yes','no'): f['non yes/no result']+=1
        if py is None: f['dropped: no settlement value']+=1; continue
        pay=0.0 if py=='loss' else (py if x['fav']=='yes' else 1-py)
        out.append(dict(x,net=pay-x['entry']-fee(x['entry'],x['series'],x['T'])))
    return out,f
def events(tr,key='net'):
    E=C.defaultdict(list); D={}
    for x in tr: E[x['ev']].append(x[key]); D[x['ev']]=min(D.get(x['ev'],x['day']),x['day'])
    ev=sorted(E); return np.array([np.mean(E[e]) for e in ev]),np.array([D[e] for e in ev]),ev
def tclust(y,d):
    n=len(y); m=y.mean(); g=C.defaultdict(float)
    for v,k in zip(y-m,d): g[k]+=v
    G=len(g); se=math.sqrt(G/(G-1)*sum(v*v for v in g.values()))/n; return m,se,m/se,G
def boot(y,d,B=10000,seed=20261112):
    rng=np.random.default_rng(seed); ks=sorted(set(d)); idx={k:i for i,k in enumerate(ks)}; di=np.array([idx[k] for k in d])
    S=np.bincount(di,weights=y,minlength=len(ks)); N=np.bincount(di,minlength=len(ks)); bs=[]
    for _ in range(B):
        c=np.bincount(rng.integers(0,len(ks),len(ks)),minlength=len(ks)); bs.append((c*S).sum()/(c*N).sum())
    return np.percentile(bs,[2.5,97.5])
def summary(tr):
    y,d,ev=events(tr); m,se,t,G=tclust(y,d); lo,hi=boot(y,d)
    return dict(markets=len(tr),events=len(y),days=G,games=len({e.split('-',1)[-1] for e in ev}),mean=m,se=se,t=t,ci=(lo,hi))
def control(tr,T,R,seed=20261112,n=1000):
    rng=np.random.default_rng(seed)
    nets=C.defaultdict(list)
    for x in T.values():
        py=payout_yes(R.get(x['ticker'],{}))
        if py is None: continue
        ny=py-x['ask']-fee(x['ask'],x['series'],x['T']); pn=round(1-x['bid'],4); nn=(1-py)-pn-fee(pn,x['series'],x['T'])
        nets[x['day']].append((ny,nn))
    arr={k:np.array(v) for k,v in nets.items()}
    for x in tr:
        a=arr[x['day']]; i=rng.integers(0,len(a),n); s=rng.integers(0,2,n); x['ctrl']=a[i,s].mean()
    return tr
if mode=='funnel':
    f,_=funnel(sys.argv[2]); [print(f'  {k}: {v}') for k,v in f.items()]
elif mode=='train':
    f,T=funnel('train'); R=results('train')
    print('result status counts:',C.Counter((r.get('status'),r.get('result')) for r in R.values()).most_common(8))
    best=None
    for b in BK:
        tr,ff=trades(T,R,b); s=summary(tr); print(b,dict(ff),{k:(round(v,4) if isinstance(v,float) else v) for k,v in s.items()})
        if best is None or s['mean']>best[1]: best=(b,s['mean'])
    print('CHOSEN BUCKET',best[0]); json.dump({'bucket':best[0],'train_mean':best[1],'locked_at':datetime.now(timezone.utc).isoformat()},open(W+'bucket_lock.json','w'))
elif mode=='hold':
    b=json.load(open(sys.argv[2]))['bucket']; f,T=funnel('hold'); R=results('hold')
    print('result status counts:',C.Counter((r.get('status'),r.get('result')) for r in R.values()).most_common(8))
    tr,ff=trades(T,R,b); print('PRIMARY',b,dict(ff)); s=summary(tr); print(s)
    tr=control(tr,T,R); yc,dc,_=events(tr,'ctrl'); y,d,_=events(tr)
    print('control mean',yc.mean(),'diff',(y-yc).mean(),'diff CI',boot(y-yc,d), 'diff t',tclust(y-yc,d)[2])
    print('passes: mean>0',s['mean']>0,'t>=3',s['t']>=3,'CI>0',s['ci'][0]>0,'events>=300',s['events']>=300,'days>=60',s['days']>=60)
    print('EXPLORATORY (never a pass):')
    for bb in BK:
        if bb!=b: print(' ',bb,{k:(round(v,4) if isinstance(v,float) else v) for k,v in summary(trades(T,R,bb)[0]).items()})
    print('  voids as total loss',{k:(round(v,4) if isinstance(v,float) else v) for k,v in summary(trades(T,R,b,True)[0]).items()})
    bym=C.defaultdict(list)
    for x in tr: bym[x['day'][:7]].append(x['net'])
    print('  by month (market-level mean, n):',[(k,round(float(np.mean(v)),4),len(v)) for k,v in sorted(bym.items())])
    print('  trades per day in holdout:',round(len(tr)/s['days'],1))
