#!/usr/bin/env python3
# make-trends v1.2: v1.1 + lease series (leases_total, nodes_leased) per the lease-coverage trend.
# v1.1: registra anche chain_total/chain_active (conteggio nativo on-chain via count_total):
#       campo "nascosto" nei dati, non mostrato in UI - storico per noi.
# Runs after make-summary.py. Appends one snapshot per run to trends.jsonl,
# writes trends.json (site file) and pushes it to GitHub reusing the token
# already stored in push-latest.sh (never hardcode the token here).
import json, os, re, base64, urllib.request
from datetime import datetime, timezone, timedelta

HERE=os.path.dirname(os.path.abspath(__file__)) or "."
LATEST=os.path.join(HERE,"latest.json")
SUMMARY=os.path.join(HERE,"history-summary.json")
HISTORY=os.path.join(HERE,"history.jsonl")
TRENDS_LOG=os.path.join(HERE,"trends.jsonl")
TRENDS_OUT=os.path.join(HERE,"trends.json")
PUSH_SH=os.path.join(HERE,"push-latest.sh")
REPO="superpios/node-scorecard"; BRANCH="main"
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
# lease coverage from latest.json (campo scritto dal collector v3.7)
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
print(f"trends: {len(series)} points, movers +{len(movers_up)}/-{len(movers_down)} -> trends.json")

# ---- push trends.json to GitHub (token read from push-latest.sh) ----
try:
    tok=re.search(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',open(PUSH_SH).read())
    if not tok: raise RuntimeError("token non trovato in push-latest.sh")
    tok=tok.group(1)
    api=f"https://api.github.com/repos/{REPO}/contents/trends.json"
    def gh(url,data=None,method="GET"):
        req=urllib.request.Request(url,data=data,method=method,
            headers={"Authorization":f"token {tok}","User-Agent":"scorecard","Accept":"application/vnd.github+json"})
        return json.loads(urllib.request.urlopen(req,timeout=30).read())
    sha=None
    try: sha=gh(api+f"?ref={BRANCH}").get("sha")
    except Exception: pass
    body={"message":"update trends.json","branch":BRANCH,
          "content":base64.b64encode(open(TRENDS_OUT,"rb").read()).decode()}
    if sha: body["sha"]=sha
    gh(api,json.dumps(body).encode(),"PUT")
    print("OK trends.json pushed")
except Exception as e:
    print(f"push trends fallito (riproverà al prossimo giro): {e}")
