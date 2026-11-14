"""PM3 test analysis. Usage: pm3_analyze.py universe.jsonl pull.jsonl results.json train|hold [C]
train with no C: fits C on the grid. With C: the primary test, random control and dollar check."""
import json,sys,gzip,math,collections as Co
import numpy as np, pandas as pd
from datetime import datetime
uf,pf,rf,which=sys.argv[1:5]; CFIX=float(sys.argv[5]) if len(sys.argv)>5 else None
ts=lambda s:datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
U={m['t']:m for m in map(json.loads,open(uf)) if m['sp']==which}
R=json.load(open(rf))
fee_type={s['ticker']:s.get('fee_type') for s in json.load(gzip.open('/mnt/project-files/data/kalshi_series_2026-11-11.json.gz'))['series']}
fun=Co.Counter(); rows=[]
def yval(t):
    r=R.get(t)
    if not r: return None
    if r[0]=='yes': return 1.0
    if r[0]=='no': return 0.0
    try: return float(r[1]) if r[1] is not None else None
    except Exception: return None
def fill(tr,side,p,snap,end):   # side 'yes' = we sell YES at p; 'no' = we buy YES (sell NO) at p
    f=0.0
    for t in tr:
        tt=ts(t[0])
        if tt<=snap or tt>=end or t[6]: continue
        if side=='yes' and t[1]=='yes' and t[4]>=p-1e-9: f+=t[5]
        if side=='no' and t[1]=='no' and t[4]<=p+1e-9: f+=t[5]
        if f>=10: return 10.0
    return f
def fee(f,p): return math.ceil(0.0175*f*p*(1-p)*100-1e-9)/100 if f>0 else 0.0
for l in open(pf):
    x=json.loads(l); m=U.get(x['t'])
    if not m: continue
    fun['markets pulled']+=1
    if x['st'] in('fail','trfail'): fun['dropped: API failure']+=1; continue
    if not x['q']: fun['dropped: no quote in the 6h before snapshot']+=1; continue
    b,a=x['q'][1],x['q'][2]
    if not(0.03<=a<=0.97 and a-b>=0.0199): fun['dropped: quote cannot carry an order (ask outside 3-97c or spread <2c)']+=1; continue
    y=yval(x['t'])
    if y is None: fun['dropped: no usable result']+=1; continue
    fun['kept: quoted, order possible']+=1
    tr=x.get('tr',[])
    pY=round(a-0.01,4); fY=fill(tr,'yes',pY,m['snap'],m['end'])
    pN=round(b+0.01,4); fN=fill(tr,'no',pN,m['snap'],m['end'])
    mk=fee_type.get(m['s'])=='quadratic_with_maker_fees'
    rows.append(dict(t=x['t'],ev=m['e'],day=m['cday'],ask=a,bid=b,pY=pY,fY=fY,netY=(pY-y-fee(fY,pY)/fY) if fY else np.nan,
        realY=(pY-y-(fee(fY,pY)/fY if mk else 0)) if fY else np.nan,pN=pN,fN=fN,netN=(y-pN-fee(fN,pN)/fN) if fN else np.nan,y=y))
D=pd.DataFrame(rows)
print('== funnel',which); [print(f'{k:75s}{v:>8,}') for k,v in fun.items()]
def evals(g,f='fY',n='netY'):
    g=g[g[f]>0]; g=g.assign(w=g[f]*g[n])
    e=g.groupby(['ev','day'],as_index=False).agg(w=('w','sum'),f=(f,'sum')); e['v']=e.w/e.f; return e
def ctstat(e):
    x=e.v.values; mu=x.mean(); d=e.assign(r=x-mu).groupby('day').r.sum().values; G=len(d)
    se=math.sqrt((d**2).sum()*G/(G-1))/len(x); return mu,mu/se,G
def boot(e,B=10000,seed=1):
    g=e.groupby('day').v.agg(['sum','count']); s,c=g['sum'].values,g['count'].values; rng=np.random.default_rng(seed)
    idx=rng.integers(0,len(s),(B,len(s))); m=s[idx].sum(1)/c[idx].sum(1); return np.percentile(m,[2.5,97.5]),g
