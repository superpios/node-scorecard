#!/usr/bin/env python3
# Sentinel Scorecard Collector v3.2 (global --all)
# v3: aggiunge price_hr/price_gb (da LCD), protocol/peers/version/banda (da API locale)
# v3.1: retry API nodo (2 tentativi) per ridurre nodi con moniker/peers None
# v3.2: ASN enrichment con cache su file (lookup IP->ASN via ip-api, 1 call per IP nuovo)
import json, os, sys, time, urllib.request, urllib.parse, ssl, socket
from datetime import datetime, timezone
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=os.path.join(HERE,"history.jsonl"); WATCH=os.path.join(HERE,"watchlist.json"); LATEST=os.path.join(HERE,"latest.json")
ASNCACHE=os.path.join(HERE,"asn_cache.json")
LCD="https://lcd.sentinel.co"; TIMEOUT=10
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
def now_iso(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def fetch(url,timeout=TIMEOUT):
    req=urllib.request.Request(url,headers={"User-Agent":"scorecard/3.2"})
    with urllib.request.urlopen(req,timeout=timeout,context=CTX) as r: return json.loads(r.read().decode())
def lookup_asn(remote, cache):
    # remote = 'host:port' o 'ip:port' -> 'AS#### Org' (cache su IP, 1 call per IP nuovo)
    if not remote: return None
    host=remote.split(":")[0].strip()
    if not host: return None
    try: ip=socket.gethostbyname(host)
    except Exception: return None
    if ip in cache: return cache[ip]
    try:
        d=fetch(f"http://ip-api.com/json/{ip}?fields=status,as,isp",timeout=8)
        if d.get("status")=="success":
            cache[ip]=d.get("as") or d.get("isp"); return cache[ip]
    except Exception: pass
    cache[ip]=None
    return None
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
def all_nodes(lim=200,maxp=15):
    out=[]; key=None
    for p in range(maxp):
        url=f"{LCD}/sentinel/node/v3/nodes?pagination.limit={lim}"
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
    for p in (arr or []):
        if p.get("denom")=="udvpn":
            try: return round(int(p["quote_value"])/1e6,2)
            except: return None
    return None
def sample(addr):
    rec={"ts":now_iso(),"addr":addr,"status":None,"inactive_at":None,"remote":None,"moniker":None,
         "dl_mbps":None,"ul_mbps":None,"api_ok":False,"gb_tokens":0,
         "price_hr":None,"price_gb":None,"protocol":None,"peers":None,"version":None,"country":None,"city":None,"asn":None}
    try:
        n=fetch(f"{LCD}/sentinel/node/v3/nodes/{addr}").get("node",{})
        rec["status"]=n.get("status"); rec["inactive_at"]=n.get("inactive_at")
        ra=n.get("remote_addrs") or []; rec["remote"]=ra[0] if ra else None
        rec["moniker"]=n.get("moniker")
        gp=n.get("gigabyte_prices") or []; hp=n.get("hourly_prices") or []
        rec["gb_tokens"]=len(gp)
        rec["price_gb"]=price_udvpn(gp)
        rec["price_hr"]=price_udvpn(hp)
    except Exception as e: rec["error"]=str(e); return rec
    if rec["remote"]:
        api=None
        for attempt,to in enumerate((7,12)):
            try:
                api=fetch(f"https://{rec['remote']}/",timeout=to); break
            except Exception:
                if attempt==0: time.sleep(1)
                api=None
        if api is not None:
            try:
                res=api.get("result",api)
                rec["api_ok"]=True
                if res.get("downlink"):
                    try: rec["dl_mbps"]=round(int(res["downlink"])*8/1e6,2)
                    except: pass
                if res.get("uplink"):
                    try: rec["ul_mbps"]=round(int(res["uplink"])*8/1e6,2)
                    except: pass
                rec["peers"]=res.get("peers")
                rec["protocol"]=res.get("service_type")
                ver=res.get("version") or {}
                rec["version"]=ver.get("tag") if isinstance(ver,dict) else ver
                if not rec["moniker"]: rec["moniker"]=res.get("moniker")
                loc=res.get("location") or {}
                if loc.get("country"): rec["country"]=loc["country"]
                if loc.get("city"): rec["city"]=loc["city"]
            except Exception: rec["api_ok"]=False
        else:
            rec["api_ok"]=False
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
def enrich_asn():
    # ASN enrichment fuori dal ThreadPool (rate-limit ip-api 45/min). Con cache, solo IP nuovi.
    if not os.path.exists(DATA): return
    cache=json.load(open(ASNCACHE)) if os.path.exists(ASNCACHE) else {}
    latest_by={}
    for l in open(DATA):
        if l.strip():
            try: r=json.loads(l); latest_by[r["addr"]]=r
            except: pass
    new_lookups=0
    for addr,r in latest_by.items():
        if r.get("asn"): continue
        rem=r.get("remote")
        if not rem: continue
        host=rem.split(":")[0].strip()
        try: ip=socket.gethostbyname(host)
        except Exception: ip=None
        if not ip: continue
        if ip in cache:
            r["asn"]=cache[ip]
        else:
            r["asn"]=lookup_asn(rem,cache); new_lookups+=1
            if new_lookups%40==0: time.sleep(62)  # resta sotto 45/min di ip-api
    json.dump(cache,open(ASNCACHE,"w"))
    json.dump(list(latest_by.values()),open(LATEST,"w"))
    print(f"[{now_iso()}] ASN: {new_lookups} nuovi lookup, cache {len(cache)} IP")
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
    if "--asn" in a: enrich_asn(); return
    if "--all" in a:
        print(f"[{now_iso()}] Scarico lista globale nodi..."); t=all_nodes(); print(f"[{now_iso()}] {len(t)} nodi da campionare")
    else:
        t=load_watch()["nodes"]
        if not t: print("Vuoto. Usa --add o --all"); return
        print(f"[{now_iso()}] Campiono {len(t)} nodi watchlist")
    w=0; act=0; done=0; total=len(t)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with open(DATA,"a") as f:
        with ThreadPoolExecutor(max_workers=60) as ex:
            futs={ex.submit(sample,addr):addr for addr in t}
            for fut in as_completed(futs):
                try: rec=fut.result()
                except Exception as e: rec={"ts":now_iso(),"addr":futs[fut],"error":str(e)}
                f.write(json.dumps(rec)+"\n"); w+=1; done+=1
                if rec.get("status")=="active": act+=1
                if "--all" in a and done%200==0: print(f"  ...{done}/{total} ({act} active)")
    print(f"[{now_iso()}] {w} campioni ({act} active)")
    export_latest()
    enrich_asn()   # v3.2: aggiunge ASN dopo l'export
if __name__=="__main__": main()
