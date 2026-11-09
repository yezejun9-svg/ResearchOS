import ast,hashlib,json,sys,traceback,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
BR=B/'w09_formal_root_bridge_source_codex/bridge-20261010-06'
SR=B/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-06-attach'
NR=B/'full_w09_nf6_actual_independent_review_codex/review-actual-nf6-20261010-01'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def ref(path):
    raw=Path(path).read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
    path=Q/name
    with path.open('xb')as out:out.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return ref(path)
def main():
    handoff=json.loads((BR/'HDF.json').read_text(encoding='utf-8'));review=json.loads((SR/'HDF.json').read_text(encoding='utf-8'))
    assert review['decision']=='ACCEPTED_SOURCE_ONLY' and review['reviewed_author']=='/root/full_w09_source_review'
    basis=[ref(BR/'HDF.json'),handoff['manifest_ref'],handoff['source_ref'],handoff['root_calling_contract_ref'],handoff['contract_ref'],handoff['consumer_launcher_ref'],ref(SR/'HDF.json'),review['manifest_ref'],review['decision_ref'],ref(R/'execution/v2.4/formal_profile_w09.py'),ref(R/'execution/v2.4/formal_case_index.py'),ref(R/'ops/ci/w09_evidence_closure.py'),ref(NR/'HDF.json'),ref(NR/'MF.json'),ref(NR/'decision.json'),ref(NR/'six-Mode-publication.result.json')]
    modes=json.loads((NR/'six-Mode-publication.result.json').read_text(encoding='utf-8'))
    basis += [item['mode_ref']for item in modes['mode_decisions']]
    raw=GUARD.read_bytes();assert hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm=types.ModuleType('br6_prepare_guard');gm.__file__=str(GUARD);exec(compile(raw,str(GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);primary=None;refs=[]
    try:
        guard.acquire(basis)
        profile=guard.get_buffer(str(R/'execution/v2.4/formal_profile_w09.py')).decode('utf-8');bridge=guard.get_buffer(handoff['source_ref']['path']).decode('utf-8')
        selections={'profile':{'_independent','_global','_review_execution_cutoff','_root_original','_capture_registry','_independent_roles','verify_owner','_role_registry','_vector','_dispatches'},'bridge':{'assemble','capture','roles','consume','check','derive','source_review','root_request'}}
        excerpts={}
        for label,source in [('profile',profile),('bridge',bridge)]:
            items=[]
            for node in ast.parse(source).body:
                if isinstance(node,ast.FunctionDef)and node.name in selections[label]:items.append({'function':node.name,'line':node.lineno,'end_line':node.end_lineno,'source':ast.get_source_segment(source,node)})
                if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id in('IDS','SCHEMAS','PREFIX','CASE_SCHEMA','STAGES')for t in node.targets):items.append({'constant':ast.get_source_segment(source,node),'line':node.lineno})
            excerpts[label]=items
        refs.append(save('actual-contract-excerpts.json',excerpts))
        contract=json.loads(guard.get_buffer(handoff['root_calling_contract_ref']['path']));refs.append(save('calling-contract-observed.json',contract))
        refs.append(save('basis.json',{'schema':'researchos.w09-br6-formal-review-preparation-basis.v1','source_refs':basis,'bridge_hdf':handoff,'bridge_independent_review_hdf':review,'six_Mode_refs':modes['mode_decisions'],'future_context_ref':None,'future_consumer_refs':None,'formal_acceptance':False,'execution_grant':False,'Root_stages_called':0,'live_Canon_read':False}))
        print(json.dumps({'profile_functions':[(x['function'],x['line'])for x in excerpts['profile']if'function'in x],'bridge_functions':[(x['function'],x['line'])for x in excerpts['bridge']if'function'in x],'root_calling_contract':contract,'output_refs':refs},ensure_ascii=False))
    except BaseException as exc:primary={'type':type(exc).__name__,'message':str(exc)};traceback.print_exc()
    finally:
        close=guard.close();cr=save('preparation-SourceGuard.closed.json',close)
        print(json.dumps({'guard_cleanup_ref':cr,'primary_error':primary,'closed':close['closed'],'retained_handles_count':close['retained_handles_count'],'resources_held':len(close['entries'])},ensure_ascii=False))
    return 0 if primary is None and close['closed']and close['retained_handles_count']==0 and close['errors']==[] else 1
if __name__=='__main__':
    code=main();print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
