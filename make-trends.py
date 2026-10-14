#!/usr/bin/env python3
# make-trends v1.2: v1.1 + lease series (leases_total, nodes_leased) per the lease-coverage trend.
# v1.1: also records chain_total/chain_active (native on-chain count via count_total):
#       "hidden" field in the data, not shown in UI - historical record for us.
# Runs after make-summary.py. Appends one snapshot per run to trends.jsonl
# and writes trends.json next to the collector. Both files stay on the device
# for the paid API. This script must not upload them to GitHub: Pages publishes
# the main branch, so a push would serve node snapshots for free.
import json, os, urllib.request
from datetime import datetime, timezone, timedelta

HERE=os.path.dirname(os.path.abspath(__file__)) or "."
LATEST=os.path.join(HERE,"latest.json")
SUMMARY=os.path.join(HERE,"history-summary.json")
HISTORY=os.path.join(HERE,"history.jsonl")
TRENDS_LOG=os.path.join(HERE,"trends.jsonl")
TRENDS_OUT=os.path.join(HERE,"trends.json")
MAX_POINTS=1100          # ~ 4+ months at 8 runs/day
NOW=datetime.now(timezone.utc)

latest=json.load(open(LATEST))
hsum={h["a"]:h for h in json.load(open(SUMMARY))}

# ---- snapshot of the network right now (post-stale, same as the site) ----
def disp_status(n):
    return "stale" if hsum.get(n["addr"],{}).get("stale") else n.get("status")
act=[n for n in latest if disp_status(n)=="active"]
snap={
 "ts":NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
 "total":len(latest),
 "active":len(act),
 "stale":sum(1 for n in latest if disp_status(n)=="stale"),
 "api_ok":sum(1 for n in act if n.get("api_ok")),
 "asn":{}, "country":{}
}
for n in act:
    a=n.get("asn")
    if a:
        num=a.split(" ")[0]
        snap["asn"][num]=snap["asn"].get(num,0)+1
    c=n.get("country")
    if c: snap["country"][c]=snap["country"].get(c,0)+1
# keep file small: ASNs with >=3 nodes, top 40 countries
# hidden metric: lifetime on-chain registrations + native active count (1 cheap call each)
def _chain_count(extra=""):
    try:
        req=urllib.request.Request(f"https://lcd.sentinel.co/sentinel/node/v3/nodes?pagination.limit=1&pagination.count_total=true{extra}",
                                   headers={"User-Agent":"scorecard"})
        return int(json.loads(urllib.request.urlopen(req,timeout=15).read())["pagination"]["total"])
    except Exception: return None
# lease coverage from latest.json (field written by collector v3.7)
_act=[n for n in latest if disp_status(n)=="active"]
_lv=[n.get("leases") for n in _act if n.get("leases") is not None]
snap["nodes_leased"]=sum(1 for v in _lv if v>0) if _lv else None
snap["leases_total"]=sum(v for v in _lv if v) if _lv else None
snap["chain_total"]=_chain_count()
snap["chain_active"]=_chain_count("&status=1")
snap["asn"]={k:v for k,v in snap["asn"].items() if v>=3}
snap["country"]=dict(sorted(snap["country"].items(),key=lambda x:-x[1])[:40])

with open(TRENDS_LOG,"a") as f: f.write(json.dumps(snap,separators=(",",":"))+"\n")

# ---- node movers: 7d uptime vs previous 23d, from raw history ----
cut7=NOW-timedelta(days=7); cut30=NOW-timedelta(days=30)
stats={}  # addr -> [act7,tot7,actP,totP]
for l in open(HISTORY):
    try: r=json.loads(l)
    except: continue
    ts=r.get("ts","")
    try: t=datetime.fromisoformat(ts.replace("Z","+00:00"))
    except: continue
    if t<cut30: continue
    s=stats.setdefault(r.get("addr"),[0,0,0,0])
    if t>=cut7:
        s[1]+=1
        if r.get("status")=="active": s[0]+=1
    else:
        s[3]+=1
        if r.get("status")=="active": s[2]+=1
movers=[]
name={n["addr"]:(n.get("moniker") or "") for n in latest}
for a,(a7,t7,ap,tp) in stats.items():
    if t7<20 or tp<40: continue          # need real track record in both windows
    u7=a7/t7*100; up=ap/tp*100
    movers.append({"a":a,"mon":name.get(a,""),"d7":round(u7,1),"prev":round(up,1),"delta":round(u7-up,1)})
movers.sort(key=lambda m:m["delta"])
movers_down=[m for m in movers if m["delta"]<-2][:10]
movers_up=[m for m in movers[::-1] if m["delta"]>2][:10]

# ---- write the site file: full series (capped) + movers ----
series=[]
for l in open(TRENDS_LOG):
    try: series.append(json.loads(l))
    except: pass
series=series[-MAX_POINTS:]
json.dump({"series":series,"movers_up":movers_up,"movers_down":movers_down,
           "generated":snap["ts"]},open(TRENDS_OUT,"w"),separators=(",",":"))
print(f"trends: {len(series)} points, movers +{len(movers_up)}/-{len(movers_down)} -> {TRENDS_OUT} (local only, not published)")
