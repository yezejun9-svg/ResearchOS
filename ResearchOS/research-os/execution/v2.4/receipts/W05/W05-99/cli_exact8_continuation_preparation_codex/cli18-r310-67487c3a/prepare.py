"""Pure text/AST/hash preparation. Does not import or execute prepared runner/helper."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
OLD=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_continuation_preparation_codex/cli44-r309-grant-1bd789af'
OBS=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli44-r309-c927f880'
REVIEW=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli44-r309-stopped-aecd69f538014b068358ab527e547e53'
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (HERE/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(HERE/name)
def change(s,a,b):
 if s.count(a)!=1:raise RuntimeError('TEXT_ANCHOR:'+a[:80])
 return s.replace(a,b)
old=load(OLD/'finite_selectors.v3.json')['selectors']
lanes={'remaining17':old[27:],'windows4':[old[26]]}
assert len(lanes['remaining17'])==17 and sum(len(x['expected_leaf_names']) for x in lanes['remaining17'])==107
assert lanes['windows4'][0]['selector']=='^TestCLIReadStatusActualWindowsConsoleSignal$' and len(lanes['windows4'][0]['expected_leaf_names'])==4
outputs={k:str(ROOT/('execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/'+v)) for k,v in [('remaining17','cli17-r310-67487c3a'),('windows4','cli-windows4-r310-67487c3a')]}
assert all(not Path(x).exists() for x in outputs.values())
roster_refs={k:save('roster.'+k+'.json',dict(schema='researchos.cli-fixed-lane-roster.v1',lane=k,selectors=v,original44=ref(OLD/'finite_selectors.v3.json'),mutable_start_index=False)) for k,v in lanes.items()}
for name in ('reused_provenance.json','uri65.current.json'):
 with (HERE/name).open('xb') as f:f.write((OLD/name).read_bytes())
source=ref(OLD/'runner.v4.py');assert source['sha256']=='42fe7f31566588ff87f564085d033c15ce094d6218c404837072225cfd9f32b6'
s=(OLD/'runner.v4.py').read_text(encoding='utf-8')
s=change(s,'import argparse\n','import argparse\nimport ctypes\n')
s=change(s,'OUT = ROOT / "execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli44-r309-c927f880"','OUT = None\nLANE = None\nLANES = '+repr({k:dict(output=v,count=len(lanes[k]),leaves=sum(len(x['expected_leaf_names']) for x in lanes[k]),checkpoint_key=('cli17_continuation_scope_ref' if k=='remaining17' else 'cli_windows4_continuation_scope_ref')) for k,v in outputs.items()}))
s=change(s,'_AUTHORIZED_SCOPE_INPUT = None','_AUTHORIZED_SCOPE_INPUT = None\n_CHECKPOINT_RAW = None\n_KERNEL_MODULE = None\nKERNEL_PATH = Path("C:/Windows/System32/kernel.appcore.dll")\nKERNEL_SHA = "ed6d62f2555d260547cc94a5cdfe2a6fcb684f18b8e182f78f9e4de224321fc9"\nKERNEL_BYTES = 121360')
a=s.index('def authorize(args):');b=s.index('\n\ndef initialize_owned_runtime():',a)
s=s[:a]+'''def authorize(args):
    global _AUTHORIZED_SCOPE_INPUT, _CHECKPOINT_RAW, OUT, LANE
    require(sys.flags.isolated == 1 and sys.flags.optimize == 0, "Python must use -I without optimization")
    LANE = args.lane
    fixed = LANES[LANE]
    OUT = Path(fixed["output"])
    scope_path = Path(args.scope).resolve()
    raw = scope_path.read_bytes()
    require(sha(raw) == args.scope_sha256, "ROOT_SCOPE_HASH")
    _AUTHORIZED_SCOPE_INPUT = {"path": str(scope_path), "sha256": sha(raw), "bytes": len(raw)}
    _KNOWN_INPUTS.add(scope_path)
    scope = json.loads(raw)
    require(scope["owner"] == "codex:/root/w05_merge_review", "ROOT_OWNER")
    require(scope["registration_checkpoint"] == 310, "REGISTRATION_CP")
    grant = scope["cli_bounded_continuation"]
    require(grant["lane"] == LANE and grant["candidate"] == CANDIDATE, "LANE_CANDIDATE_GRANT")
    require(Path(grant["checkout"]) == CHECKOUT and Path(grant["output"]) == OUT, "PATH_GRANT")
    manifest = HERE / "manifest.json"
    require(grant["prepared_manifest_sha256"] == sha(manifest.read_bytes()), "PREPARED_MANIFEST_GRANT")
    helper = grant["owned_process_helper_ref"]
    require(Path(helper["path"]) == OWNED_HELPER and helper["sha256"] == OWNED_HELPER_SHA, "OWNED_HELPER_GRANT")
    require(file_ref(OWNED_HELPER)["sha256"] == OWNED_HELPER_SHA, "OWNED_HELPER_CHANGED")
    require(grant["invocation_limit"] == fixed["count"] and grant["leaf_limit"] == fixed["leaves"], "FINITE_GRANT")
    require(grant["SDK_MODEL_EXTERNAL_PAID_CALLS"] == 0, "NO_MODEL_GRANT")
    require(grant["kernel_resource_ref"] == file_ref(KERNEL_PATH), "KERNEL_RESOURCE_GRANT")
    require(grant["roster_ref"] == file_ref(HERE / ("roster." + LANE + ".json")), "EXACT_ROSTER_GRANT")
    _CHECKPOINT_RAW = (ROOT / "execution/v2.4/checkpoint.json").read_bytes()
    checkpoint = json.loads(_CHECKPOINT_RAW)
    require(checkpoint["revision"] >= 310, "CAS_NOT_APPLIED")
    pin = checkpoint["work_in_progress"][fixed["checkpoint_key"]]
    require((ROOT / pin["path"]).resolve() == scope_path and pin["sha256"] == args.scope_sha256, "CANONICAL_SCOPE_NOT_BOUND")
    for row in read_json(manifest)["entries"]:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "MANIFEST_MEMBER_PATH")
        path = HERE / relative
        _KNOWN_INPUTS.add(path)
        require(file_ref(path)["sha256"] == row["sha256"], "PREPARED_FILE_CHANGED:" + str(path))
    for row in read_json(OLD_PREP / "preparation_tools.v2.json"):
        require(file_ref(row["path"])["sha256"] == row["sha256"], "TOOL_PIN:" + row["path"])
    return {"scope": dict(_AUTHORIZED_SCOPE_INPUT), "grant": grant,
            "checkpoint": {"revision": checkpoint["revision"], "sha256": sha(_CHECKPOINT_RAW), "bytes": len(_CHECKPOINT_RAW)}}


def preload_kernel_resource():
    global _KERNEL_MODULE
    before = file_ref(KERNEL_PATH)
    require(before["sha256"] == KERNEL_SHA and before["bytes"] == KERNEL_BYTES, "KERNEL_EXACT_BYTES")
    # Absolute DLL_LOAD_DIR | DEFAULT_DIRS. No arbitrary search path, export call, or child.
    _KERNEL_MODULE = ctypes.WinDLL(str(KERNEL_PATH), winmode=0x00001100)
    require(file_ref(KERNEL_PATH) == before, "KERNEL_PRELOAD_DRIFT")
    _KNOWN_INPUTS.add(KERNEL_PATH)
    observed = runtime_vector()
    require(any(Path(x["path"]).resolve() == KERNEL_PATH.resolve() and x["sha256"] == KERNEL_SHA and x["bytes"] == KERNEL_BYTES for x in observed), "LOADED_KERNEL_PATH_NOT_OBSERVED")
    save(OUT / "kernel-preload.json", {"resource": before, "method": "ctypes.WinDLL absolute DLL_LOAD_DIR|DEFAULT_DIRS", "export_calls": 0, "original_loader_cause": None, "qualification_claim": False})
''' +s[b:]
s=change(s,'    save(OUT / "runtime.before-first-case.json", current_runtime)','''    prior = read_json(HERE / "prior7803-and-observed.json")
    for expected in prior["refs"]:
        require(file_ref(expected["path"]) == expected, "PRIOR7803_PROVENANCE_CHANGED")
    prior_vector = read_json(prior["original7803"]["path"])
    require(file_ref(prior["original7803"]["path"]) == prior["original7803"], "PRIOR7803_VECTOR_CHANGED")
    check_vector(prior_vector, OUT / "original7803.current-before.json")
    _KNOWN_INPUTS.update(Path(x["path"]) for x in prior_vector)
    save(OUT / "runtime.before-first-case.json", current_runtime)''')
s=change(s,'    paths.extend(p for p in HERE.iterdir() if p.is_file())','''    paths.extend(p for p in HERE.iterdir() if p.is_file())
    paths.extend(x["path"] for x in prior_vector)
    paths.extend(x["path"] for x in prior["refs"])
    paths.extend([prior["original7803"]["path"], OUT / "authorized-checkpoint.raw", KERNEL_PATH])''')
s=change(s,'    roster = read_json(HERE / "finite_selectors.v3.json")["selectors"]\n    require(len(roster) == 44 and sum(len(x["expected_leaf_names"]) for x in roster) == 145, "ROSTER_LIMIT")','    roster = read_json(HERE / ("roster." + LANE + ".json"))["selectors"]\n    require(len(roster) == LANES[LANE]["count"] and sum(len(x["expected_leaf_names"]) for x in roster) == LANES[LANE]["leaves"], "ROSTER_LIMIT")')
s=change(s,'    parser.add_argument("--scope", required=True)','    parser.add_argument("--lane", choices=sorted(LANES), required=True)\n    parser.add_argument("--scope", required=True)')
s=change(s,'        initialize_owned_runtime()  # Sets dont_write_bytecode before helper imports.','''        with (OUT / "authorized-checkpoint.raw").open("xb") as handle:
            handle.write(_CHECKPOINT_RAW)
        _KNOWN_INPUTS.add(OUT / "authorized-checkpoint.raw")
        initialize_owned_runtime()  # Sets dont_write_bytecode before helper imports.''')
s=change(s,'        save(OUT / "runtime.initial-after-preload.json", runtime_vector())','        preload_kernel_resource()\n        save(OUT / "runtime.initial-after-preload.json", runtime_vector())')
ast.parse(s)
with (HERE/'runner.v5.py').open('xb') as f:f.write(s.encode())
kernel=ref(Path('C:/Windows/System32/kernel.appcore.dll'))
assert kernel['sha256']=='ed6d62f2555d260547cc94a5cdfe2a6fcb684f18b8e182f78f9e4de224321fc9' and kernel['bytes']==121360
prior=load(OBS/'execution.inputs.before-first-case.json')
current=[ref(x['path']) for x in prior]
assert current==prior
save('original7803.current.json',current)
prior_refs=[ref(REVIEW/x) for x in ('review.json','failure_origins.json','case_matrix.json','readonly_cause.json')]+[ref(OBS/'cases/26/runtime.before.json'),ref(OBS/'cases/26/runtime.after-native.json'),ref(OBS/'invocations/case-26/invocation.json'),ref(OBS/'invocations/case-26/stdout.raw')]
save('prior7803-and-observed.json',dict(original7803=ref(OBS/'execution.inputs.before-first-case.json'),refs=prior_refs,kernel=kernel,loader_cause=None))
spec=save('prepared_execution_spec.json',dict(schema='researchos.cli-split-finite-continuation-preparation.v1',status='PREPARED_NOT_AUTHORIZED_NOT_EXECUTED',source_candidate='b98738ac093ea55bb8700cfa724ddd9e6b2a1251',runner=ref(HERE/'runner.v5.py'),base_runner=source,lanes={k:dict(output=outputs[k],roster=roster_refs[k],selector_limit=len(v),leaf_limit=sum(len(x['expected_leaf_names']) for x in v),checkpoint_work_key=('cli17_continuation_scope_ref' if k=='remaining17' else 'cli_windows4_continuation_scope_ref')) for k,v in lanes.items()},execution_order=['remaining17','windows4'],independent_outputs=True,kernel=kernel,kernel_observed_not_loader_cause=True,reused_provenance=ref(HERE/'reused_provenance.json'),new_primary_compilation=0,protected_qualified_leaves=110,remaining17_expected107=True,windows_expected4=True,total_planned_unique_union221=True,model_SDK_Node_external_paid=0,first_unexpected_stop=True,automatic_retry=False,raw_outer_exit_nullable=True,main_source_canonical_writes=0,preparation_executed_runner_or_helper=False,public_DLL_preload_executed=False,closure=['original7803 plus original compiler graph/WORK/generated/importcfg/archive/exes','Python source and actual cached pyc, actual OS DLL resources after explicit URI+Kernel preload','new Root scope exact bytes plus launch-verified CP scope binding snapshot','every case: before / after-native / after-fixtures full vector and runtime containment'],windows_boundary='Unchanged test internally builds temporary CLI and executes four original controls/three signals; require logged SHA/bytes match reused CLI. No broad selector or start_index.',grant_shape=dict(owner='codex:/root/w05_merge_review',registration_checkpoint=310,cli_bounded_continuation='lane,candidate,checkout,output,prepared_manifest_sha256,owned_process_helper_ref,invocation_limit,leaf_limit,SDK_MODEL_EXTERNAL_PAID_CALLS,kernel_resource_ref,roster_ref'),limits=['No product/source acceptance','No Main/fullharness/held2/P02/attach completion/formal','No root canonical refs hash cycle: snapshot actual CP only after Root CAS and preserve copy as immutable input','Native positive does not cure old runtime closure omissions; both old origins retained']))
save('static_audit.json',dict(ast_parse=True,controller_imported=False,helper_imported=False,WinDLL_called=False,go_Node_SQL_HTTP_test_calls=0,original7803_current_all_match=True,outputs_absent=outputs,source8_unchanged_via_original_vector=True,roster17_original_indexes=[x['original_index'] for x in lanes['remaining17']],windows_original_indexes=[x['original_index'] for x in lanes['windows4']],counts=dict(remaining17=107,windows4=4,prior_qualified110=110),original_failures_preserved=prior_refs))
members=[]
for p in sorted(HERE.iterdir()):
 if p.is_file():
  r=ref(p);r['path']=p.name;members.append(r)
manifest=save('manifest.json',dict(schema='researchos.prepared-controller-manifest.v1',entries=members,count=len(members),includes_self=False))
handoff=save('handoff.json',dict(status='PREPARED_ONLY_WAIT_ROOT_CAS',runner=ref(HERE/'runner.v5.py'),spec=spec,manifest=manifest,rosters=roster_refs,kernel_ref=kernel,outputs=outputs,actual_compile_case_DLL_helper_import=0))
print(json.dumps(dict(namespace=str(HERE),runner=ref(HERE/'runner.v5.py'),spec=spec,manifest=manifest,handoff=handoff),ensure_ascii=False))
