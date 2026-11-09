from pathlib import Path
import json,hashlib,ast
own=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/native_private_stdin_helper_revision_codex/320740c9ef7c4dbaa6cae48633aa8e60');prior=own.parent.parent/'native_private_stdin_helper_source_codex/d6e8f35ea16d42c9b7f30c91faec090d'
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,v):(own/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (own/'HDF.json').exists() and not (own/'MF.json').exists()
pins=json.loads((own/'base-pins.json').read_bytes())
for p in pins:assert ref(Path(p['path']))==p
sources=['windows_owned_private_stdin.py','private_pipe_public_probe.py','root_verify_private_pipe.py']
for name in sources:ast.parse((own/name).read_text(encoding='utf-8'),filename=name)
e=json.loads((own/'static-evidence.json').read_bytes())
assert e['prior_process_lifecycle_suffix_equal_after_line_ending_normalization'] and not e['raw_lifecycle_suffix_byte_equality_claimed']
driver=(own/'root_verify_private_pipe.py').read_text(encoding='utf-8')
assert driver.count('"-I", "-S", "-B", "-X", "utf8"')==2
assert (own/'private_pipe_public_probe.py').read_bytes()==(prior/'private_pipe_public_probe.py').read_bytes()
members={str(p.relative_to(own)).replace('\\','/'):ref(p) for p in sorted(own.rglob('*')) if p.is_file()}
write('MF.json',{'schema':'researchos.source-manifest.v1','formal':False,'members':members,'member_count':len(members),'source_refs':{name:members[name] for name in sources},'base_refs':pins,'input_drift_count':0})
write('HDF.json',{'schema':'researchos.native-private-stdin-helper-revision-handoff.v1','status':'SOURCE_IMPLEMENTED_PENDING_ROOT_NATIVE_TESTS_AND_INDEPENDENT_REVIEW','sourceStatus':'EXECUTION_REPORTED','formal':False,'production_ready':False,'execution_authority':False,'source_root':str(own),'source_file_count':3,'source_refs':{name:members[name] for name in sources},'manifest_ref':ref(own/'MF.json'),'previous_source_handoff':ref(prior/'HDF.json'),'previous_source_manifest':ref(prior/'MF.json'),'contract_ref':ref(own/'CONTRACT.md'),'patch_ref':ref(own/'revision.patch'),'source_finding_ref':ref(own/'source-finding.json'),'static_evidence_ref':ref(own/'static-evidence.json'),'original_tool_io_ref':ref(own/'original-tool-io.json'),'failure_origins':[ref(own/'failure-origin.794.json'),ref(own/'failure-origin.795.json')],'failed_partial_795_refs':ref(own/'failed-partial-795-refs.json'),'input_pin_count':len(pins),'input_drift_count':0,'process_lifecycle_suffix_equal_after_line_ending_normalization':True,'raw_suffix_byte_equality_claimed':False,'per_invocation_capacity_empty_and_write_deadline_guards':True,'public_probe_python_flags':['-I','-S','-B','-X','utf8'],'scope':'Root-only private stdin adjunct; not production native authority acceptance','api':'run_owned_private_stdin(argv,cwd,env,stdout,stderr,timeout,private_input,creation_flags=0)','actual_author_execution':{'python_source_metadata_and_ast':True,'native_calls':False,'child_processes':False,'go':False,'sql':False,'provider':False,'signing':False,'private_resource_reads':False,'old_sealed_source_writes':False,'Main_or_canonical_writes':False},'remaining_gates':['Root independent Source review','Root six public-dummy native cases with actual receipts and cleanup','Root accepts helper before any real credential delivery','Migration synthetic fixture bridge and real nonzero token positive/hostile matrix remain unimplemented','Distinct exact-abandonment native positive still requires matched actual historical closure']})
for key,p in members.items():assert ref(own/key)==p
for p in pins:assert ref(Path(p['path']))==p
assert json.loads((own/'HDF.json').read_bytes())['manifest_ref']==ref(own/'MF.json')
print(json.dumps({'HDF':ref(own/'HDF.json'),'MF':ref(own/'MF.json'),'source_refs':{name:ref(own/name) for name in sources},'failure_refs':[ref(own/'failure-origin.794.json'),ref(own/'failure-origin.795.json')],'member_count':len(members),'input_pins':len(pins),'input_drift_count':0},ensure_ascii=True))

