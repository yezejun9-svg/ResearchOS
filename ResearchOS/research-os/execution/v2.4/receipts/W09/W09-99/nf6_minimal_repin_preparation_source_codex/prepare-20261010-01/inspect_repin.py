"""Read and retain only the published Source contracts; no product entry runs."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, traceback, types

R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
N=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
REG=W/'w09_nf4_root_registration_source_codex/register-20261010-02'
BR=W/'w09_formal_root_bridge_source_codex/bridge-20261010-03'
C=W/'nf5_c19_main_order_candidate_source_codex/candidate-20261010-01'
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp);exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__);s.D=D

base={name:s.pin(path) for name,path in {'NF5_HDF':N/'HDF.json','REG5_HDF':REG/'HDF.json','BR3_HDF':BR/'HDF.json','candidate_HDF':C/'HDF.json'}.items()}
heads={name:json.loads(Path(ref['path']).read_bytes()) for name,ref in base.items()}
nf,reg,br,cand=[heads[name] for name in ('NF5_HDF','REG5_HDF','BR3_HDF','candidate_HDF')]
refs=dict(base)
for name,key in [('NF5_MF','manifest_ref'),('NF5_contract','calling_contract_ref'),('NF5_choice','source_choice_ref'),('NF5_runtime','runtime_ref'),('NF5_overrides','overrides_ref'),('NF5_launcher','launcher_ref'),('NF5_prepare','prepare_caller_ref'),('NF5_run','producer_caller_ref'),('NF5_blueprint','compiler_blueprint_ref')]:refs[name]=nf[key]
for name,key in [('REG5_MF','manifest_ref'),('REG5_caller','caller_ref'),('REG5_core','core_ref'),('REG5_contract','contract_ref'),('REG5_inputs','input_pins_ref')]:refs[name]=reg[key]
for name,key in [('BR3_source','source_ref'),('BR3_launcher','consumer_launcher_ref'),('BR3_contract','contract_ref')]:refs[name]=br[key]
refs['BR3_MF']=s.pin(BR/'MF.json')
refs['candidate_source']=cand['sourcecandidate_ref']
refs['current_Main']=s.pin(R/'ops/ci/retrieval.py')
refs['guard_implementation']=s.GREF
functions={
    'NF5_runtime':['package_refs','choice','build_environment','read_inputs','invoke','compiler_inventory','stage'],
    'NF5_overrides':['choice','validate_authority','read_inputs','validate_packet','validate_scratch_parent'],
    'NF5_launcher':['main'],
    'REG5_caller':['reviewed_sources','own_source','request_context','model','check_or_activate','activated_context','finalize_native_requests'],
    'REG5_core':['validate_lease','merge_pending','make_native_scopes','native_owner_worker','canonical_changes'],
    'BR3_source':['native_inputs','consumer_plan','root_request','consume'],
    'BR3_launcher':['main'],
}
g=s.guard();result={};failure=None
try:
    g.acquire(list(refs.values()))
    documents={name:json.loads(g.get_buffer(ref['path'])) for name,ref in refs.items() if Path(ref['path']).suffix=='.json'}
    sources={name:g.get_buffer(refs[name]['path']) for name in functions}
    evidence={name:s.code_evidence(raw,refs[name]['path'],wanted) for name,wanted in functions.items() for raw in [sources[name]]}
    constants={}
    for name,raw in sources.items():
        values=[];lines=raw.decode('utf-8').splitlines()
        for node in ast.parse(raw,filename=refs[name]['path']).body:
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                text='\n'.join(lines[node.lineno-1:node.end_lineno])
                if any(term in text for term in ('fullw09-20261010-05','GENERATION','SLICE','OWNER_KEY','NKEY','NSLICE','PUBLIC_TEMP','TRUSTED','ROLE_PATH','INDEX_PATH')):values.append({'line':node.lineno,'source':text})
        constants[name]=values
    bp=documents['NF5_blueprint']
    # Shape observations, not a requalification of the 3905 compiler inputs.
    bpsummary={'top_keys':list(bp),'scalars':{k:v for k,v in bp.items() if v is None or type(v) in (str,bool,int)},'list_or_dict_counts':{k:len(v) for k,v in bp.items() if type(v) in (list,dict)},'references_to_old_Main_hash':g.get_buffer(refs['NF5_blueprint']['path']).count(cand['before_main_ref']['sha256'].encode()),'references_to_candidate_hash':g.get_buffer(refs['NF5_blueprint']['path']).count(cand['sourcecandidate_ref']['sha256'].encode())}
    choice=documents['NF5_choice']
    result={'schema':'researchos.w09-nf6-repin-input-extract.v1','observed_utc':datetime.now(timezone.utc).isoformat(),'input_refs':refs,'NF5_HDF':documents['NF5_HDF'],'NF5_contract':documents['NF5_contract'],'NF5_choice':choice,'NF5_blueprint_summary':bpsummary,'REG5_HDF':documents['REG5_HDF'],'REG5_contract':documents['REG5_contract'],'REG5_inputs':documents['REG5_inputs'],'BR3_HDF':documents['BR3_HDF'],'BR3_contract_text':g.get_buffer(refs['BR3_contract']['path']).decode('utf-8'),'candidate_HDF':documents['candidate_HDF'],'source_function_evidence':evidence,'source_constant_evidence':constants,'current_Main_observed_ref':refs['current_Main'],'candidate_is_current_Main_bytes':refs['current_Main']['sha256']==cand['sourcecandidate_ref']['sha256'] and refs['current_Main']['bytes']==cand['sourcecandidate_ref']['bytes'],'future_current_Source21_qualification':False,'compiler_3905_checks_rerun':False,'product_entry_calls':0,'Rootexecute':False}
except BaseException as exc:
    failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    closed=g.close();guard_ref=s.write('repin-input.guard.closed.json',closed)
    result.update(failure=failure,guard_ref=guard_ref,guard_closed=closed['closed'],guard_retained_handles_count=closed['retained_handles_count'])
    result_ref=s.write('repin-input-extract.json',result)
print(json.dumps({'status':'SOURCE_INPUTS_EXTRACTED' if failure is None else 'FAILED','result_ref':result_ref,'guard_ref':guard_ref,'input_count':len(refs),'failure':failure,'guard_closed':closed['closed'],'guard_retained_handles_count':closed['retained_handles_count'],'choice_common_fields':list(result.get('NF5_choice',{}).get('common',{})),'blueprint_summary':result.get('NF5_blueprint_summary'),'current_Main_ref':refs['current_Main'],'candidate_is_current_Main_bytes':result.get('candidate_is_current_Main_bytes'),'Rootexecute':False,'future_current_Source21_qualification':False},ensure_ascii=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:raise SystemExit(1)
