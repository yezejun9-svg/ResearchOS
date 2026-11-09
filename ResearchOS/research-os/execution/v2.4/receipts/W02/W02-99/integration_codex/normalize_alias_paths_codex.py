"""Replace display annotations with real existing paths in versioned aliases."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
V24=ROOT / "execution/v2.4"
SPEC=ROOT / ".local/worktrees/v24-continuation/spec/v2.4"
def load(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def ref(path,base=V24):return dict(path=path.relative_to(base).as_posix(),sha256=sha(path))
path_file,cp_file,state_file=(V24 / n for n in ["path_ownership.json","checkpoint.json","step_state.json"])
paths,cp,state=load(path_file),load(cp_file),load(state_file)
assert paths["revision"]==44 and cp["revision"]==201
legacy=ROOT / "execution/path_ownership.json"
legacy_sha=sha(legacy)
changed={}
for key,actual in {"CLI":"apps/cli","DESKTOP":"apps/desktop","QUALIFICATION":"qualification/v2.4"}.items():
    original=paths["aliases"][key]["paths"]
    assert len(original)==1 and original[0].startswith(actual+" (")
    assert (ROOT / actual).is_dir()
    changed[key]=dict(original_display_paths=original,actual_paths=[actual])
    paths["aliases"][key]["paths"]=[actual]
    paths["aliases"][key]["historical_display_paths"]=original
now=dt.datetime.now(dt.timezone.utc).isoformat()
paths.update(revision=45,updated_at=now,updated_by="codex:/root",amended_at=now,amended_by="codex:/root")
write(path_file,paths)
record=HERE / "alias_path_amendment_codex.json"
write(record,dict(recorded_at=now,actor="codex:/root",step_id="W02-99",status="CURRENT_EXISTING_ALIAS_PATHS_NORMALIZED",path_revision_before=44,path_revision_after=45,path_ownership_sha256=sha(path_file),aliases_changed=changed,owners_changed=0,other_aliases_and_card_bindings_unchanged=True,legacy_path_sha256=legacy_sha,legacy_unchanged=sha(legacy)==legacy_sha,scope="CLI/Desktop/qualification directories already exist. Move display annotations into historical_display_paths so later path consumers can resolve real repository-relative paths. No product code/data/resource/route/owner/REAL_ISSUE_SCOPE change.",new_tests_gui_provider_service_actions=0))
next(r for r in state["steps"] if r["id"]=="W02-99")["evidence"].append(ref(record))
write(state_file,state)
cp.update(updated_at=now,updated_by="codex:/root",note="W02 parent active, path45 resolves actual CLI/Desktop/qualification aliases without display comments. Owners, other aliases, REAL_ISSUE_SCOPE, original legacy bytes and product sources unchanged.36 accepted cards/2parents/0formal/58 old failure origins retained; W02 raw failures pending final integration accounting.")
cp["integrity_events"].append(dict(at=now,actor="codex:/root",card="W02-99",event="EXISTING_ALIAS_PATHS_NORMALIZED",evidence=ref(record),detail="Three already-existing path strings become directly resolvable; historical comments retained. No ownership or route change."))
write(cp_file,cp)
event=HERE / "alias_path_value_round_codex.json"
write(event,dict(schema="researchos.value-round.v1",round_id="W02-current-alias-path-normalization-20261005",delta="DOCUMENTATION",summary="Normalize three existing alias paths; keep historical annotations/owners, other aliases and all product sources unchanged.",evidence_refs=[ref(record,ROOT)]))
argv=[sys.executable,"-B","-X","utf8",str(ROOT / "bootstrap/v24_checkpoint.py"),"--checkpoint",str(cp_file),"--state",str(state_file),"--plan",str(SPEC / "contracts/execution.plan.json"),"--delivery",str(SPEC / "contracts/delivery.contract.json"),"--expected-revision","201","--round-event",str(event),"--actor","codex:/root"]
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE / "checkpoint202.stdout.txt").write_bytes(result.stdout)
(HERE / "checkpoint202.stderr.txt").write_bytes(result.stderr)
assert result.returncode==0,result.stderr.decode("utf-8","replace")
assert load(cp_file)["revision"]==202 and sha(legacy)==legacy_sha
print(json.dumps(dict(status="PASS",checkpoint=202,path_revision=45,record_sha256=sha(record),owners_changed=0,product_changes=0)))