def rule(C): return D[(D.ask<=C+1e-9)]
if CFIX is None:
    print('\n== fitting C on training (event-level mean net per filled contract)')
    for C in (0.10,0.15,0.20):
        r=rule(C); e=evals(r); mu,t,G=ctstat(e)
        print(f'C={C:.2f} orders {len(r):6d} filled orders {int((r.fY>0).sum()):6d} filled events {len(e):5d} days {G:4d} mean {mu*100:+.4f}c t {t:+.2f}')
    sys.exit()
r=rule(CFIX); e=evals(r); mu,t,G=ctstat(e); ci,g=boot(e)
nd=D.day.nunique(); fo=int((r.fY>0).sum())
print(f'\n== PRIMARY C={CFIX:.2f}: orders {len(r)}, filled orders {fo} ({fo/len(r):.1%}), filled events {len(e)} of {r.ev.nunique()}, days with fills {G}')
print(f'mean net per contract {mu*100:+.3f}c  day-clustered t {t:+.2f}  bootstrap 95% [{ci[0]*100:+.3f}, {ci[1]*100:+.3f}]c')
print(f'contracts filled {r.fY.sum():.0f}, YES won on {(r[r.fY>0].y>=0.5).mean():.1%} of filled orders, mean sell price {r[r.fY>0].pY.mean():.3f}')
er=evals(r,'fY','realY'); print(f'exploratory real per-series maker fee: mean {er.v.mean()*100:+.3f}c')
# random control: for each rule order, a random quoted market the same day, random side
pool=D.groupby('day').indices; rng=np.random.default_rng(7); K=1000
side=[];idxs=[];rep=[]
for d,grp in r.groupby('day'):
    P=pool[d]; n=len(grp)
    idxs.append(P[rng.integers(0,len(P),(K,n))].ravel()); side.append(rng.integers(0,2,K*n)); rep.append(np.repeat(np.arange(K),n))
I=np.concatenate(idxs); S=np.concatenate(side); Rp=np.concatenate(rep)
f=np.where(S==0,D.fY.values[I],D.fN.values[I]); v=np.where(S==0,D.netY.values[I],D.netN.values[I])
cdf=pd.DataFrame(dict(rep=Rp,ev=D.ev.values[I],day=D.day.values[I],f=f,w=f*np.nan_to_num(v)))
cdf=cdf[cdf.f>0].groupby(['rep','ev','day'],as_index=False).agg(w=('w','sum'),f=('f','sum')); cdf['v']=cdf.w/cdf.f
cm=cdf.groupby('rep').v.mean(); print(f'control: mean {cm.mean()*100:+.3f}c (replicate 2.5-97.5%: {cm.quantile(.025)*100:+.3f}, {cm.quantile(.975)*100:+.3f}), filled events per replicate {len(cdf)/K:.0f}')
cg=cdf.groupby('day').v.agg(['sum','count']).reindex(g.index).fillna(0)
s1,c1,s2,c2=g['sum'].values,g['count'].values,cg['sum'].values,cg['count'].values
idx=np.random.default_rng(2).integers(0,len(s1),(10000,len(s1)))
diff=s1[idx].sum(1)/c1[idx].sum(1)-s2[idx].sum(1)/np.maximum(c2[idx].sum(1),1)
print(f'rule minus control {(mu-cm.mean())*100:+.3f}c, bootstrap 95% [{np.percentile(diff,2.5)*100:+.3f}, {np.percentile(diff,97.5)*100:+.3f}]c')
days=170 if which=='hold' else nd; per_day=r.fY.sum()/days
print(f'dollar check: filled contracts per day {per_day:.1f}, filled orders per day {fo/days:.2f}, cash tied up per filled contract {(1-r[r.fY>0].pY).mean():.3f}, implied monthly net ${per_day*30*mu:+.2f}')
