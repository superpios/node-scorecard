#!/usr/bin/env python3
# Sentinel Scorecard Collector v3 (global --all)
# v3: aggiunge price_hr/price_gb (da LCD), protocol/peers/version/banda (da API locale)
import json, os, sys, time, urllib.request, urllib.parse, ssl
from datetime import datetime, timezone
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=os.path.join(HERE,"history.jsonl"); WATCH=os.path.join(HERE,"watchlist.json"); LATEST=os.path.join(HERE,"latest.json")
LCD="https://lcd.sentinel.co"; TIMEOUT=10
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
def now_iso(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def fetch(url,timeout=TIMEOUT):
    req=urllib.request.Request(url,headers={"User-Agent":"scorecard/3.0"})
    with urllib.request.urlopen(req,timeout=timeout,context=CTX) as r: return json.loads(r.read().decode())
def load_watch():
    if os.path.exists(WATCH):
        try: return json.load(open(WATCH))
        except: return {"nodes":[]}
    return {"nodes":[]}
def save_watch(w): json.dump(w,open(WATCH,"w"),indent=2)
def add_node(a):
    w=load_watch()
    if a not in w["nodes"]: w["nodes"].append(a); save_watch(w); print(f"Aggiunto {a}")
    else: print("Gia' presente")
def all_nodes(lim=200,maxp=12):
    out=[]; key=None
    for p in range(maxp):
        url=f"{LCD}/sentinel/node/v3/nodes?status=1&pagination.limit={lim}"
        if key: url+=f"&pagination.key={urllib.parse.quote(key)}"
        try: d=fetch(url,timeout=15)
        except Exception as e: print(f"  ! pagina {p}: {e}"); break
        ns=d.get("nodes",[])
        for n in ns: out.append(n.get("address"))
        key=(d.get("pagination") or {}).get("next_key")
        print(f"  pagina {p+1}: +{len(ns)} (tot {len(out)})")
        if not key or not ns: break
        time.sleep(0.5)
    return out
def price_udvpn(arr):
    # estrae il quote_value (in udvpn) e lo converte in P2P (diviso 1e6)
    for p in (arr or []):
        if p.get("denom")=="udvpn":
            try: return round(int(p["quote_value"])/1e6,2)
            except: return None
    return None
def sample(addr):
    rec={"ts":now_iso(),"addr":addr,"status":None,"inactive_at":None,"remote":None,"moniker":None,
         "dl_mbps":None,"ul_mbps":None,"api_ok":False,"gb_tokens":0,
         "price_hr":None,"price_gb":None,"protocol":None,"peers":None,"version":None,"country":None,"city":None}
    try:
        n=fetch(f"{LCD}/sentinel/node/v3/nodes/{addr}").get("node",{})
        rec["status"]=n.get("status"); rec["inactive_at"]=n.get("inactive_at")
        ra=n.get("remote_addrs") or []; rec["remote"]=ra[0] if ra else None
        rec["moniker"]=n.get("moniker")
        gp=n.get("gigabyte_prices") or []; hp=n.get("hourly_prices") or []
        rec["gb_tokens"]=len(gp)
        rec["price_gb"]=price_udvpn(gp)   # P2P/GB
        rec["price_hr"]=price_udvpn(hp)   # P2P/hr
    except Exception as e: rec["error"]=str(e); return rec
    if rec["remote"]:
        try:
            api=fetch(f"https://{rec['remote']}/",timeout=7); res=api.get("result",api)
            rec["api_ok"]=True
            # banda: l'API locale espone downlink/uplink (bytes/s)
            if res.get("downlink"):
                try: rec["dl_mbps"]=round(int(res["downlink"])*8/1e6,2)
                except: pass
            if res.get("uplink"):
                try: rec["ul_mbps"]=round(int(res["uplink"])*8/1e6,2)
                except: pass
            rec["peers"]=res.get("peers")
            rec["protocol"]=res.get("service_type")  # v2ray / wireguard / openvpn
            ver=res.get("version") or {}
            rec["version"]=ver.get("tag") if isinstance(ver,dict) else ver
            if not rec["moniker"]: rec["moniker"]=res.get("moniker")
            loc=res.get("location") or {}
            if loc.get("country"): rec["country"]=loc["country"]
            if loc.get("city"): rec["city"]=loc["city"]
        except Exception: rec["api_ok"]=False
    return rec
def export_latest():
    if not os.path.exists(DATA): print("Nessuno storico."); return
    latest={}
    for l in open(DATA):
        if l.strip():
            try: r=json.loads(l); latest[r["addr"]]=r
            except: pass
    json.dump(list(latest.values()),open(LATEST,"w"))
    print(f"Esportati {len(latest)} nodi in {LATEST}")
def report():
    if not os.path.exists(DATA): print("Nessuno storico."); return
    rows=[json.loads(l) for l in open(DATA) if l.strip()]; by={}
    for r in rows: by.setdefault(r["addr"],[]).append(r)
    print(f"\n{len(rows)} campioni su {len(by)} nodi\n")
    for a,recs in sorted(by.items(),key=lambda x:-sum(1 for r in x[1] if r.get('status')=='active')/len(x[1])):
        n=len(recs); up=round(sum(1 for r in recs if r.get("status")=="active")/n*100,1)
        mon=(recs[-1].get("moniker") or a[:20])[:22]; print(f"  {mon:<24} {n:>4}smp {up:>5}%")
def main():
    a=sys.argv[1:]
    if "--add" in a: add_node(a[a.index("--add")+1]); return
    if "--report" in a: report(); return
    if "--export-latest" in a: export_latest(); return
    if "--all" in a:
        print(f"[{now_iso()}] Scarico lista globale nodi..."); t=all_nodes(); print(f"[{now_iso()}] {len(t)} nodi da campionare")
    else:
        t=load_watch()["nodes"]
        if not t: print("Vuoto. Usa --add o --all"); return
        print(f"[{now_iso()}] Campiono {len(t)} nodi watchlist")
    w=0; act=0
    with open(DATA,"a") as f:
        for i,addr in enumerate(t):
            rec=sample(addr); f.write(json.dumps(rec)+"\n"); w+=1
            if rec.get("status")=="active": act+=1
            if "--all" in a:
                if (i+1)%50==0: print(f"  ...{i+1}/{len(t)} ({act} active)")
            else:
                bw=f"{rec['ul_mbps']}Mbps" if rec.get("ul_mbps") else "n/d"
                print(f"  {addr[:24]}... {rec.get('status') or '?':<9} {rec.get('protocol') or '?':<9} {bw}")
            time.sleep(0.25)
    print(f"[{now_iso()}] {w} campioni ({act} active)"); export_latest()
if __name__=="__main__": main()
