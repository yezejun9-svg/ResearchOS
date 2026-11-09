"""Prepare immutable continuation controller; read/hash only, no product invocation."""
from pathlib import Path
import ast
import hashlib
import json

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
OLDPREP=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f'
OLDOUT=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli47-r308-7d5925db'
AUDIT=OLDOUT.parent/'cli47-r308-stopped-audit-3f62f862'
NEWOUT=OLDOUT.parent/'cli44-r309-c927f880'

def read(p): return json.loads(p.read_bytes())
def ref(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,x):
    with (HERE/name).open('xb') as f: f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def rep(body,old,new):
    if body.count(old)!=1: raise RuntimeError('Replacement count: '+old[:100])
    return body.replace(old,new,1)

frozen=read(OLDOUT/'execution.inputs.before-first-case.json')
current=[ref(Path(x['path'])) for x in frozen]
if current!=frozen: raise RuntimeError('ORIGINAL_COMPILED_INPUT_CHANGED')
save('reused7718.current.json',current)
additions=read(AUDIT/'runtime.additions.json')
if [ref(Path(x['path'])) for x in additions]!=additions: raise RuntimeError('PUBLIC_URI_RUNTIME_CHANGED')
save('uri65.current.json',additions)
old_roster=read(OLDPREP/'finite_selectors.json')
subset=[dict(x,original_index=index) for index,x in enumerate(old_roster['selectors']) if index>=3]
if len(subset)!=44 or sum(len(x['expected_leaf_names']) for x in subset)!=145: raise RuntimeError('ROSTER')
save('finite_selectors.v3.json',{'schema':'researchos.cli-bounded-continuation-roster.v1',
 'original47_roster_ref':ref(OLDPREP/'finite_selectors.json'),'selectors':subset,
 'excluded_original_indexes':[0,1,2],'excluded_pass_leafs':76,
 'closure_supplement_original_indexes':[3,4],'previously_not_run_original_indexes':list(range(5,47))})
save('reused_provenance.json',{'candidate':'b98738ac093ea55bb8700cfa724ddd9e6b2a1251',
 'original_prepare':ref(OLDOUT/'prepare.completed.json'),
 'original7718':ref(OLDOUT/'execution.inputs.before-first-case.json'),
 'original_graph':ref(OLDOUT/'go-packages.json'),
 'original_compile_before':ref(OLDOUT/'compile.inputs.before.json'),
 'original_compile_after':ref(OLDOUT/'compile.inputs.after.json'),
 'original_archives':ref(OLDOUT/'compiled.archives.before.json'),
 'original_generated':ref(OLDOUT/'generated.manifest.json'),
 'binaries':read(OLDOUT/'prepare.completed.json')['binaries'],
 'no_new_build':True,'stopped_review':ref(AUDIT/'review.json'),
 'first3_results':[ref(OLDOUT/'cases'/f'{i:02d}'/'result.json') for i in range(3)],
 'origin_retained':ref(AUDIT/'failure_origins.json'),
 'source8':ref(AUDIT/'source8.current.json')})

