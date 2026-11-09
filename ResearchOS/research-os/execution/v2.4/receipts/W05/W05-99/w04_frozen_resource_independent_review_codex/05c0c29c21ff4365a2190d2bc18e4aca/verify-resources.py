import json,hashlib,ast
from pathlib import Path,PurePosixPath
D=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
O=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/w04-frozen-resource-verification-root-4e17c2a0972847f5'
K=R.parent/'ResearchOS_Implementation_Package_v2.4'
F=R/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/frozen-package-input'
EXPECT='4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
refs={}
def j(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve();b=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def ck(r):
 a=pin(r['path']);assert (a['sha256'],a['bytes'])==(r['sha256'],r['bytes']),r['path']
 refs[a['path'].casefold()]=a;return a
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
for p in O.iterdir():
 assert p.is_file();ck(pin(p))
assert len(list(O.iterdir()))==4
c=j(O/'resource-closure.actual.json')
assert pin(O/'resource-closure.actual.json')['sha256']=='a6ab1753706de986c0ab02cf77cd15a32489fedd3768f9fdab115a87e075c653'
assert c['manifest_sha256']==EXPECT and Path(c['package_input'])==F
assert c['manifest_member_count']==147 and c['snapshot_file_count']==148 and c['guarded_reference_count']==299
assert c['go_or_native_cases_executed']==c['model_requests']==0 and not c['formal_acceptance']
assert (K/'PACKAGE_MANIFEST.json').read_bytes()==(F/'PACKAGE_MANIFEST.json').read_bytes()
assert pin(F/'PACKAGE_MANIFEST.json')['sha256']==EXPECT
manifest=j(F/'PACKAGE_MANIFEST.json');assert len(manifest['files'])==147
names=[]
expected_guards={}
for item in manifest['files']:
 rel=PurePosixPath(item['path']);assert not rel.is_absolute() and '..' not in rel.parts and ':' not in item['path'] and '\\' not in item['path']
 names.append(item['path'])
 for base in (K,F):
  p=base.joinpath(*rel.parts);assert p.resolve().is_relative_to(base.resolve())
  r=ck(dict(path=str(p),sha256=item['sha256'],bytes=item['size_bytes']))
  expected_guards[r['path'].casefold()]=r
assert len(set(x.casefold() for x in names))==147
snapshot=list(F.rglob('*'))
assert all(not p.is_symlink() and not p.is_junction() for p in snapshot)
actual_names={p.relative_to(F).as_posix() for p in snapshot if p.is_file()}
assert len(actual_names)==148 and actual_names==set(names)|{'PACKAGE_MANIFEST.json'}
for p in (K/'PACKAGE_MANIFEST.json',F/'PACKAGE_MANIFEST.json',Path(c['python_ref']['path']),O/'verify_w04_frozen_resources.only.py',R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'):
 r=ck(pin(p));expected_guards[r['path'].casefold()]=r
assert len(expected_guards)==299
actual_guards={str(Path(x['path']).resolve()).casefold():ck(x) for x in c['source_refs']}
assert actual_guards==expected_guards
g=j(O/'source-guard.cleanup.actual.json')
assert g['verification']=='PASSED' and g['closed'] and not g['errors'] and g['failure'] is None and g['retained_handles_count']==0 and len(g['entries'])==299
cleanup_guards={}
for x in g['entries']:
 assert x['verified'] and x['final_path_match'] and x['closed']
 r=ck(x);cleanup_guards[r['path'].casefold()]=r
assert cleanup_guards==expected_guards
assert c['python_ref']['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
assert c['required_environment']==dict(RESEARCHOS_W04_PACKAGE_INPUT=str(F),PATH_python_directory=str(Path(c['python_ref']['path']).parent))
assert len(c['canonical_unchanged_refs'])==4
for r in c['canonical_unchanged_refs']:ck(r)
assert j(R/'execution/v2.4/checkpoint.json')['revision']==356
io=j(O/'original-tool-io.json');result=io['result']
assert result['chunk_id']=='e1646a' and result['exit_code']==0
lines=result['output'].splitlines();assert lines[-1]=='ROOT_PYTHON_EXIT=0'
out=json.loads(lines[0])
assert out=={k:c[k] for k in ('status','manifest_member_count','snapshot_file_count','guarded_reference_count','formal_acceptance')}
ast.parse((O/'verify_w04_frozen_resources.only.py').read_bytes())
for n in ('internal/domain/w04_current_context_test.go','internal/domain/context_test.go','internal/domain/import.go'):ck(pin(R/n))
requirements=dict(current_A01=dict(source='internal/domain/w04_current_context_test.go:259',environment='RESEARCHOS_W04_PACKAGE_INPUT',manifest_sha256=EXPECT,copy_to='t.TempDir()/package',full_CopyFS_snapshot_count=148),legacy_A01=dict(source='internal/domain/context_test.go:252',package_source='../../spec/v2.0',python_lookup='exec.Command("python",...) at313',uses_v24_frozen_environment=False),python_path_directory=c['required_environment']['PATH_python_directory'],future_actual_runner_must_bind_PATH_and_source_runtime_guards=True,all_W04_test_prerequisites_not_certified=True)
e=dict(resource_closure_ref=pin(O/'resource-closure.actual.json'),original_IO=io,manifest_member_count=147,snapshot_file_count=148,guarded_reference_count=299,exact_guard_union_verified=True,no_extra_snapshot_files=True,no_snapshot_symlinks_or_junctions=True,all_guards_final_path_verified_closed=True,retained_handles=0,current_canonical_CP356_refs=c['canonical_unchanged_refs'],requirements=requirements,resource_component_only=True,Go_native_model_SQL_Owner_executions=0,base_refs=list(refs.values()),review_diagnostic_ordinal=812)
r=save('evidence.json',e)
print(json.dumps(dict(directory=str(D),evidence=r,base_refs=len(refs),manifest_members=147,snapshot_files=148,guards=299,drift=0),ensure_ascii=True))
