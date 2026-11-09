"""Independent CP571 source/pure-mock/offline-build review. Never executes helper."""
import ast,datetime,hashlib,json,os,runpy,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent.parent
PREP=BASE/'product_host_native_20261028'/'native-init-diagnosis-02'/'environment-probe'/'preparation02'
SCOPE=BASE/'resume_cp528_codex'/'20261025-current-chat'/'continuation-cp571'/'Native-folder-environment-preparation02-scope.json'
OUT=ROOT/'preparation02-5fcc8477'
OUT.mkdir(exist_ok=False)
SNAP=OUT/'input-snapshots';SNAP.mkdir()
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
scope=load(SCOPE);prep=load(PREP/'PREPARATION.json')
assert ref(SCOPE)['sha256']=='dff6c62374875c158d612c0cf50c8cc5472a70cff789b5b1b2ce8c5f274cdfa1'
assert ref(PREP/'PREPARATION.json')['sha256']=='a93ee48dc114d63f9b54fd99d4b6b167c31edad87343db6a33101d30ec0ff567'
assert ref(PREP/'controller.py')['sha256']=='5fcc8477878a111f30800db819572200e6ab23b9e92da3e98d1ec5a6bf6dcc75'
assert ref(PREP/'RUN-SCOPE-TEMPLATE.json')['sha256']=='c74838277b64241fa61c229e9031ad67ba22a8044a122ee5ffcf1bd7df38c22a'
assert scope['native_execution_authorized'] is False and prep['native_execution_authorized'] is False
assert load(PREP/'RUN-SCOPE-TEMPLATE.json')['native_execution_authorized'] is False
refs=[]
for p in sorted(PREP.iterdir()):
    if p.is_file():
        (SNAP/p.name).write_bytes(p.read_bytes());refs.append(ref(p))
(SNAP/'ROOT-PREPARATION-SCOPE.json').write_bytes(SCOPE.read_bytes());refs.append(ref(SCOPE))
for label,row in prep['files'].items():
    p=Path(row['path']);actual=ref(p)
    assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],label
    refs.append(actual)
    if label in ('source','transformed','main','go_mod','go_sum'):
        (SNAP/(label+'-'+p.name)).write_bytes(p.read_bytes())
source=Path(prep['files']['source']['path']).read_bytes()
assert source.count(b'package host')==1
assert Path(prep['files']['transformed']['path']).read_bytes()==source.replace(b'package host',b'package main',1)
assert Path(prep['files']['main']['path']).read_text(encoding='utf-8').count('chooseNativeFolderWindows(')==1
save('INPUTS.json',refs)
ast.parse((SNAP/'controller.py').read_text(encoding='utf-8'))
test_argv=[sys.executable,'-B',str(SNAP/'test_controller_mock.py'),'-v']
result=subprocess.run(test_argv,capture_output=True,check=False)
(OUT/'pure-mocks.stdout.raw').write_bytes(result.stdout);(OUT/'pure-mocks.stderr.raw').write_bytes(result.stderr)
save('PURE-MOCK-COMMAND.json',{'argv':test_argv,'exit':result.returncode,'actual_helper_runs':0,
    'stdout':ref(OUT/'pure-mocks.stdout.raw'),'stderr':ref(OUT/'pure-mocks.stderr.raw')})
assert result.returncode==0,result.stderr

g=runpy.run_path(str(SNAP/'controller.py'))
waiting={'scope_sha256':'scope','controller_pid':111,'helper_pid':222,'release_nonce':'nonce',
    'at':'2026-10-28T00:00:00+00:00'}
valid={'schema':'researchos.native-folder-environment-root-release.v1','actor':'codex:/root',
    'scope_sha256':'scope','controller_pid':111,'helper_pid':222,'release_nonce':'nonce',
    'root_confirmed_identity_absence':True,'confirmed_absent_at':'2026-10-28T00:00:01+00:00'}
negative=[]
for label,key,value in [('actor','actor','wrong'),('scope','scope_sha256','wrong'),('controller','controller_pid',112),
                        ('helper','helper_pid',223),('nonce','release_nonce','wrong'),('absence','root_confirmed_identity_absence',False),
                        ('timestamp','confirmed_absent_at','2026-10-27T00:00:00+00:00')]:
    sample=dict(valid);sample[key]=value
    p=OUT/(label+'.release-fixture.json');p.write_text(json.dumps(sample),encoding='utf-8')
    assert g['release_valid'](p,waiting) is False,label
    negative.append(label)
save('INDEPENDENT-RELEASE-PROBES.json',{'status':'PASS','rejected_release_fields':negative,'actual_helper_runs':0})

build=load(PREP/'build-command.json');build_result=load(PREP/'build-result.json')
assert build_result['exit_code']==0 and build['version_exit']==0
for name,value in {'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOENV':'off','GOWORK':'off','GOFLAGS':'-mod=readonly','CGO_ENABLED':'0'}.items():
    assert build['env'][name]==value
for row in build['inputs'].values():
    actual=ref(Path(row['path']));assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']
