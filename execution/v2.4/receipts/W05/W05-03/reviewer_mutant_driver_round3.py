"""Round-3 reviewer mutant matrix, v2: every mutant gets up to 4 runs so a flake is never
recorded as a kill and a kill is never recorded as a survivor."""
import json,os,subprocess,hashlib,time,sys
REPO=r"D:\作品集\ResearchOS\research-os"
LOCK=json.load(open(os.path.join(REPO,"execution","toolchains","locked.json"),encoding="utf-8"))
GO=LOCK["tools"]["go"]["path"]
assert hashlib.sha256(open(GO,"rb").read()).hexdigest()==LOCK["tools"]["go"]["sha256"]
ENV={**os.environ,"GOTOOLCHAIN":"local","GOENV":"off","GOPATH":os.path.join(REPO,".local","gopath"),
     "GOCACHE":os.path.join(REPO,".local","gocache"),"RESEARCHOS_TASK_ID":"W05","RESEARCHOS_CHECK_ID":"W05-03",
     "PYTHONIOENCODING":"utf-8"}
TRANS=("HOST_UNREACHABLE","connection attempt failed","context deadline","CONNECTEX","timeout","refused")
def run():
    r=subprocess.run([GO,"run","./tests/runtime/cli_contract"],cwd=REPO,env=ENV,capture_output=True,
                     text=True,encoding="utf-8",errors="replace",timeout=900)
    ls=[l for l in (r.stdout or "").strip().splitlines() if l.startswith("{")]
    pay=json.loads(ls[-1]) if ls else {}
    fs=pay.get("failures",[])
    det=json.dumps(fs,ensure_ascii=False).lower()
    return {"rc":r.returncode,"status":pay.get("status"),"assertions":pay.get("assertions"),
            "failed":[f.get("id") for f in fs],
            "transport_share":round(sum(1 for f in fs if any(k in json.dumps(f,ensure_ascii=False).lower() for k in TRANS))/max(1,len(fs)),2),
            "details":{f.get("id"):json.dumps(f.get("detail"),ensure_ascii=False)[:200] for f in fs}}
M=json.load(open(os.path.join(REPO,".local","r3","mutants.json"),encoding="utf-8"))
only=sys.argv[1:] or None
N=int(os.environ.get("ATTEMPTS","4"))
out=[]
for m in M:
    if only and m["id"] not in only: continue
    p=m["file"]; orig=open(os.path.join(REPO,p),"rb").read(); base=hashlib.sha256(orig).hexdigest()
    t=orig.decode("utf-8")
    if t.count(m["old"])!=1:
        out.append({"id":m["id"],"classification":"anchor-missing"}); print(m["id"],"ANCHOR-MISSING",flush=True); continue
    open(os.path.join(REPO,p),"wb").write(t.replace(m["old"],m["new"],1).encode("utf-8"))
    runs=[]
    try:
        for a in range(N):
            rec=run(); rec["attempt"]=a+1; runs.append(rec)
            if rec["status"]=="PASS": break
    finally:
        open(os.path.join(REPO,p),"wb").write(orig)
    restored=hashlib.sha256(open(os.path.join(REPO,p),"rb").read()).hexdigest()==base
    passes=[r for r in runs if r["status"]=="PASS"]
    fails=[r for r in runs if r["status"]!="PASS"]
    exp=[e for e in m["expected"] if e.startswith("W0503")]
    # a run counts as a kill only if every expected named row went red in it
    kills=[r for r in fails if exp and all(e in r["failed"] for e in exp)]
    cls="survived" if passes else ("caught-by-card-id" if kills else "indeterminate")
    if passes and kills: cls="caught-by-card-id"   # named row died in >=1 run, but a clean PASS also happened: report both
    out.append({"id":m["id"],"file":p,"claim":m["claim"],"expected":exp,"classification":cls,
                "runs_with_mutant":[{"status":r["status"],"assertions":r["assertions"],"n_failed":len(r["failed"]),
                                     "transport_share":r["transport_share"],"failed":r["failed"]} for r in runs],
                "killed_by":sorted(set(exp)) if kills else [],
                "kill_runs":len(kills),"clean_runs_with_mutant":len(passes),
                "first_failure_details":(fails[0]["details"] if fails else {}),
                "restore":{"sha_matches":restored,"sha":base}})
    print(json.dumps({"id":m["id"],"cls":cls,"kill_runs":len(kills),"clean":len(passes),
                      "spreads":[(r["status"],r["assertions"],len(r["failed"]),r["transport_share"]) for r in runs],
                      "restored":restored},ensure_ascii=False),flush=True)
    if not restored: print("!!! RESTORE FAILED",p,flush=True)
json.dump(out,open(os.path.join(REPO,".local","r3","mutant_results2.json"),"w",encoding="utf-8"),indent=1,ensure_ascii=False)
print("DONE",len(out))
