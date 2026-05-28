#!/usr/bin/env python3
# make-summary v2: aggregati + timeline compatta per nodo (per l'Inspector)
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)) or "."
DATA=os.path.join(HERE,"history.jsonl")
OUT=os.path.join(HERE,"history-summary.json")
WINDOW=168  # ultimi N campioni nella timeline (1 settimana orari)

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
    summary.append({"a":a,"mon":recs[-1].get("moniker") or a,"n":n,
        "uptime":round(uptime,1),"trans":trans,"stab":round(stab,1),"ul":ul,
        "country":country,"sc":sc,"tl":tl,"tl_from":tl_from,"tl_to":tl_to})

json.dump(summary,open(OUT,"w"))
print(f"summary v2: {len(summary)} nodi (con timeline) -> {OUT}")
