import difflib,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path)), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
def write(name,obj):
    with (OUT/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
source=pin(OUT/'root_coordinator.py')
for name in ('input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json','input-intake.json'):
    path=OUT/name;doc=json.loads(path.read_bytes())
    doc['source_ref' if name in ('independent-source-review.template.json','input-intake.json') else 'coordinator_source_ref']=source
    path.write_bytes((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode())
origin_path=OUT/'failure-origin.builder.original-tool-io.json'
origin=json.loads(origin_path.read_bytes());origin['root_failure_number']=716
origin_path.write_bytes((json.dumps(origin,ensure_ascii=False,indent=2)+'\n').encode())
current=(OUT/'build_packet.py').read_bytes()
new=b"    assert Path(current['path']) == Path(ref['path']) and current['sha256'] == ref['sha256'] and current['bytes'] == ref['bytes'], role\n"
old=b'    assert current == ref, role\n'
assert current.count(new)==1
failed=current.replace(new,old)
with (OUT/'build_packet.failed.recovered.py').open('xb') as f:f.write(failed)
for name,a,b in [('builder.forward.diff',failed,current),('builder.inverse.diff',current,failed)]:
    text=''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='builder-before',tofile='builder-after'))
    with (OUT/name).open('xb') as f:f.write(text.encode())
write('builder-correction-evidence.json',{'failure':716,'failed_source_ref':pin(OUT/'build_packet.failed.recovered.py'),'corrected_source_ref':pin(OUT/'build_packet.py'),'recovery':'Exact one-line inverse reconstruction after failure; not a claimed pre-failure snapshot','full_bytes_inverse_roundtrip':failed.replace(old,new)==current,'original_tool_io_ref':pin(origin_path)})
fixed=json.loads((OUT/'fixed-pins.json').read_bytes())
checks=[]
for role,ref in fixed.items():
    actual=pin(ref['path']);match=Path(actual['path'])==Path(ref['path']) and actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
    checks.append({'role':role,'ref':ref,'matches':match})
assert all(x['matches'] for x in checks)
controls=json.loads((OUT/'source-controls.v3.json').read_bytes())
assert controls['candidate_source_ref']==source and controls['passed']==controls['total']==40
write('final-input-recheck.json',{'inputs':checks,'drift':0,'checked_roles':len(checks),'canonical_or_Main_writes':0})
write('source-status.json',{'decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW','source_ref':source,'controls_ref':pin(OUT/'source-controls.v3.json'),'controls_passed':40,'candidate_entry_calls':0,'candidate_WinAPI_calls':0,'candidate_SQL_calls':0,'candidate_native_processes':0,'provider_requests':0,'Main_canonical_writes':0,'execution_grant_issued':False,'runtime_qualification':False,'formal_acceptance':False,'new_failures':[710,711,712,716],'open':['SUCCESSFUL_ROOT_BOOTSTRAP_INPUT','INDEPENDENT_COORDINATOR_SOURCE_REVIEW','ACTUAL_PARENT_HOST_C7_LIFECYCLE','ACTUAL_PROVIDER_RECONCILIATION','FORMAL_ACCEPTANCE']})
members=[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
manifest=write('manifest.json',{'schema':'researchos.source-packet-manifest.v1','actor_id':'codex:/root/command_queue_impl','members':members,'member_count':len(members),'input_refs':list(fixed.values()),'excludes_self_and_handoff_to_avoid_hash_cycle':True})
handoff=write('handoff.json',{'schema':'researchos.root-sdk-coordinator-source-handoff.v1','actor_id':'codex:/root/command_queue_impl','decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW','manifest_ref':manifest,'source_ref':source,'fixed_pins_ref':pin(OUT/'fixed-pins.json'),'report_ref':pin(OUT/'REPORT.md'),'controls_ref':pin(OUT/'source-controls.v3.json'),'no_provider_template_ref':pin(OUT/'input.no-provider.template.json'),'model_trial_template_ref':pin(OUT/'input.model-trial.template.json'),'root_execution_authority_template_ref':pin(OUT/'root-execution-authority.template.json'),'independent_review_template_ref':pin(OUT/'independent-source-review.template.json'),'failures':[{'root_failure_number':n,'origin_ref':pin(OUT/('failure-origin.builder.original-tool-io.json' if n==716 else 'failure-origin.'+str(n)+'.original-tool-io.json'))} for n in (710,711,712,716)],'candidate_native_SQL_provider_calls':0,'Main_canonical_writes':0,'runtime_qualification':False,'formal_acceptance':False,'stopped':True})
print(json.dumps({'handoff_ref':handoff,'manifest_ref':manifest,'source_ref':source,'member_count':len(members),'input_roles':len(fixed),'input_drift':0,'controls':40}))
