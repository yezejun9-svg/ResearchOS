import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'closure-and-finite-continuation-r309'
RECEIPTS = ROOT / 'execution/v2.4/receipts/W05/W05-99'


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def write(name, value):
    ast.parse(value)
    with (OUT / name).open('xb') as stream:
        stream.write(value.encode('utf-8'))
    return ref(OUT / name)


def change(code, old, new):
    assert code.count(old) == 1, old[:90]
    return code.replace(old, new, 1)


plan_path = RECEIPTS / 'cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json'
plan = json.loads(plan_path.read_bytes())
export_path = RECEIPTS / 'session_list_identity_independent_replay_codex/root-r309-534857db-public-jev/public-source-export.json'
export = json.loads(export_path.read_bytes())
old_names = {row['relative_path'] for row in export}
missing = [row for row in plan['git_resources'] if row['path'] not in old_names]
assert len(missing) == 31
git = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']['git']['path']
tree_raw = subprocess.check_output([git, 'ls-tree', '-r', '-z', '534857db99fa5e694987f877af74c322eaa2a0b3'], cwd=ROOT)
tree = {}
for entry in tree_raw.split(b'\0'):
    if not entry:
        continue
    meta, name = entry.split(b'\t', 1)
    mode, kind, blob = meta.decode('ascii').split()
    tree[name.decode('utf-8')] = {'mode': mode, 'kind': kind, 'git_blob': blob}
for pin in missing:
    assert tree[pin['path']]['kind'] == 'blob' and tree[pin['path']]['git_blob'] == pin['git_blob']
scope = json.loads((PREVIOUS / 'list_independent_scope.v2.json').read_bytes())
additional = dict(scope['public_JEV_sources'])
for pin in missing:
    additional[pin['path']] = {key: pin[key] for key in ['git_blob', 'sha256', 'bytes']}
assert len(additional) == 36
code = (PREVIOUS / 'list_replay.v2.py').read_text(encoding='utf-8')
assert ref(PREVIOUS / 'list_replay.v2.py')['sha256'] == 'a714295db60586264dd7afdb302b48dfaa18791fd49b66e85455824783c014ad'
code = code.replace('root-r309-534857db-public-jev', 'root-r310-534857db-public-plan').replace('independent-session-list-r309-534857db-public-jev', 'independent-session-list-r310-534857db-public-plan')
code = code.replace("list_independent_scope.v2.json", "list_independent_scope.json")
code = code.replace("assert cp['revision'] >= 309", "assert cp['revision'] >= 310")
start = code.index('PUBLIC_JEV = ')
end = code.index('\nRESOURCE_PLAN_REF = ', start)
code = code[:start] + 'PUBLIC_JEV = ' + repr(additional) + code[end:]
code = change(code, "    public_plan = load(plan_path)", "    public_plan = load(plan_path)\n    assert len(public_plan['git_resources']) == 518\n    assert all((EXPORT / pin['path']).is_file() for pin in public_plan['git_resources']), 'Known approved public compiler catalog export is incomplete'")
code = code.replace('Previously approved generic public Go compiler sources; no private truth/qualification data or test generator execution', 'All36 individually named already approved public Go compiler resources; no private runtime truth/qualification data or dependency test execution')
runner = write('list_replay.py', code)
scope.update(runner_ref=runner, status='AUTHORIZED_BY_CAS310_ONLY_NOT_EXECUTED',
    checkout=str(ROOT / '.local/independent-session-list-r310-534857db-public-plan'),
    output=str(RECEIPTS / 'session_list_identity_independent_replay_codex/root-r310-534857db-public-plan'),
    public_JEV_sources=additional, public_compiler_addition_count=36,
    new_additional_public_resources=missing,
    previous_failed_scope_ref=ref(PREVIOUS / 'list_independent_scope.v2.json'),
    previous_failed_driver_ref=ref(PREVIOUS / 'list_replay.v2.py'),
    second_failed_cohort_origin_ref=ref(OUT.parent / 'root-list14-launch-r309/failure_origin.json'),
    public_export='Original677 public Git files plus36 individually pinned resources already in the approved518 compiler catalog. Whole known catalog coverage required before anyGo tool. New713 export/cache/WORK/exe; no execution/qualification/third_party/private vault/userDB. Imported public dependency tests are source only, never selected or independently executed.',
    input_change='Complete known518 catalog reconciled at once,31 missing paths added after fiveJEV prior cohort. Fresh export/cache/WORK/exe; URI/Pythonpyc/OS/Go graph and explicitenv/ownedJob safeguards retained.',
    failure_chain='Two previous actual go-list omissions preserved at original separate input cohorts. No same-input retry, no count reset; new candidate source unchanged and complete public dependency input changes explicit.')
scope_ref = save('list_independent_scope.json', scope)
save('public-catalog-reconciliation.json', {'approved_plan_ref': ref(plan_path), 'prior_export_ref': ref(export_path),
    'candidate': '534857db99fa5e694987f877af74c322eaa2a0b3', 'prior_public_exports': len(export),
    'missing31': missing, 'actual_category_counts': {prefix: sum(x['path'].startswith(prefix + '/') for x in missing) for prefix in ['evaluation', 'ops']},
    'all31_actual_candidate_Git_blob_ids_match_approved_plan': True, 'future_exports': len(export) + len(missing),
    'all_known518_paths_required_before_Go': True, 'Go_compiler_native_cases_SQL_HTTP_MODEL': 0,
    'source_acceptance': False, 'formal_increment': 0})
