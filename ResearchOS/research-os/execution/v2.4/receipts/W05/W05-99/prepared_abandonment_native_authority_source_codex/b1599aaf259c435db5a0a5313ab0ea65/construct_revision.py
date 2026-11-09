from pathlib import Path
import hashlib,json,re,shutil
R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
N=B/"prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65"
P=B/"prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864"
M=B/"prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2"
def pin(path):
    b=path.read_bytes()
    return {"path":str(path),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
def save(path,v):
    path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
expected=[
(P/"HDF.json","2f33da54d8e91dad1651da92ecbbc6506d0520a541b730176129fafd2db0a3d2",23048),
(P/"MF.json","349aa6b33bd8a2616aa619607b25bea10f502e60292f734abcfc3e21a311215c",24259),
(M/"HDF.json","a6e03021860808f09d7e36622a6aff9206a3e2aa18008afd94c62ff00f177a99",12691),
(M/"MF.json","b1585d636212dfe6592bf51aff78257decff13a14d4efc148f6c0f66de94d42c",27291),
(R/"execution/v2.4/checkpoint.json","e128ec5e0a7aa8b7dad605fc3cd8889dc09f72d7b2ce0d1a864543c53328830d",3971419)]
inputs=[]
for p,h,n in expected:
    actual=pin(p)
    if actual["sha256"]!=h or actual["bytes"]!=n:
        save(N/"input-drift.json",{"expected":{"path":str(p),"sha256":h,"bytes":n},"actual":actual})
        raise SystemExit("INPUT_DRIFT_STOP")
    inputs.append(actual)
mf=json.loads((P/"MF.json").read_text(encoding="utf-8"))
for name,v in mf["members"].items():
    actual=pin(Path(v["path"]))
    if actual["sha256"]!=v["sha256"] or actual["bytes"]!=v["bytes"]:
        save(N/"input-drift.json",{"member":name,"expected":v,"actual":actual})
        raise SystemExit("PREVIOUS_SOURCE_DRIFT_STOP")
for name,v in mf["source_refs"].items():
    dst=N/"candidate-root"/name
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(v["path"],dst)
(N/"contracts").mkdir(exist_ok=True)
shutil.copyfile(P/"contracts/native-authority.v1.json",N/"contracts/native-authority.v1.json")
roots=["apps/control","internal","adapters","evaluation","ops"]
embeds=[]; files_per_root={}
for root in roots:
    paths=[p for p in (R/root).rglob("*") if p.is_file()]
    files_per_root[root]=len(paths)
    for source in paths:
        if source.suffix!=".go":continue
        text=source.read_text(encoding="utf-8")
        for lineno,line in enumerate(text.splitlines(),1):
            m=re.match(r"\s*//go:embed\s+(.+)$",line)
            if not m:continue
            # All actual directives here are single literal relative files.
            pattern=m.group(1).strip()
            target=source.parent/pattern
            if any(c in pattern for c in '*?[]"`') or pattern.startswith("all:") or not target.is_file():
                raise SystemExit("ACTUAL_EMBED_PATTERN_REQUIRES_EXPLICIT_INSPECTION")
            embeds.append({"source":pin(source),"line":lineno,"directive":line.strip(),"target":pin(target),"target_relative":target.relative_to(R).as_posix()})
save(N/"input-refs.json",{"schema":"researchos.native-authority-v2-inputs.v1","verified_inputs":inputs,"previous_source_manifest_member_count":len(mf["members"]),"copied_source_count":len(mf["source_refs"]),"previous_source_refs":mf["source_refs"]})
save(N/"actual-embed-inventory.json",{"schema":"researchos.actual-source-embed-inspection.v1","scope":roots,"directives":embeds,"directive_count":len(embeds),"regular_file_counts":files_per_root,"go_list_executed":False,"interpretation":"Read-only inspection of current repository literal go:embed directives, not a compiler-derived dependency closure."})
print(json.dumps({"inputs_verified":len(inputs),"previous_members_verified":len(mf["members"]),"copied_source_files":len(mf["source_refs"]),"embed_directives":len(embeds),"files_per_root":files_per_root},ensure_ascii=True))