body=(OLDPREP/'runner.v2.py').read_text(encoding='utf-8')
body=rep(body,'OUT = ROOT / "execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli47-r308-7d5925db"',
 '''OUT = ROOT / "execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli44-r309-c927f880"
OLD_OUT = ROOT / "execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli47-r308-7d5925db"
OLD_PREP = ROOT / "execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f"''')
body=rep(body,'BIN = OUT / "bin"','BIN = OLD_OUT / "bin"')
body=rep(body,'grant = scope["cli47_execution"]','grant = scope["cli44_continuation"]')
body=rep(body,'manifest = HERE / "manifest.v2.json"','manifest = HERE / "manifest.v3.json"')
body=rep(body,'grant["prepared_manifest_v2_sha256"]','grant["prepared_manifest_v3_sha256"]')
body=rep(body,'grant["invocation_limit"] == 47 and grant["leaf_limit"] == 221','grant["invocation_limit"] == 44 and grant["leaf_limit"] == 145')
body=rep(body,'for row in read_json(HERE / "preparation_tools.v2.json"):','for row in read_json(OLD_PREP / "preparation_tools.v2.json"):')
# The remaining reference occurs only inside old prepare; remove that entire producer.
start=body.index('\ndef prepare(env):')
end=body.index('\ndef observe_child(',start)
body=body[:start]+'''
def freeze_reused_inputs():
    provenance = read_json(HERE / "reused_provenance.json")
    for key in ("original_prepare", "original7718", "original_graph", "original_compile_before",
                "original_compile_after", "original_archives", "original_generated", "stopped_review", "origin_retained", "source8"):
        expected = provenance[key]
        require(file_ref(expected["path"]) == expected, "REUSED_PROVENANCE_CHANGED:" + key)
    original = read_json(Path(provenance["original7718"]["path"]))
    _KNOWN_INPUTS.update(Path(x["path"]) for x in original)
    check_vector(original, OUT / "original7718.current-before.json")
    for expected in provenance["binaries"]:
        require(file_ref(expected["path"]) == expected, "REUSED_BINARY_CHANGED")
    current_runtime = runtime_vector()
    current_by_path = {x["path"]: x for x in current_runtime}
    for expected in read_json(HERE / "uri65.current.json"):
        require(current_by_path.get(expected["path"]) == expected, "URI_PRELOAD_INCOMPLETE:" + expected["path"])
    save(OUT / "runtime.before-first-case.json", current_runtime)
    paths = [x["path"] for x in original] + [x["path"] for x in current_runtime]
    paths.extend(p for p in HERE.iterdir() if p.is_file())
    paths.extend(provenance[key]["path"] for key in (
        "original_prepare", "original7718", "original_graph", "original_compile_before",
        "original_compile_after", "original_archives", "original_generated", "stopped_review", "origin_retained", "source8"))
    frozen = vector(paths)
    _KNOWN_INPUTS.update(Path(x["path"]) for x in frozen)
    save(OUT / "execution.inputs.before-first-case.json", frozen)
    save(OUT / "freeze.completed.json", {"candidate": CANDIDATE, "input_count": len(frozen),
        "reused_binaries": provenance["binaries"], "new_compile_count": 0, "cases_executed": 0})


def check_case_closure(frozen, directory, stage):
    runtime = runtime_vector()
    save(directory / ("runtime." + stage + ".json"), runtime)
    by_path = {x["path"]: x for x in frozen}
    require(all(by_path.get(x["path"]) == x for x in runtime), "RUNTIME_INPUT_DRIFT:" + stage)
    check_vector(frozen, directory / ("inputs." + stage + ".json"))

''' + body[end:]
body=rep(body,'require((OUT / "prepare.completed.json").is_file(), "PREPARE_REQUIRED")','require((OUT / "freeze.completed.json").is_file(), "REUSE_FREEZE_REQUIRED")')
body=rep(body,'read_json(HERE / "finite_selectors.json")["selectors"]','read_json(HERE / "finite_selectors.v3.json")["selectors"]')
body=rep(body,'require(len(roster) == 47, "ROSTER_LIMIT")','require(len(roster) == 44 and sum(len(x["expected_leaf_names"]) for x in roster) == 145, "ROSTER_LIMIT")')
body=rep(body,'check_vector(frozen, case_dir / "inputs.before.json")','check_case_closure(frozen, case_dir, "before")')
body=rep(body,'''            current_runtime = runtime_vector()
            require(all(frozen_by_path.get(x["path"]) == x for x in current_runtime), "NEW_RUNTIME_INPUT_AFTER_CASE")
            check_vector(frozen, case_dir / "inputs.after.json")''',
'''            check_case_closure(frozen, case_dir, "after-native")''')
body=rep(body,'''                    "invocation": optional_ref(invocation_path)})
        events =''', '''                    "invocation": optional_ref(invocation_path)})
            check_case_closure(frozen, case_dir, "after-fixtures")
        events =''')
