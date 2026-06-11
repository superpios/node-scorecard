#!/usr/bin/env python3
# make-summary v3.5.1: l_pos richiede >=8 campioni (evita falsi "never leased" a storico giovane). v3.5: v3.4 + lease stats: l_pos (% recent samples with a lease = "lease uptime"), l_now
import json, os
from datetime import datetime, timezone
HERE=os.path.dirname(os.path.abspath(__file__)) or "."
DATA=os.path.join(HERE,"history.jsonl")
OUT=os.path.join(HERE,"history-summary.json")
WINDOW=168           # ultimi N campioni nella timeline (1 settimana orari)
STALE_HOURS=24       # se l'ultimo campione > 24h -> nodo considerato stale
PURGE_DAYS=30        # nodes unseen for 30+ days (delisted from chain) drop out of the summary
NOW=datetime.now(timezone.utc)

by={}
for l in open(DATA):
    if not l.strip(): continue
    try: r=json.loads(l)
    except: continue
    if r.get("addr"): by.setdefault(r["addr"],[]).append(r)

summary=[]
for a,recs in by.items():
    recs.sort(key=lambda r:r.get("ts",""))
    n=len(recs)
    active=sum(1 for r in recs if r.get("status")=="active")
    uptime=active/n*100 if n else 0
    trans=sum(1 for i in range(1,len(recs)) if (recs[i].get("status")=="active")!=(recs[i-1].get("status")=="active"))
    stab=max(0,100-(trans/(n-1))*200) if n>1 else 100
    uls=[r["ul_mbps"] for r in recs if r.get("ul_mbps")]
    ul=sum(uls)/len(uls) if uls else None
    country=next((r.get("country") for r in reversed(recs) if r.get("country")),None)
    sc=round(uptime*0.6+stab*0.3+(10 if ul else 0))
    # timeline compatta: ultimi WINDOW campioni, '1'=active '0'=altro
    win=recs[-WINDOW:]
    tl="".join("1" if r.get("status")=="active" else "0" for r in win)
    tl_from=win[0].get("ts") if win else None
    tl_to=win[-1].get("ts") if win else None
    # recent lease stats (last ~7 days): l_pos = "lease uptime" (% of samples with an active lease)
    lr=[r.get("leases") for r in recs[-56:] if r.get("leases") is not None]
    l_pos=round(sum(1 for v in lr if v>0)/len(lr)*100) if len(lr)>=8 else None  # serve >=1 giorno di campioni lease
    l_now=recs[-1].get("leases") if recs[-1].get("leases") is not None else None
    # recent peers stats (last ~7 days): for the "healthy but no clients" lease check
    pr=[r.get("peers") for r in recs[-56:] if r.get("peers") is not None]
    p_pos=round(sum(1 for v in pr if v>0)/len(pr)*100) if pr else None
    p_avg=round(sum(pr)/len(pr),1) if pr else None
    # stale check: età ultimo campione
    age_h=None; stale=False
    last_ts=recs[-1].get("ts","")
    try:
        last_dt=datetime.fromisoformat(last_ts.replace('Z','+00:00'))
        age_h=round((NOW-last_dt).total_seconds()/3600, 1)
        stale=age_h > STALE_HOURS
    except: pass
    if age_h is not None and age_h > PURGE_DAYS*24: continue  # purge: delisted/dead for 30+ days
    mon=next((r.get("moniker") for r in reversed(recs) if r.get("moniker")),a)
    summary.append({"a":a,"mon":mon,"n":n,
        "uptime":round(uptime,1),"trans":trans,"stab":round(stab,1),"ul":ul,
        "country":country,"sc":sc,"tl":tl,"tl_from":tl_from,"tl_to":tl_to,
        "stale":stale,"age_h":age_h,"p_pos":p_pos,"p_avg":p_avg,"l_pos":l_pos,"l_now":l_now})

json.dump(summary,open(OUT,"w"))
stale_count=sum(1 for s in summary if s.get("stale"))
purged=len(by)-len(summary)
print(f"summary v3.5: {len(summary)} nodi ({stale_count} stale, {purged} purged >30d) -> {OUT}")
