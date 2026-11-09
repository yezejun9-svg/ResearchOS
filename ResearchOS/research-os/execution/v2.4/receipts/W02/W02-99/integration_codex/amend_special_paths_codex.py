"""Root maps existing code/evidence and leaves private formal storage unbound."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
V24=ROOT / "execution/v2.4"
SPEC=ROOT / ".local/worktrees/v24-continuation/spec/v2.4"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def ref(path,base=V24):return {"path":path.relative_to(base).as_posix(),"sha256":sha(path)}
path_file=V24 / "path_ownership.json"
cp_file=V24 / "checkpoint.json"
state_file=V24 / "step_state.json"
paths,cp,state=load(path_file),load(cp_file),load(state_file)
assert paths["revision"]==43 and cp["revision"]==200 and "special_paths" not in paths
legacy_file=ROOT / "execution/path_ownership.json"
legacy_hash=sha(legacy_file)
legacy=load(legacy_file)
assert "../../../spec/v2.0/ui/design-tokens.json" in (ROOT / "apps/web/src/main.jsx").read_text(encoding="utf-8")
assert (ROOT / "spec/v2.0/ui/design-tokens.json").is_file()
assert (ROOT / "adapters/evaluation").is_dir() and (V24 / "receipts").is_dir()
now=dt.datetime.now(dt.timezone.utc).isoformat()
special=dict(
 evaluation_adapter=dict(path="adapters/evaluation",owner=paths["card_path_bindings"]["W10-02"]["owner"],owner_card="W10-02",status="BOUND",scope="Existing public development evaluation adapter source; no protected label access granted."),
 design_tokens=dict(path="spec/v2.0/ui/design-tokens.json",owner="codex:/root",status="BOUND",source_import="apps/web/src/main.jsx:3",scope="Current actual renderer import, unchanged frozen source; does not claim final v2.4 UI acceptance."),
 development_results=dict(path="execution/v2.4/receipts",owner="codex:/root",status="BOUND",access_class="DEVELOPMENT_FIXTURE_EVIDENCE",historical_paths=["execution/receipts"],scope="Actual construction development/fixture raw reports; per-card bindings own their subpaths. This is not product Artifact storage or a location for formal private examples/labels."),
 verifier_restricted_store=copy.deepcopy(legacy["special_paths"]["verifier_restricted_store"]))
special["verifier_restricted_store"].update(public_resource_ref="ResearchOSVerifierCanary",current_formal_readiness="NOT_ESTABLISHED",binding_scope="Public reference only. path remains null/UNBOUND; existing service/public historical summary does not authorize current-purpose private data access. No private path/data inspected.")
assert special["verifier_restricted_store"]["path"] is None and special["verifier_restricted_store"]["status"]=="UNBOUND"
paths.update(revision=44,special_paths=special,updated_at=now,updated_by="codex:/root",amended_at=now,amended_by="codex:/root")
write(path_file,paths)
record=HERE / "path_mapping_amendment_codex.json"
write(record,dict(recorded_at=now,actor="codex:/root",step_id="W02-99",status="EXISTING_PUBLIC_PATHS_REGISTERED_PRIVATE_STORE_UNBOUND",path_revision_before=43,path_revision_after=44,path_ownership_sha256=sha(path_file),legacy_path_ownership_sha256=legacy_hash,legacy_bytes_unchanged=sha(legacy_file)==legacy_hash,special_paths=special,source_import_sha256=sha(ROOT / "apps/web/src/main.jsx"),design_tokens_sha256=sha(ROOT / "spec/v2.0/ui/design-tokens.json"),scope="Frozen W02 development checklist5 actual path registration. Original legacy map unchanged; no data moved/provisioned, private read, new service, provider or product source edit.",new_tests=0,private_label_reads=0,provider_calls=0,service_actions=0))
row=next(r for r in state["steps"] if r["id"]=="W02-99")
assert row["status"]=="IN_PROGRESS"
row["evidence"].append(ref(record))
write(state_file,state)
cp.update(updated_at=now,updated_by="codex:/root",note="W02 parent implementation continues. Path44 adds actual public evaluation/design-token/development-evidence mapping; formal private store remains UNBOUND.36 accepted cards,2/22parents,0/42formal and58 preserved failure origins unchanged; W02 new raw harness failures pending frozen integration accounting.")
cp["integrity_events"].append(dict(at=now,actor="codex:/root",card="W02-99",event="CURRENT_SPECIAL_PATH_MAPPING_REGISTERED",evidence=ref(record),detail="Correct stale legacy UI path in versioned map only. Preserve null UNBOUND private store and all original legacy bytes; no provider/service/data access."))
write(cp_file,cp)
event=HERE / "path_mapping_value_round_codex.json"
write(event,dict(schema="researchos.value-round.v1",round_id="W02-current-special-path-map-20261005",delta="DOCUMENTATION",summary="Map existing current adapter, renderer token import and development evidence paths. Current-purpose formal private store remains null/UNBOUND; no capability or new LIVE resource claimed.",evidence_refs=[ref(record,ROOT)]))
argv=[sys.executable,"-B","-X","utf8",str(ROOT / "bootstrap/v24_checkpoint.py"),"--checkpoint",str(cp_file),"--state",str(state_file),"--plan",str(SPEC / "contracts/execution.plan.json"),"--delivery",str(SPEC / "contracts/delivery.contract.json"),"--expected-revision","200","--round-event",str(event),"--actor","codex:/root"]
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE / "checkpoint201.stdout.txt").write_bytes(result.stdout)
(HERE / "checkpoint201.stderr.txt").write_bytes(result.stderr)
assert result.returncode==0,result.stderr.decode("utf-8","replace")
assert load(cp_file)["revision"]==201 and sha(legacy_file)==legacy_hash
print(json.dumps(dict(status="PASS",checkpoint=201,path_revision=44,private_store="UNBOUND",legacy_unchanged=True,record_sha256=sha(record))))