body=rep(body,'result = {"selector": entry["selector"], "native_exit": 0,',
 'result = {"selector": entry["selector"], "original_index": entry["original_index"], "native_exit": 0,')
body=rep(body,'check_vector(frozen, OUT / "execution.inputs.after-all.json")',
 'check_case_closure(frozen, OUT, "after-all")')
start=body.index('\ndef main():')
body=body[:start]+'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", required=True)
    parser.add_argument("--scope-sha256", required=True)
    args = parser.parse_args()
    auth = authorize(args)
    # Reject pre-existing OUT outside try: no catch may append to an older sealed cohort.
    OUT.mkdir(parents=True, exist_ok=False)
    owns_output = True
    try:
        save(OUT / "execute.started.json", {"at": now(), "authorization": auth, "argv": sys.argv})
        initialize_owned_runtime()  # Sets dont_write_bytecode before helper imports.
        # Pure local string conversion preloads pathlib's urllib.request chain. No URL open/SQL.
        uri = CHECKOUT.as_uri()
        save(OUT / "pure-uri-preload.json", {"input": str(CHECKOUT), "result": uri,
            "network_or_SQL_call": False, "actual_function": "pathlib.Path.as_uri"})
        save(OUT / "runtime.initial-after-preload.json", runtime_vector())
        freeze_reused_inputs()
        execute(environment())
    except BaseException as error:
        if owns_output:
            observation_error = None
            try:
                preserve_failure_observations("execute")
            except BaseException as observation:
                observation_error = {"error_type": type(observation).__name__, "message": str(observation)}
            save(OUT / "execute.stopped.json", {"at": now(), "error_type": type(error).__name__, "message": str(error),
                "failure_observation_error": observation_error,
                "next_action": "STOP; preserve originals; no same-input retry", "source_changes": 0})
        raise


if __name__ == "__main__":
    main()
