from pathlib import Path
import datetime,json,types
p=Path(__file__).with_name('inspect_public21_source.py');h=types.ModuleType('support');h.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),h.__dict__)
support_path=h.R/'execution/v2.4/receipts/W09/W09-99/full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
m=h.inert(support_path);m.D=h.D
original=m.capture('c8e2f1',0,0,1143)
s=json.loads((h.D/'source-observations.json').read_bytes());r=json.loads((h.D/'runtime-source-review.json').read_bytes());closed=json.loads((h.D/'runtime-source-review.guard.closed.json').read_bytes())
assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
failed_ids=[x['id'] for x in r['failed']];assert failed_ids==['leaf78-input-closure-current-held']
manifest_ref=r['leaf_input_manifest_ref'];assert h.pin(manifest_ref['path'])==manifest_ref
leaf_manifest=json.loads(Path(manifest_ref['path']).read_bytes())
contract=s['contracts']['runner'];caller=h.inert(h.N/'public21_root.source.py');caller._base=h.inert(s['source_handoff']['OC3_source_ref']['path'])
resource_map={caller.canonical(x['path']):x for x in r['held_resource_refs']}
refs=leaf_manifest['references']
checks=[]
def check(name,ok,details=None):checks.append(dict(id=name,passed=bool(ok),details=details,kind='INDEPENDENT_SOURCE_OR_REUSED_HELD_PIN_CHECK_NOT_PRODUCT'))
check('leaf-input-manifest-declared-refs-all-in-already-held-current-closure',all(caller.canonical(x['path']) in resource_map and caller.same_ref(x,resource_map[caller.canonical(x['path'])]) for x in refs),{'actual_declared_count':len(refs),'fixed_count_not_an_authority_gate':True,'pin_reacquisition':False})
mandatory=[contract[key] for key in ('old21_control','old21_backup','source_guard','owned_job','public22_helpers_ref')]+list(contract['frozen_runtime_refs'].values())
check('real-contract-mandatory-tool-and-frozen-SQL-input-membership',all(caller.canonical(x['path']) in resource_map and caller.same_ref(x,resource_map[caller.canonical(x['path'])]) for x in mandatory),{'contract_ref':s['source_handoff']['runner_source_refs']['contract_ref'],'mandatory_count':len(mandatory),'inferred_member_counts':False})
numbered=sorted(int(Path(relative).name[:4]) for relative in contract['frozen_runtime_refs'] if Path(relative).suffix=='.sql' and Path(relative).name[:4].isdigit())
check('frozen-numbered21-and-real-session-addon-source-bindings',numbered==list(range(1,22)) and 'migrations/sqlite/next_v24_sessions.sql' in contract['frozen_runtime_refs'],{'numbered':numbered,'actual_SQL_execution':False})
check('no-generated-private-owner-ref-in-runtime-inputs',not any('/private/owner.json' in x['path'].replace('\\','/').casefold() for x in r['held_resource_refs']),{'Owner_content_reads_or_hashes':0})
check('required-loaded-DLL-and-Python-current-resource-pins-reused',all(e['verified'] and e['final_path_match'] and e['closed'] for e in closed['entries']) and len(closed['entries'])==len(r['held_resource_refs']),{'held_ref_count':len(r['held_resource_refs']),'new_353_pin_loop':False,'loaded_Windows_module_count':r['actual_loaded_Windows_module_ref_count']})
assert all(x['passed'] for x in checks)
result={'schema':'researchos.public21-source-review-narrow-continuation.v1','review_author':h.REVIEWER,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original1143':original,'original1143_outer_exit':0,'original1143_Python_exit':0,'original1143_children_exits':None,'original_report_ref':h.pin(h.D/'runtime-source-review.json'),'original_guard_ref':h.pin(h.D/'runtime-source-review.guard.closed.json'),'corrected_failed_predicate_only':failed_ids[0],'correction':'78 describes historical Leaf Source package members. Actual input-manifest declares 62 refs; qualification requires every exact declared ref plus mandatory Source/programme/stdlib/SQLite/loaded DLL resources, without a fixed count gate.','actual_leaf_input_count':len(refs),'original12_successes_reused':True,'original353_current_pins_reused':True,'new_checks':checks,'new_checks_failed':[],'Source_Leaf_Caller_or_input_manifest_modified':False,'RootScope_qualification_or_grant_issued':False,'Go_Native_SQL_model_TP_calls':0,'execution_grant':False,'formal_acceptance':False}
g=h.inert(h.G).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
try:
    g.acquire([h.pin(h.D/'source-observations.json'),h.pin(h.D/'runtime-source-review.json'),h.pin(h.D/'runtime-source-review.guard.closed.json'),manifest_ref,original['raw_ref'],original['binding_ref']])
    result_ref=h.write('narrow-continuation.json',result)
finally:
    audit=g.close();guard_ref=h.write('narrow-continuation.guard.closed.json',audit);assert audit['closed'] is True and audit['retained_handles_count']==0 and not audit['errors']
print(json.dumps({'continuation_ref':result_ref,'guard_ref':guard_ref,'new_checks_passed':len(checks),'actual_leaf_input_count':len(refs),'original1143':original,'original12_successes_reused':True,'353pins_not_repeated':True,'all_guards_closed':True,'retained_handles_count':0,'actual_product_calls':0},ensure_ascii=False),flush=True)
