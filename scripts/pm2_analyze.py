"""PM2 test. Modes:
  funnel SET            counts only, reads no result
  train                 training returns for M in {0.02,0.04,0.06}; writes the margin lock
  hold                  the one holdout test with the locked M (refuses without the lock)
Quote files: q_train.txt, q_hold.txt (a market lands in a set by its first signal day, not by file).
Usage: pm2_analyze.py MODE [SET] DIR"""
import json,sys,os,gzip,math,collections as C
from datetime import datetime,timezone
import numpy as np, pandas as pd
mode=sys.argv[1]; SET=sys.argv[2] if mode=='funnel' else mode; D=sys.argv[-1]
SPLIT='2026-05-27'; GRID=[0.02,0.04,0.06]; LOCK=os.path.join(D,'margin_lock.json')
ts=lambda s:int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
day=lambda t:datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
if mode=='hold':
    if not os.path.exists(LOCK): sys.exit('margin lock missing')
    GRID=[json.load(open(LOCK))['M']]
# ---- spot (Coinbase candle start_ts = START of minute; spot at m = close of candle starting at m-60)
SP={}
for coin in ('BTC','ETH','SOL','XRP'):
    df=pd.read_csv(f'/mnt/project-files/data/pm2/coinbase_{coin}_1m.csv.gz')
    t0=int(df.start_ts.min()); n=int((df.start_ts.max()-t0)//60)+1; i=((df.start_ts-t0)//60).astype(int).values
    cl=np.full(n,np.nan); cl[i]=df.close.values; ohlc=np.full(n,np.nan); ohlc[i]=((df.open+df.high+df.low+df.close)/4).values
    r=pd.Series(np.log(cl)).diff()
    sig=r.rolling(60,min_periods=60).std(ddof=1).values      # 60 returns from 61 closes, any gap -> NaN
    SP[coin]=(t0,cl,ohlc,sig)
coin_of=lambda s:s[2:5]
# ---- markets in this set
LO,HI=ts('2025-01-01T00:00:00Z'),ts('2026-11-13T00:00:00Z')
mk={}
for l in gzip.open('/mnt/project-files/data/pm2/pm2_listings_slim.jsonl.gz'):
    m=json.loads(l); E=ts(m['close_time']); h=not m['series'].endswith('15M'); op=ts(m['open_time'])
    first=E-55*60 if h else op+60
    if (day(first)>=SPLIT)!=(SET=='hold'): continue
    if not (LO<=E<HI) or (h and m.get('floor_strike') is None): continue   # Step 2 funnel drops, already counted there
    m.update(E=E,h=h,op=op,first=first,day=day(first)); mk[m['ticker']]=m
LO,HI=ts('2025-01-01T00:00:00Z'),ts('2026-11-13T00:00:00Z')
fee=lambda P:math.ceil(round(0.07*10*P*(1-P)*100,6))/100/10      # 10 contracts, rounded up to the cent, per contract
f=C.Counter(); f['markets in set']=len(mk); seen=set()
trades=[]; pool=C.defaultdict(list)   # pool[(series,close hour)] = valid (ticker,entry,side) for the random control
prng=np.random.default_rng(7); pcount=C.Counter()
def addpool(key,item,cap=4000):   # reservoir sample: uniform over all valid (market, minute, side) in the group
    pcount[key]+=1; L=pool[key]
    if len(L)<cap: L.append(item)
    else:
        j=int(prng.integers(pcount[key]))
        if j<cap: L[j]=item
def quotes(c):
    q={}   # k (minutes before close) -> (bid,ask) of the latest candle ending within the 5 minutes up to that minute
    for off,b,a in c: q[off]=(b,a)
    out={}
    for k in range(0,62):
        for j in range(k,k+5):
            if j in q: out[k]=q[j]; break
    return out
for fn in ('q_train.txt','q_hold.txt'):
    p=os.path.join(D,fn)
    if not os.path.exists(p): continue
    for l in open(p):
        r=json.loads(l); m=mk.get(r['t'])
        if m is None or r['t'] in seen: continue
        seen.add(r['t'])
        if r['s']=='fail': f['drop: quote pull failed']+=1; continue
        t0,cl,ohlc,sig=SP[coin_of(m['series'])]
        if m['h']: K=m.get('floor_strike')
        else: K=ohlc[(m['op']-60-t0)//60]
        ks=list(range(55,1,-1)) if m['h'] else list(range((m['E']-m['op'])//60-1,1,-1))
        q=quotes(r['c']); valid=lambda x:x and x[0] is not None and x[0]>0 and x[1] is not None and x[1]<1
        anyq=False; anyfair=False; fired={}
        for k in ks:
            mm=m['E']-60*k; ix=(mm-60-t0)//60
            for d in (0,1):
                x=q.get(k-d)
                if not valid(x): continue
                anyq=True
                if d==0 and SET=='hold':
                    for side,P in (('yes',x[1]),('no',1-x[0])):
                        if 0.05<=P<=0.95: addpool((m['series'],m['E']//3600),(r['t'],P,side))
                S=cl[ix]; sg=sig[ix]
                if not(S==S and sg==sg and sg>0 and K==K and K): continue
                anyfair=True
                fair=0.5*(1+math.erf(math.log(S/K)/(sg*math.sqrt(k-0.5))/math.sqrt(2)))
                b,a=x; ye=fair-a-fee(a); ne=(1-fair)-(1-b)-fee(1-b)
                side,P,e=('yes',a,ye) if ye>=ne else ('no',1-b,ne)
                for M in GRID:
                    if (M,d) not in fired and e>M and 0.05<=P<=0.95: fired[(M,d)]=(side,P,k)
        if not anyq: f['drop: no usable quote in any signal minute']+=1; continue
        if not anyfair: f['drop: quote but no spot/sigma/strike']+=1; continue
        f['tradeable markets']+=1
        for (M,d),(side,P,k) in fired.items():
            trades.append(dict(t=r['t'],ev=m['event_ticker'],day=m['day'],ser=m['series'],E=m['E'],M=M,d=d,side=side,P=P,fee=fee(P),k=k))
f['drop: market not in quote files']=len(mk)-len(seen)
T=pd.DataFrame(trades)
print('FUNNEL',SET); [print(' ',k,f'{v:,}') for k,v in f.items()]
if len(T):
    for (M,d),g in T.groupby(['M','d']): print(f'  traded M={M} delay={d}m: markets {len(g):,} events {g.ev.nunique():,} days {g.day.nunique()}')
if mode=='funnel': sys.exit()
# ---- results
R={}
for l in open(os.path.join(D,f'r_{SET}.jsonl')):
    x=json.loads(l); R[x['ticker']]=x
def yesval(t):
    x=R.get(t) or {}
    if x.get('result') in ('yes','no'): return 1.0 if x['result']=='yes' else 0.0
    v=x.get('settlement_value_dollars')
    return None if v is None else float(v)
T['yv']=T.t.map(yesval); print('trades with no usable result (dropped):',int(T.yv.isna().sum())); T=T.dropna(subset=['yv'])
T['net']=np.where(T.side=='yes',T.yv,1-T.yv)-T.P-T.fee
def stats(ev,rng=None,B=10000):
    x=ev.v.values; g=ev.groupby('day').v.agg(['sum','count']); n=len(x); mu=x.mean()
    s=ev.assign(r=ev.v-mu).groupby('day').r.sum().values; G=len(s)
    t=mu/math.sqrt(G/(G-1)*(s**2).sum()/n**2)
    rng=rng or np.random.default_rng(2026); cnt=rng.multinomial(G,[1/G]*G,size=B)
    bs=(cnt@g['sum'].values)/(cnt@g['count'].values)
    return dict(events=n,days=G,mean=mu,t=t,lo=np.percentile(bs,2.5),hi=np.percentile(bs,97.5))
def event(g): return g.groupby(['ev','day'],as_index=False).net.mean().rename(columns={'net':'v'})
out={}
for (M,d),g in T.groupby(['M','d']):
    s=stats(event(g)); out[(M,d)]=s
    print(f"M={M} delay={d}m  markets {len(g):,}  "+'  '.join(f'{k} {v:.4f}' if isinstance(v,float) else f'{k} {v:,}' for k,v in s.items()))
if mode=='train':
    ok=[M for M in GRID if out.get((M,0),{}).get('events',0)>=300]
    M=max(ok,key=lambda M:out[(M,0)]['mean']) if ok else None
    json.dump(dict(M=M,chosen_on='train, zero delay, highest event mean among >=300 events',
                   train={str(k):v for k,v in out.items()}),open(LOCK,'w'),indent=1,default=float)
    print('LOCKED M =',M); sys.exit()
# ---- holdout: random control (zero delay), exploratory cuts, dollar check
M=GRID[0]; P0=T[(T.M==M)&(T.d==0)].copy(); rng=np.random.default_rng(12345)
cache={}
def ctrl(key):
    if key not in cache:
        pl=pool.get(key) or []
        if not pl: cache[key]=np.nan; return np.nan
        idx=rng.integers(0,len(pl),size=1000); v=[]
        for i in idx:
            t,P,side=pl[i]; y=yesval(t)
            if y is None: continue
            v.append((y if side=='yes' else 1-y)-P-fee(P))
        cache[key]=(np.mean(v),np.std(v))
    return cache[key]
P0['c']=[ctrl((s,E//3600))[0] if ctrl((s,E//3600))==ctrl((s,E//3600)) else np.nan for s,E in zip(P0.ser,P0.E)]
ce=P0.dropna(subset=['c']).groupby(['ev','day'],as_index=False).agg(r=('net','mean'),c=('c','mean'))
print(f"CONTROL mean {ce.c.mean():.4f}  (rule on same events {ce.r.mean():.4f})")
sd=stats(ce.assign(v=ce.r-ce.c)); print('RULE MINUS CONTROL',{k:(round(v,4) if isinstance(v,float) else v) for k,v in sd.items()})
print('distinct close hours across coins (traded):',P0.E.floordiv(3600).nunique())
print('EXPLORATORY (never a pass)')
for name,g in [('15-minute only',P0[P0.ser.str.endswith('15M')]),('hourly only',P0[~P0.ser.str.endswith('15M')])]+[(c,P0[P0.ser.str[2:5]==c]) for c in ('BTC','ETH','SOL','XRP')]:
    if len(g)>20: s=stats(event(g),B=2000); print(f"  {name}: events {s['events']:,} mean {s['mean']:.4f} t {s['t']:.2f}")
print('  side mix:',P0.side.value_counts().to_dict(),' entry price median',round(P0.P.median(),3),' minutes-before-close median',P0.k.median())
nd=P0.day.nunique(); per_day=len(P0)/nd
print(f"DOLLAR CHECK: {per_day:.0f} trades a day x 10 contracts x {P0.net.mean():.4f} per contract x 30 = {per_day*10*P0.net.mean()*30:,.0f} dollars a month")
