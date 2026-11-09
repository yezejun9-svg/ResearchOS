import sys
sys.dont_write_bytecode=True
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('seal_guard',Q/'read_inputs.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)

def main():
    excluded={'HDF.json','MF.json','sealed.pins.json','seal-source-guard.closed.json','postseal.tool-io.json'}
    paths=sorted((path for path in Q.rglob('*') if path.is_file() and path.name not in excluded),key=lambda path:path.relative_to(Q).as_posix())
    assert not any('synthetic-temp' in path.parts or '__pycache__' in path.parts for path in paths)
    guard=lib.Guard();closed=False
    try:
        members=[]
        for path in paths:
            raw,ref=guard.read(path)
            members.append(ref)
        refs={Path(ref['path']).relative_to(Q).as_posix():ref for ref in members}
        delivery=json.loads((Q/'Source-delivery.json').read_text(encoding='utf-8'))
        controls=json.loads((Q/'source-controls-v5.result.json').read_text(encoding='utf-8'))
        assert delivery['authority']=='NONE' and controls['new_control_count']==57 and controls['inherited_v4_count']==46
        assert refs['candidate-root/execution/v2.4/formal_profile_w09.py']['sha256']==delivery['candidate_profile_ref']['sha256']
        assert refs['formal_case_index.before.py']['sha256']==refs['formal_case_index.after.py']['sha256']
        mf={'schema':'researchos.w09-profile-v5-immutable-source-manifest.v1','namespace':str(Q),'Source_author':'codex:/root/backup_regression_resources','authority':'NONE','status':'SEALED_SOURCE_ONLY_PENDING_NON_AUTHOR_REVIEW','members':members,'member_count':len(members),'current_before':delivery['current_before'],'candidate_profile_ref':refs['candidate-root/execution/v2.4/formal_profile_w09.py'],'candidate_CM40_ref':refs['candidate-root/execution/v2.4/commands.json'],'source_delivery_ref':refs['Source-delivery.json'],'calling_contract_ref':refs['ROOT_CALLING_CONTRACT.source.md'],'complete_original_IO_ref':refs['complete-original-tool-IO.json'],'original_failure_refs':[refs['failure-origin.1018.json'],refs['failure-origin.1020.json']],'pure_controls_ref':refs['source-controls-v5.result.json'],'preserved_v4_controls_ref':refs['source-controls-v4.result.json'],'public_Source_pins_ref':refs['public-source-pins.json'],'current_Source_guard_ref':refs['final-source-guard.closed.json'],'exclusions':sorted(excluded),'exclusion_reason':'MF/HDF and closed seal receipt/output are excluded to avoid cyclic hashes; later actual sealing tool IO is separately preserved and never claimed as an MF member','formal_acceptance':False,'parent_acceptance':False,'adoption_authority':False,'current_formal_C19_reuse_authority':False,'Main_writes':0,'Canon_writes':0}
        mfref=lib.savejson('MF.json',mf)
        hdf={'schema':'researchos.w09-profile-v5-source-hdf.v1','namespace':str(Q),'manifest_ref':mfref,'Source_author':'codex:/root/backup_regression_resources','Source_status':'PREPARED_PENDING_NON_AUTHOR_REVIEW','authority':'NONE','source_delivery_ref':refs['Source-delivery.json'],'candidate_profile_ref':refs['candidate-root/execution/v2.4/formal_profile_w09.py'],'candidate_CM40_ref':refs['candidate-root/execution/v2.4/commands.json'],'calling_contract_ref':refs['ROOT_CALLING_CONTRACT.source.md'],'role_policy_proposal_ref':refs['role-policy.source-proposal.json'],'registration_proposal_ref':refs['CM40-registration.source-proposal.json'],'exact_inverse_ref':refs['exact-inverse.json'],'profile_diff_ref':refs['profile.diff'],'commands_diff_ref':refs['commands.diff'],'static_verification_ref':refs['static-verification.json'],'finite_controls_ref':refs['source-controls-v5.result.json'],'preserved_v4_controls_ref':refs['source-controls-v4.result.json'],'public_Source_pins_ref':refs['public-source-pins.json'],'current_Source_guard_ref':refs['final-source-guard.closed.json'],'complete_original_IO_ref':refs['complete-original-tool-IO.json'],'original_failure_refs':[refs['failure-origin.1018.json'],refs['failure-origin.1020.json']],'required_next':'Independent non-author Source review, then actual Root scope/adoption/provenance/routes and peer formal review; no self-acceptance','Go_Native_dispatcher_model_SQLite':'NOTRUN','actual_role_or_formal_captures_created':0,'formal_acceptance':False,'parent_acceptance':False,'actual_adoption':'NOTRUN','member_count':len(members)}
        hdfref=lib.savejson('HDF.json',hdf)
        closed_result=guard.close();closed=True
        closedref=lib.savejson('seal-source-guard.closed.json',closed_result)
        for ref in members+[mfref,hdfref,closedref]:
            path=Path(ref['path']);assert lib.pin(path,path.read_bytes())==ref
            path.chmod(stat.S_IREAD)
        pins=lib.savejson('sealed.pins.json',{'schema':'researchos.w09-profile-v5-sealed-pins.v1','HDF_ref':hdfref,'MF_ref':mfref,'Source_delivery_ref':refs['Source-delivery.json'],'candidate_profile_ref':refs['candidate-root/execution/v2.4/formal_profile_w09.py'],'candidate_CM40_ref':refs['candidate-root/execution/v2.4/commands.json'],'calling_contract_ref':refs['ROOT_CALLING_CONTRACT.source.md'],'controls_ref':refs['source-controls-v5.result.json'],'complete_original_IO_ref':refs['complete-original-tool-IO.json'],'seal_source_guard_ref':closedref,'member_count':len(members),'member_readonly_attributes_set':True,'retained_handles':0,'authority':'NONE','STOP':True})
        Path(pins['path']).chmod(stat.S_IREAD)
        print(json.dumps({'HDF_ref':hdfref,'MF_ref':mfref,'sealed_pins_ref':pins,'Source_delivery_ref':refs['Source-delivery.json'],'candidate_profile_ref':refs['candidate-root/execution/v2.4/formal_profile_w09.py'],'candidate_CM40_ref':refs['candidate-root/execution/v2.4/commands.json'],'calling_contract_ref':refs['ROOT_CALLING_CONTRACT.source.md'],'controls_ref':refs['source-controls-v5.result.json'],'complete_original_IO_ref':refs['complete-original-tool-IO.json'],'members':len(members),'retained_handles':0,'authority':'NONE','STOP':True},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