'''
tree=ast.parse(body)
if '\ndef prepare(' in body or 'cat-file' in body or '"test", "-c"' in body or 'taskkill' in body:
    raise RuntimeError('UNAUTHORIZED_PRODUCER_REMAINS')
with (HERE/'runner.v3.py').open('xb') as f: f.write(body.encode('utf-8'))
helper=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
spec={'decision':'CLI44_CONTINUATION_PREPARED_NOT_AUTHORIZED_NOT_EXECUTED',
 'candidate':'b98738ac093ea55bb8700cfa724ddd9e6b2a1251','runner':ref(HERE/'runner.v3.py'),
 'root_grant':{'cli44_continuation':{
    'candidate':'b98738ac093ea55bb8700cfa724ddd9e6b2a1251',
    'checkout':str(ROOT/'.local/independent-cli-exact8-0dcea526'),'output':str(NEWOUT),
    'prepared_manifest_v3_sha256':'<actual manifest.v3 SHA from handoff; excluded self/handoff>',
    'owned_process_helper_ref':ref(helper),'invocation_limit':44,'leaf_limit':145,
    'SDK_MODEL_EXTERNAL_PAID_CALLS':0}},
 'selectors':ref(HERE/'finite_selectors.v3.json'),'reused_provenance':ref(HERE/'reused_provenance.json'),
 'current_original_input_check':ref(HERE/'reused7718.current.json'),
 'uri_runtime_pins':ref(HERE/'uri65.current.json'),
 'old_controller':ref(OLDPREP/'runner.v2.py'),'old_failure':ref(AUDIT/'failure_origins.json'),
 'paths':{'new_output':str(NEWOUT),'reused_checkout':str(ROOT/'.local/independent-cli-exact8-0dcea526'),
    'reused_GOCACHE':str(ROOT/'.local/independent-cli-exact8-0dcea526/.local/cache'),
    'reused_WORK':str(ROOT/'.local/independent-cli-exact8-0dcea526/.local/work'),
    'reused_TEMP':str(ROOT/'.local/independent-cli-exact8-0dcea526/.local/temp'),
    'reused_bin':str(OLDOUT/'bin')},
 'input_change':'Pure local URI preload freezes all actual Python/OS modules, including observed65, before first case; gate before child, after native, after fixture export.',
 'controller_and_helper_imported_during_preparation':False,
 'runtime_freeze':'Full original Go graph/source/WORK-generated-testmain/importcfg/allarchives/exes current before plus actual controller/module/OS DLLs/new prepared files. Three full checks per selector. Original immutable sources and files are never rewritten.',
 'first3_reuse_boundary':'Original indexes0,1,2 native0/76leaf matched before/after runtime+known7718 without DB export import. Keep original cohort/binary/current pin; do not call them new run. Index3/4 closure-incomplete repeat only under new explicit inputs.',
 'counts':'44 exact selectors: original3+4 closure supplement and original5..46 never-run. Expected145, not yet PASS. Potential cross-cohort union76+145=221 only after actual completion.',
 'scope_limits':{'new_export':0,'new_compile':0,'product_source_edit':0,'SQL_schema_change':0,'Node_SDK_model_paid_external_provider':0,'held2': 'NOT_RUN','fullharness':'BUILD_ONLY_ORIGINAL_NOT_EXECUTED'},
 'Windows':'Original4 controls/3 signals unchanged. Their unchanged test helper internally builds fresh temporary CLI; logged actualhash/size must equal pinned reusedCLI bytes; watcher only copies matching ownTEMP bytes.',
 'fresh_fixtures':'New OUT/cases fixture roots for both supplement controls and42 never-run. Never reuse old DB or alter old outputs. Own temporary directory/cache may be reused by unchanged test helpers.',
 'failure':'First unexpected stops; no auto retry/reset. Every invoke exclusiveJob cleanup required. Finally raw observation preserved. Pre-existing OUT refusal writes nothing into it.',
 'launch':['<pinned Python>','-X','utf8','-I',str(HERE/'runner.v3.py'),'--scope','<Root309 actualscope>','--scope-sha256','<actualSHA>'],
 'source_acceptance':False,'formal_increment':0}
save('prepared_execution_spec.v3.json',spec)
save('static_audit.json',{'runner':ref(HERE/'runner.v3.py'),'AST':True,'helper':ref(helper),
 'current7718_equal':current==frozen,'public65_equal':True,'selectors':44,'expected_leaves':145,
 'new_go_invocations':0,'cases_executed':0,'helper_imported':False,
 'first3': [ref(OLDOUT/'cases'/f'{i:02d}'/'result.json') for i in range(3)],
 'original_status':'Five native0/78leaf, controller1 retained; source acceptance remains withheld.'})
entries=[]
for p in sorted(HERE.iterdir()):
    if p.is_file():
        x=ref(p); x['path']=p.name; entries.append(x)
save('manifest.v3.json',{'schema':'researchos.prepared-runner-manifest.v3','entries':entries,
 'count':len(entries),'self_excluded':True,'handoff_excluded':True,'external_helper':ref(helper)})
save('handoff.v3.json',{'decision':spec['decision'],'manifest':ref(HERE/'manifest.v3.json'),
 'runner':ref(HERE/'runner.v3.py'),'spec':ref(HERE/'prepared_execution_spec.v3.json'),
 'roster':ref(HERE/'finite_selectors.v3.json'),'static_audit':ref(HERE/'static_audit.json'),
 'reused_binaries':read(OLDOUT/'prepare.completed.json')['binaries'],
 'original_controller_failure':ref(AUDIT/'failure_origins.json'),
 'execution_count':0,'new_compile_count':0,'new_failure_origins':[]})
print(json.dumps({n:ref(HERE/n) for n in ('runner.v3.py','manifest.v3.json','prepared_execution_spec.v3.json','handoff.v3.json','finite_selectors.v3.json')},ensure_ascii=False))