artifact=Path(scope['artifact_root']).resolve()
assert Path(prep['files']['helper']['path']).resolve().parent==artifact
rebuild_dir=artifact/'independent-review-5fcc8477';rebuild_dir.mkdir(exist_ok=False)
rebuild=rebuild_dir/'native-folder-environment.exe'
argv=list(build['argv'])
assert argv[1:5]==['build','-trimpath','-buildvcs=false','-ldflags=-buildid=']
assert argv[5]=='-o'
assert Path(argv[0]).resolve()==Path(prep['files']['go_exe']['path']).resolve()
assert [Path(p).resolve() for p in argv[7:]]==[Path(prep['files'][label]['path']).resolve() for label in ('main','transformed')]
argv[6]=str(rebuild)
save('INDEPENDENT-BUILD-COMMAND.json',{'argv':argv,'cwd':build['cwd'],'env':build['env'],
    'source_command_ref':ref(PREP/'build-command.json'),'purpose':'offline compile only; never execute resulting helper'})
result=subprocess.run(argv,cwd=build['cwd'],env=build['env'],capture_output=True,check=False)
(OUT/'independent-build.stdout.raw').write_bytes(result.stdout)
(OUT/'independent-build.stderr.raw').write_bytes(result.stderr)
save('INDEPENDENT-BUILD-RESULT.json',{'exit':result.returncode,'output':ref(rebuild) if rebuild.exists() else None,
    'stdout':ref(OUT/'independent-build.stdout.raw'),'stderr':ref(OUT/'independent-build.stderr.raw'),
    'canonical_ref':prep['files']['helper'],'binary_equal':rebuild.exists() and rebuild.read_bytes()==Path(prep['files']['helper']['path']).read_bytes(),
    'actual_helper_runs':0})
assert result.returncode==0,result.stderr
assert rebuild.read_bytes()==Path(prep['files']['helper']['path']).read_bytes()
report={'schema':'researchos.independent-native-folder-environment-preparation-review.v2',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'SOURCE_AND_OFFLINE_BUILD_ACCEPTED_FOR_SEPARATE_FINITE_AB_SCOPE',
    'controller_source_accepted':True,'chooser_source_fidelity_accepted':True,'build_provenance_accepted':True,
    'actual_native_runs':0,'actual_helper_runs':0,'formal_increment':0,'findings':[],
    'fixed_preparation_ref':ref(PREP/'PREPARATION.json'),'controller_ref':ref(PREP/'controller.py'),
    'helper_ref':prep['files']['helper'],'template_ref':ref(PREP/'RUN-SCOPE-TEMPLATE.json'),
    'resolved_findings':[
        'E1: pre-spawn contract binds controller/scope/nonce without invented helper PID. Successful Popen child remains in the enclosing try frame before stream-close and postspawn work. Every postspawn BaseException enters persistent hold; reporting, signal and nested sleep errors are contained. Release requires exact Root-bound record and naturally terminated retained child handle.',
        'E2: exact offline command/cwd/environment/exit/stdout/stderr and Go/module inputs are captured and verified. Independent rebuild in a new approved artifact subdirectory produced byte-identical helper SHA92573aacf6f2caab9baead612a13cf0eef688fc1e5a4177ac6bf5b1cbfa7a463.'
    ],
    'boundary_checks':['Copied chooser differs only package host to package main; no COM/callback/flags change; main invokes chooser once.',
        'A uses the frozen Core Windows seven-key allowlist; B differs only SystemDrive. Same isolated directories/hint, helper binary and hidden startup; one process/case, A then B.',
        'Owned IDCANCEL follows retained handle creation-time plus fresh unique PID-owned dialog/HWND validation; no global input, kill, product launch or retry.',
        'Run-scope checks exact hashes, candidate clean worktree, fresh bounded roots and2-call limit. Current template remains native_execution_authorized=false.'],
    'scope_requirements':['Root must issue new exact finite A/B scope; plain Python without -O/PYTHONOPTIMIZE is required because authorization/input guards use assert.',
        'Unexpected condition aborts later cases and retains parent/handle until exact scoped Root release; retain all failure evidence.',
        'Any A2 or product validation is separately scoped. Direct helper result is diagnostic, not product qualification.'],
    'limitations':['Pure mocks and source/offline build only; no native GUI or helper execution.',
        'A/B share fresh state and fixed ordering; an observed difference can be affected by prior-case state. Do not infer product causality without follow-up.',
        'Polling may miss transient windows; failure to enumerate is not proof a window never existed.',
        'Partial receipt writes can fail closed indefinitely; preservation is proven for injected exceptions, not automatic recovery from every damaged file.'],
    'evidence_refs':[ref(OUT/'INPUTS.json'),ref(OUT/'PURE-MOCK-COMMAND.json'),ref(OUT/'INDEPENDENT-RELEASE-PROBES.json'),ref(OUT/'INDEPENDENT-BUILD-COMMAND.json'),ref(OUT/'INDEPENDENT-BUILD-RESULT.json')]}
save('REVIEW.json',report)
print(json.dumps(ref(OUT/'REVIEW.json'),ensure_ascii=False))