g2_dir = RECEIPTS / 'provider_g2_finite_replay_preparation_codex/3ed3a3da52c3471d9ddc524897100842'
g2_original = (g2_dir / 'replay.py').read_text(encoding='utf-8')
assert ref(g2_dir / 'replay.py')['sha256'] == '27616fc015711e28ca1d1317251b5e6d7112ba49d1e2be392a63f12e58e9c116'
g2 = change(g2_original, 'HERE = Path(__file__).resolve().parent', 'HERE = Path(' + repr(str(g2_dir)) + ')')
g2 = change(g2, "            'RESEARCHOS_MU_BUNDLE':str(self.bundle),'RESEARCHOS_GO':str(self.go)})",
    "            'RESEARCHOS_MU_BUNDLE':str(self.bundle),'RESEARCHOS_GO':str(self.go),\n            'CGO_ENABLED':'0','GOOS':'windows','GOARCH':'amd64','GOAMD64':'v1','GOEXPERIMENT':'','GODEBUG':'','GOWORK':'off',\n            'GOFLAGS':'-buildvcs=false','GOMODCACHE':str(Path(spec['repo'])/'.local/gopath/pkg/mod'),\n            'GIT_NO_REPLACE_OBJECTS':'1','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull})")
g2 = change(g2, "        require(result['job_cleanup']['job_idle_confirmed'] and result['job_cleanup']['primary_exit_confirmed'], 'Job cleanup not confirmed')",
    "        cleanup=result.get('job_cleanup') or {}\n        require(result.get('resumed') is True and all(cleanup.get(key) is True for key in\n            ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'])\n            and cleanup.get('errors')==[], 'Full ownedJob cleanup not confirmed')")
g2 = change(g2, "[self.go,'list','-deps','-test','-json','./internal/domain']", "[self.go,'list','-deps','-test','-compiled','-json','./internal/domain']")
g2 = change(g2, "['GoFiles','CgoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','HFiles','SFiles','SysoFiles']",
    "['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles']")
g2 = change(g2, "                    p=d/rel; require(p.is_file(),'Missing actual graph input '+str(p)); paths.add(p)",
    "                    p=Path(rel) if Path(rel).is_absolute() else d/rel\n                    if not p.is_file() and key=='CompiledGoFiles':\n                        require(p.resolve().is_relative_to(self.work.resolve()),'Generated compiler input outside own work/cache')\n                        continue\n                    require(p.is_file(),'Missing actual graph input '+str(p)); paths.add(p)")
g2 = change(g2, "        save(self.phaseout/'generated.json',generated);save(self.phaseout/'archives.json',vector(archives))",
    "        actual_WORK={p for p in work.rglob('*') if p.is_file()}\n        save(self.phaseout/'actual_WORK.allfiles.json',vector(actual_WORK))\n        paths.update(actual_WORK)\n        save(self.phaseout/'generated.json',generated);save(self.phaseout/'archives.json',vector(archives))")
g2 = change(g2, "        self.guarded=prep['inputs']+vector(phase_resources|{self.out/'prepared.json'})",
    "        self.guarded=vector({Path(x['path']) for x in prep['inputs']}|phase_resources|{self.out/'prepared.json'})\n        for expected in prep['inputs']: verify(expected)")
g2 = change(g2, "            check_vector(critical_baseline,case/'critical.before.json')",
    "            check_vector(critical_baseline,case/'critical.before.json')\n            check_vector(self.guarded,case/'all-inputs.before.json')")
g2 = change(g2, "            snapshots+=self.snapshot_audit(case)",
    "            check_vector(self.guarded,case/'all-inputs.after-native.json')\n            snapshots+=self.snapshot_audit(case)\n            check_vector(self.guarded,case/'all-inputs.after-fixtures.json')")
g2_runner = write('g2_replay.v3.py', g2)
save('g2-controller-static-amendment.json', {'decision': 'ROOT_STATIC_CONTROLLER_AMENDMENT_NOT_EXECUTED',
    'original_preparation_handoff': ref(g2_dir / 'handoff.json'), 'original_runner': ref(g2_dir / 'replay.py'),
    'new_runner': g2_runner, 'original_spec_unchanged': ref(g2_dir / 'execution_spec.json'),
    'changes': ['Explicit lockedGo platform/env','Full assigned/resumed/cleanup flags','Complete compiled actualGo graph fields',
        'All actualWORK files retained/frozen','Prepared phase inputs and newgrant/runtime deduplicated with originalpins verified',
        'Complete percase before/nativeafter/fixtureafter vectors'],
    'roster_fixed29': True, 'phase_prepare_only_future_grant': True, 'no_export_compile_SQL_HTTP_SDK_MODEL_paid': True,
    'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'list_runner': runner, 'list_scope': scope_ref, 'additional31': len(missing), 'G2_new_controller': g2_runner}, ensure_ascii=True))
