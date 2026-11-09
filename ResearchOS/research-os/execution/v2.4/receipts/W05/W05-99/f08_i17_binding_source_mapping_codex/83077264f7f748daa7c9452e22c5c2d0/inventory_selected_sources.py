from pathlib import Path
import hashlib,json,re
ROOT=Path("D:/作品集/ResearchOS/research-os")
OWN=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_i17_binding_source_mapping_codex/83077264f7f748daa7c9452e22c5c2d0"
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
def ref(p):
    raw=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"lines":len(raw.decode("utf-8-sig").splitlines())}
def put(name,obj):
    target=OWN/name
    if target.exists(): raise RuntimeError("new-only target exists: "+str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
v3=BASE/"f08_fence_semantics_revision_preparation_codex/65c17a2368284d90beec9526fba58a44"
bd3=BASE/"f08_initial_profile_journal_revision_preparation_codex/bd3fe19a27f54a468431828f267cd02f"
b6=BASE/"f08_proof_evaluator_implementation_preparation_codex/b6b765563c9640bd8a2b9e54f643352c"
a84=BASE/"f08_sqlite_driver18_validation_preparation_codex/a84ef66a214346e4891e569c55bc6d9b"
paths=[
("driver18",a84/"innocuous_test.go.proposed.txt"),
("v3_source",v3/"client_cancel_finalization.v3.go.proposed.txt"),
("v3_tests",v3/"client_cancel_finalization_test.v3.go.proposed.txt"),
("bd3_source",bd3/"client_cancel_finalization.v2.go.proposed.txt"),
("b6_source",b6/"client_cancel_finalization.go.proposed.txt"),
("bd3_sequence",bd3/"i02-fixture-sequence.json"),
("bd3_open",bd3/"coverage-open-matrix.json"),
("b6_snapshot_map",b6/"snapshot-map.json"),
("main_driver_open",ROOT/"internal/store/sqlite.go"),
("main_envelope",ROOT/"internal/domain/client_protocol.go"),
("main_schema_loader",ROOT/"internal/domain/client_protocol_schema.go"),
("main_embeds",ROOT/"internal/domain/backup_host_configuration.go"),
("main_domain_codec",ROOT/"internal/domain/contracts.go"),
("main_jcs",ROOT/"internal/canonical/jcs.go"),
("main_module",ROOT/"go.mod")]
snapshot_map=json.loads((b6/"snapshot-map.json").read_bytes())
selected_names={"go.mod","client_protocol.go","client_protocol_schema.go","backup_host_configuration.go","contracts.go","client_command_identity.go","runtime_dispatch.go","runtime_admission.go","durability_checkpoint.go","client_command_queue.go","client_protocol_queue_control.go","orchestration.go","client.protocol.schema.json","client.protocol.domain.schema.json","closed-contract.md","source-contract.md","evaluator-v5.md","candidate.sql.txt","source-registry34.exact.json"}
for pair in snapshot_map:
    if Path(pair["original"]["path"]).name in selected_names:
        paths.append(("frozen_"+Path(pair["snapshot"]["path"]).name,Path(pair["snapshot"]["path"])))
records=[];texts={}
for i,(role,p) in enumerate(paths):
    before=ref(p);raw=p.read_bytes()
    copy=OWN/"source-snapshots"/(str(i).zfill(2)+"-"+p.name)
    if copy.exists():raise RuntimeError("copy exists")
    copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(raw)
    if hashlib.sha256(raw).hexdigest()!=before["sha256"]:raise RuntimeError("read race")
    records.append({"role":role,"source":before,"copy":ref(copy)})
    texts[role]=raw.decode("utf-8-sig").splitlines()
put("selected-inputs.before.json",records)
ranges={
 "driver18":[[261,295]],
 "v3_source":[[1,65],[66,159],[249,307],[341,390],[1196,1233]],
 "v3_tests":[[31,119],[123,215],[443,557],[565,596]],
 "main_embeds":[[15,28]],
 "main_envelope":[[76,98],[367,390],[481,506],[604,616]],
 "main_schema_loader":[[55,79]],
 "main_driver_open":[[1,65]]
}
excerpts={}
for role,rs in ranges.items():
    lines=texts[role]
    excerpts[role]=[{"line":i,"text":lines[i-1]} for a,z in rs for i in range(a,min(z,len(lines))+1)]
for role,lines in texts.items():
    if role.startswith("frozen_") and any(n in role for n in ["closed-contract.md","source-contract.md","candidate.sql.txt","evaluator-v5.md"]):
        excerpts[role]=[{"line":i,"text":t} for i,t in enumerate(lines,1) if re.search(r"researchos_f08|mode8|CAST\(.*AS BLOB|sole|original|callback|private_header|CREATE VIEW f08_source",t)]
put("evidence.excerpts.json",excerpts)
locators={}
for role,lines in texts.items():
    if role.endswith("source") or role=="v3_tests" or role.startswith("main_") or ".go" in role:
        locators[role]=[{"line":i,"declaration":line} for i,line in enumerate(lines,1) if re.match(r"\s*func\s",line) and any(n in line for n in ["f08","DecodeEnvelope","ContentHash","DecodeResponse","LoadSchema","ValidateDef","ValidateResult","privateHeader","originalHeader","claimTaskMode","carryCheckpoint","prepareRuntimeDispatch","control","Cancel","cancel","Open","JCS","Hash","Decode","Bytes","Receipt"])]
put("source.locators.json",locators)
prod_hits=[]
prod_files=list((ROOT/"internal").rglob("*.go"))
for p in prod_files:
    if p.name.endswith("_test.go"):continue
    for i,line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(),1):
        if re.search(r"researchos_f08_|f08BuildCallbacks|Register(DeterministicScalar)?Function",line):
            prod_hits.append({"path":p.as_posix(),"line":i,"text":line})
sql_role=next(role for role in texts if role.endswith("candidate.sql.txt"))
sql="\n".join(texts[sql_role])
put("observed.status.json",{
 "schema":"researchos.f08.i17.source_mapping.observed.v1",
 "scope":"public internal production Go only; frozen selected receipts; no auth state read",
 "internal_go_files_enumerated":len(prod_files),"production_registration_hits":prod_hits,
 "sql_registration_name_occurrences":{n:sql.count(n) for n in ["researchos_f08_cancel_request_v1","researchos_f08_cancel_response_v1","researchos_f08_proof_v1"]},
 "numbered_main_migrations":[p.name for p in sorted((ROOT/"migrations/sqlite").glob("[0-9][0-9][0-9][0-9]_*.sql"))],
 "callbacks_installed":False,"candidate_executed":False,"go_ast_build_verified":False,"sql24_accepted":False,
 "full_3callback_complete":False,"rawvector_materialization":"NOT_RUN; Go fixture builders are source only"
})
print(json.dumps({"selected_source_count":len(records),"production_registration_hits":len(prod_hits),"own_namespace":OWN.as_posix()},ensure_ascii=False))
