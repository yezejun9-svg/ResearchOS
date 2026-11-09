import json,hashlib,ast,difflib
from pathlib import Path
D=Path(__file__).resolve().parent
B=Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99')
O=B/'native_migration_atomic_publication_revision_codex/1a11d9c912f7c13799a37e93'
P=B/'native_migration_root_controller_source_codex/949c31b5ce9172756b85a2aa388'
Q=B/'native_root_controller_independent_review_codex/323c2c64d2614efa81ffaf75ad5bf12b'
refs={}
def j(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def ck(r):
 a=pin(r['path']);assert (a['sha256'],a['bytes'])==(r['sha256'],r['bytes']),r['path']
 refs[a['path']]=a;return a
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
hpin=ck(dict(path=str(O/'HDF.json'),sha256='89b718509b1b629022eb989e52f5cf6bdb4ca0643c03e038ea06c993a4cf9d82',bytes=7690))
h=j(hpin['path']);m=j(ck(h['manifest_ref'])['path'])
assert h['manifest_ref']['sha256']=='680c0e9253025f5374f1d4c82f162ae24c329c9affc27192e5307393a916d118'
members=m['members'];assert len(members)==13
for r in members.values():ck(r)
assert {p.name for p in O.iterdir()}==set(members)|{'MF.json','HDF.json'}
oldh=j(ck(h['prior_handoff_ref'])['path']);oldm=j(ck(h['prior_manifest_ref'])['path'])
oldmembers=oldm['members'];oldmembers=list(oldmembers.values()) if isinstance(oldmembers,dict) else oldmembers
assert len(oldmembers)==11
for r in oldmembers:ck(r)
pins=j(ck(h['public_input_pins_ref'])['path'])
for r in pins['inputs']+[pins['go_producer_reference']]:ck(r)
assert len(pins['inputs'])+1==9
for n in ('HDF.json','MF.json'):ck(pin(Q/n))
old=(P/'root_native_migration_controller.py').read_bytes()
new=(O/'root_native_migration_controller.py').read_bytes()
assert hashlib.sha256(new).hexdigest()=='14cba01f91b7d9f322243c0df041a29337c422f72ea96214337047522dec8c83'
inverse=new.decode();changes=j(O/'controller-inverse-changes.json')
assert len(changes)==11
for x in reversed(changes):
 assert inverse.count(x['after'])==1
 inverse=inverse.replace(x['after'],x['before'],1)
assert inverse.encode()==old
trees=[ast.parse(x) for x in (old,new)]
maps=[{x.name:x for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))} for t in trees]
dump=lambda n:ast.dump(n,include_attributes=False)
changed=sorted(k for k in maps[0] if dump(maps[0][k])!=dump(maps[1][k]))
assert changed==['_approval','_phase','poll','serve','snapshot','write_new']
assert sorted(set(maps[1])-set(maps[0]))==['PublicationPending','_complete_public_json']
assert not set(maps[0])-set(maps[1])
unchanged=sorted(k for k in maps[0] if k not in changed)
for n in ('windows_owned_observed.py','root-controller-api.json'):
 assert (O/n).read_bytes()==(P/n).read_bytes()
assert (O/'CONTRACT.md').read_bytes().startswith((P/'CONTRACT.md').read_bytes())
expected_diff=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='949c/root_native_migration_controller.py',tofile='atomic-revision/root_native_migration_controller.py'))
diff_equal=expected_diff.encode()==(O/'controller-atomic-publication.patch').read_bytes()
w=maps[1]['write_new']
attrs=[x for x in ast.walk(w) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]
assert any(x.func.attr=='rename' for x in attrs)
assert not any(x.func.attr=='replace' for x in attrs)
unlinks=[x for x in attrs if x.func.attr=='unlink']
assert len(unlinks)==1 and isinstance(unlinks[0].func.value,ast.Name) and unlinks[0].func.value.id=='temporary'
parser=maps[1]['_complete_public_json']
handlers=[x for x in ast.walk(parser) if isinstance(x,ast.ExceptHandler)]
assert len(handlers)==1
exceptions=[ast.unparse(x) for x in handlers[0].type.elts]
assert exceptions==['FileNotFoundError','json.JSONDecodeError','UnicodeDecodeError']
failure=j(ck(h['failure813_origin_ref'])['path'])
assert failure['ordinal']==813 and failure['actualOuter']==failure['actualPython']==1 and failure['native'] is None
assert failure['actual_output']['chunk_id']=='020cc5' and failure['actual_output']['exit_code']==1
assert failure['actual_corrected_output']['chunk_id']=='0925a7' and failure['actual_corrected_output']['exit_code']==0
assert failure['failed_before_controller_output_write'] and not failure['controller_import_or_execution']
for k in ('failed_construct_script_ref','corrected_script_ref'):ck(failure[k])
io=j(ck(h['original_tool_io_ref'])['path'])
assert io['failed_construct']['output']==failure['actual_output']
assert io['successful_construct']['output']==failure['actual_corrected_output']
assert not h['formal'] and not h['production_ready'] and not h['execution_authority']
e=dict(source_handoff_ref=hpin,source_manifest_ref=h['manifest_ref'],source_members=13,source_files=15,old_manifest_members_verified=11,direct_input_pins_verified=9,controller_inverse_exact=True,inverse_changes=11,changed_existing_functions=changed,added=['PublicationPending','_complete_public_json'],unchanged_function_AST_names=unchanged,observer_and_API_byte_equal=True,contract_old_prefix_preserved=True,patch_matches_independent_diff=diff_equal,unpinned_pending_exception_types=exceptions,only_unlink_target='temporary',Root_four_public_cases_source_accepted=True,source_finding='NATIVE_CONTROLLER_NONATOMIC_PUBLIC_JSON_PUBLICATION',finding_source_fix_verified=True,finding_actual_fix_verified=False,original_813=failure,original_tool_IO_ref=h['original_tool_io_ref'],historical20_external_pins_reexecuted=False,target_imports_or_execution=0,new_mechanical_errors=0,base_refs=list(refs.values()))
r=save('evidence.json',e)
print(json.dumps(dict(directory=str(D),evidence=r,base_refs=len(refs),changed=changed,independent_diff_equal=diff_equal,inverse_equal=True,source_members=13,old_members=11,new_mechanical_errors=0),ensure_ascii=True))
