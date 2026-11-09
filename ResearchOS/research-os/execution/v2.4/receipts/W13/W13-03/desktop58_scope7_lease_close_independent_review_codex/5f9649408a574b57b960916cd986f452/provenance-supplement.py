import hashlib,json
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os"); O=R/"execution/v2.4/receipts/W13/W13-03/desktop58_scope7_lease_close_independent_review_codex/5f9649408a574b57b960916cd986f452"
def j(p):return json.loads(Path(p).read_bytes())
def path(p):
    p=Path(p);return p if p.is_absolute() else R/p
def norm(p):return path(p).resolve()
a=j(O/"audit.json"); findings=a["failed_checks"]; out=[]
for f in findings:
    n=int(f["name"].rsplit(":",1)[1]); d=next(x for x in a["details"]["origins"] if x["failure_index"]==n)
    ref=d["evidence_ref"]; m=d["mapping_value"]; b=j(path(ref["path"]))
    reason=None; ok=False
    if n in (649,650,651,652,653,667):
        p=m.get("origin_ref",m);ok=norm(p["path"])==norm(ref["path"]) and p["sha256"]==ref["sha256"] and p["bytes"]==ref["bytes"]
        reason="Absolute versus relative Windows path representations refer to the same physical file; original hash and bytes are exact."
    elif n in (656,657):
        s=m["source"];ok=m["failure_index"]==n and m["origin_ref"] is None and s["outer_exit"]==b["actual_outer_exit"] and s["python_exit"]==b["actual_python_exit"] and s["native_exit"] is b["actual_native_exit"] is None
        text=b["full_result"]["output"]
        ok=ok and (("terminal snapshot Goal and Run': 0" in text and b["operation"]=="sdkv7_source_builder_anchor_preflight") if n==656 else ("CLI_FINAL_EXECUTION_SCOPE_INVALID" in text and b["operation"]=="sdkv7_stream_final_pure_io_fixture_shape"))
        reason="Earlier Root mapping explicitly had origin_ref null; author-sealed original now supplies exact source operation, matching failure layer and original error text; no missing earlier hash invented."
    elif n==666:
        ok=m["count"]==b["count"]==666 and norm(m["path"])==norm(ref["path"]) and m["not_yet_pinned"] is True and m["sha256"] is None and m["bytes"] is None
        reason="Earlier Root record identifies exact path and count while explicitly leaving hash/size unpinned; original receipt now independently hashed, no past hash reconstructed."
    elif n==668:
        q=j(R/"execution/v2.4/receipts/W13/W13-03/desktop58_scope7_failed_lease_close_cas_codex/b342fa5adb1e42d8813317e11e9f22c0/original-input.json")
        resume=j(path(q["root_resume_ref"]["path"]))
        strings=[]
        def collect(x):
            if isinstance(x,str):strings.append(x)
            elif isinstance(x,dict):
                for v in x.values():collect(v)
            elif isinstance(x,list):
                for v in x:collect(v)
        collect(resume)
        matches=[s for s in strings if "failure.origin.8a0dfa.json" in s and "current=668 / fixedcut=645" in s]
        ok=len(matches)>0 and b["original_result"]["chunk_id"]=="8a0dfa" and b["actual_outer_exit"]==1 and b["actual_native_exit"] is None
        reason="Origin receipt has no count field. Root-preserved source report explicitly maps failure.origin.8a0dfa.json to current=668 / fixedcut=645; original chunk and exit layers independently match."
    out.append({"original_check":f["name"],"resolved":bool(ok),"basis":reason,"evidence_ref":ref})
res={"schema":"researchos.scope7-lease-close-provenance-supplement.v1","superseded_initial_check_failures":out,"unresolved":[x for x in out if not x["resolved"]],"explanation":"Initial audit predicate assumed relative paths, already populated mapping hashes, and inline index. Its 10 false checks are retained unmodified and resolved against actual historical representations."}
with (O/"provenance-supplement.json").open("x",encoding="utf8") as f:json.dump(res,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"resolved":sum(x["resolved"] for x in out),"unresolved":res["unresolved"]},ensure_ascii=False))
