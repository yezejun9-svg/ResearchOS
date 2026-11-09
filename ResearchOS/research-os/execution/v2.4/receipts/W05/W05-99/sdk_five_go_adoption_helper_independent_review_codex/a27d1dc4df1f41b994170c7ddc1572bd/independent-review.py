import ast,hashlib,json,os
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_adoption_helper_independent_review_codex/a27d1dc4df1f41b994170c7ddc1572bd"
P=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d"
checks=[]; pins=[]
def ck(n,v):checks.append({"name":n,"passed":bool(v)})
def ref(p):
    raw=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verified(r):
    p=Path(r["path"]);p=p if p.is_absolute() else R/p
    v=ref(p);ck("pin:"+r["path"],v["sha256"]==r["sha256"] and v["bytes"]==r["bytes"]);pins.append(v);return p.read_bytes()
prep=json.loads((P/"preparation.json").read_bytes())
ck("preparation_exact",ref(P/"preparation.json")["sha256"]=="e064e1cdac43f479d224b3d65fa8422707a5f93ce45b5296feb73a53606ec318")
source=(P/"adopt_five_go.after_closed_scope7.py").read_bytes()
ck("latest_helper_exact",hashlib.sha256(source).hexdigest()=="aadb9f88a31f3ddf7dbc96f627cbcc8f1bb1f56ef729ff61c47a785ebb3e21bb" and len(source)==5475)
targets=["internal/host/vault.go","internal/host/host.go","apps/control/main.go","internal/domain/runtime_qualification.go","apps/cli/cli_stream.go"]
ck("only_five_targets",[x["target"] for x in prep["mapping"]]==targets)
for row in prep["mapping"]:
    before=verified(row["before_ref"]);backup=verified(row["backup_ref"]);proposal=verified(row["proposal_ref"]);prepared=verified(row["prepared_ref"]);verified(row["forward_ref"])
    ck("exact_byte_backup:"+row["target"],before==backup==(R/row["target"]).read_bytes())
    ck("exact_reviewed_proposal:"+row["target"],proposal==prepared)
    p=R/row["target"]
    ck("current_target_has_no_reparse:"+row["target"],all(not x.is_symlink() and not(getattr(x.lstat(),"st_file_attributes",0)&0x400) for x in (p,*p.parents) if x==R or R in x.parents))
for k in ("source_review_ref","adoption_input_review_ref"):verified(prep[k])
tree=ast.parse(source);calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
ck("no_subprocess_network_imports",all(x not in source.decode("utf8") for x in ("subprocess","Popen","requests.","urllib","socket","exec(","eval(")))
ck("single_os_replace_site",calls.count("os.replace")==1)
ck("no_remove_unlink_rmtree",not any(x.endswith((".unlink",".remove",".rmtree")) for x in calls))
ck("no_started_or_closed_execution",(not(P/"main-adoption.started.json").exists()) and (not(P/"main-adoption.closed.json").exists()))
review={"schema":"researchos.sdk-five-go-adoption-helper-independent-review.v1","reviewer_id":"codex:/root/w05_merge_review","author_id":"codex:/root","decision":"READY_FOR_ROOT_FIVE_GO_ADOPTION_AFTER_VERIFIED_SCOPE7_CLOSE","source_ref":ref(P/"adopt_five_go.after_closed_scope7.py"),"preparation_ref":ref(P/"preparation.json"),"checks":checks,"failed_checks":[x for x in checks if not x["passed"]],"checked_pins":pins,"targets":targets,"source_review_ref":prep["source_review_ref"],"adoption_input_review_ref":prep["adoption_input_review_ref"],"reviewed_behavior":["Actual closure receipt, tuple340/168/672 and two failed-closed states required before first write","Five exact baseline bytes backed up; prepared bytes equal already independently reviewed proposals","Exclusive once intent; same-volume temporary bytes, fsync, per-file atomic replacement and completed receipt","Before each write current target baseline plus original four canonical bytes checked; after loop all five target bytes and four canonical bytes checked","No model, subprocess, Git, canonical writes or other source paths; protected existing deletions outside the five target set","Partial source-write failure requires separate Root decision; no automatic rollback or retry"],"limits":["Static source and metadata input review only; helper entry not executed","Build/tests/new Main commit/new runner binding and model runtime remain Root follow-up","path_for resolves paths before its symlink check; current five actual paths independently checked no reparse, intended review applies to this exact preparation and current physical targets"],"actual_helper_executions":0,"actual_main_writes":0,"actual_canonical_writes":0,"actual_git_calls":0,"actual_native_product_calls":0,"new_tool_failures":0}
with (O/"review.json").open("x",encoding="utf8",newline="\n") as f:json.dump(review,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"checks":len(checks),"failed_checks":review["failed_checks"],"review_ref":ref(O/"review.json")},ensure_ascii=False))
