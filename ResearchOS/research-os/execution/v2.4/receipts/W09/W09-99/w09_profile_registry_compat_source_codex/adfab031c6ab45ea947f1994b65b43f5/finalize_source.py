import sys
sys.dont_write_bytecode=True
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('finite_source_guards',Q/'read_inputs.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)

def main():
    guard=lib.Guard();closed=False
    try:
        discovery=json.loads((Q/'input-discovery.json').read_text(encoding='utf-8'))
        exact=json.loads((Q/'C19-exact-receipts.json').read_text(encoding='utf-8'))
        binding=json.loads((Q/'C19-binding-inputs.json').read_text(encoding='utf-8'))
        refs={}
        def take(ref):
            path=Path(ref['path'])
            if not path.is_absolute():path=lib.R/path
            raw,actual=guard.read(path,ref)
            refs[actual['path']]=actual
            return raw,actual
        for row in discovery['current_before'].values():take(row['original_ref'])
        for ref in (discovery['gap_HDF_ref'],discovery['gap_MF_ref'],discovery['gap_report_ref'],discovery['v4_HDF_ref'],discovery['v4_MF_ref'],binding['closure_original_ref'],binding['caller_closed_ref'],binding['summary']['original_ref'],binding['historical_attribution']['original_ref'],exact['actual_CM39_archive_original_ref'],exact['actual_dispatcher_owner_original_ref']):take(ref)
        for row in exact['rows']:
            for label in ('dispatcher_receipt_ref','mode_decision_ref','dispatcher_child_stdout_ref'):take(row[label]['original_ref'])
        scope=exact['actual_dispatcher_owner_value']['scope_ref']
        scope_raw,scope_ref=take(scope)
        lib.save('inputs/C19-real-root-scope.json',scope_raw)
        first=exact['rows'][0]['dispatcher_receipt_ref']['value']
        for logical,key in [('execution/command_dispatcher/dispatch.py','dispatcher_sha256'),('execution/toolchains/locked.json','toolchain_revision')]:
            raw,actual=guard.read(lib.R/logical)
            assert actual['sha256']==first[key]
            assert all(row['dispatcher_receipt_ref']['value'][key]==actual['sha256'] for row in exact['rows'])
            refs[actual['path']]=actual
        main_profile=discovery['current_before']['Main_formal_profile']['original_ref']
        main_index=discovery['current_before']['Main_formal_case_index']['original_ref']
        cm39=discovery['current_before']['CM39']['original_ref']
        roles={'schema':'researchos.w09.role-policy-source-proposal.v1','authority':'NONE','status':'PENDING_ROOT_ACTUAL_ISSUANCE_AND_SCOPE_REGISTRATION','context_outer_schema':'researchos.w09.current-context.v1','role_policy_schema':'researchos.w09.execution-role-policy.v1','registry_schema':'researchos.w09.execution-role-registry.v1','actual_registry_path':'execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json','current_Canon_role_slot':'work_in_progress.w09_execution_role_registry_ref','issuer_role':'VERIFIER','observer_role':'ROOT_OBSERVER','Root_executor_may_equal_observer':True,'Verifier_must_differ_from':['SOURCE_AUTHORS','EXECUTOR','EVIDENCE_ASSEMBLER','ROOT_OBSERVER'],'actual_roles_not_created_here':True,'new_actual_formal_capture_count':0,'current_original_delivery_gate_unchanged':True,'Source_author_role':'codex:/root/backup_regression_resources','required_original_provenance_refs_per_role':['raw_ref','actual_audit_ref'],'required_new_assembly_scope':'W09_FULL_FORMAL_ASSEMBLY','historical_C19_owner_scope_ref':scope_ref,'existing_C19_owner_is_not_full_assembly_grant':True}
        lib.savejson('role-policy.source-proposal.json',roles)
        commands=json.loads((Q/'commands.after.json').read_text(encoding='utf-8'))
        archive=json.loads((Q/'inputs/commands.CM39.actual-archive.json').read_text(encoding='utf-8'))
        namespace={'__name__':'pure_finalize_profile'}
        candidate=(Q/'candidate-root/execution/v2.4/formal_profile_w09.py').read_bytes()
        tree=ast.parse(candidate);exec(compile(tree,'SOURCE_profile','exec'),namespace)
        assert commands['commands']==namespace['_cm40_commands'](archive)
        route_proposal={'schema':'researchos.w09.cm40-four-route-source-proposal.v1','authority':'NONE','status':'NOT_ADOPTED','before_CM39_ref':cm39,'proposal_ref':lib.pin(Q/'candidate-root/execution/v2.4/commands.json',(Q/'commands.after.json').read_bytes()),'required_Root_actual_metadata':True,'missing_routes':[{'command_key':'test.retrieval','check_id':'W09-G01','case_id':''},{'command_key':'test.retrieval','check_id':'W09-G02','case_id':''},{'command_key':'test.retrieval','check_id':'','case_id':'A06'},{'command_key':'test.security','check_id':'','case_id':'A06'}],'old_security_fallback':'Existing Main router PRESERVED W17 -> locked Go run ./tests/security/check','current_unrelated_commands_unchanged':True,'old_registry_files_unchanged':True,'exact_CM39_archive':namespace['CM39_ARCHIVE'],'exact_two_historical_receipts':namespace['LEGACY_C19_RECEIPTS'],'later_CM_revision_requires_new_review':True,'actual_invocations':'NOTRUN','formal_acceptance':False}
        lib.savejson('CM40-registration.source-proposal.json',route_proposal)
        excerpt=[]
        texts={'FrozenGoal08':(Q/'inputs/frozen-08_AGENT_EXECUTION_GOAL.md').read_text(encoding='utf-8'),'MainProfileBefore':(Q/'inputs/formal_profile_w09.before.py').read_text(encoding='utf-8'),'MainIndexUnchanged':(Q/'formal_case_index.after.py').read_text(encoding='utf-8'),'CandidateProfileV5':candidate.decode('utf-8'),'MainRouter':(Q/'inputs/Main_router.py').read_text(encoding='utf-8')}
        selectors={'FrozenGoal08':['AcceptanceReceipt','不能自己签发','不同','执行者','复核'],'MainProfileBefore':['tool = _doc(api, reader, tool_ref, SOURCE_PREFIX)','registered_command_revision','DISPATCH_INPUT_UNPINNED','len({executor.casefold()','def _root_original','def _capture_registry'],'MainIndexUnchanged':['def _registered_roots','def _w09_profile','if task_id == "W09"'],'CandidateProfileV5':['def _native_tool_doc','def _historical_registry','def _dispatcher_input','def _role_audit','def _role_registry','def _route_execution_actor','def _independent_roles','def verify_owner'],'MainRouter':['PRESERVED =','test.security','./tests/security/check']}
        for label,text in texts.items():
            for number,line in enumerate(text.splitlines(),1):
                if any(term in line for term in selectors[label]):excerpt.append({'source':label,'line':number,'text':line})
        lib.savejson('policy-and-code-excerpts.json',{'schema':'researchos.w09-source-excerpts.v1','authoritative_frozen_Goal_ref':discovery['current_before']['frozen_goal']['original_ref'],'before_refs':{'profile':main_profile,'index':main_index,'CM39':cm39},'excerpt_lines':excerpt,'policy_inference':'Frozen Goal requires executor != independent Verifier and no executor self-issuance; it does not require Root observer != executor. Existing W04/W07 stronger rules remain byte-identical. Root actual role and formal issuance prerequisites remain mandatory.'})
        final_pins=lib.savejson('public-source-pins.json',{'schema':'researchos.w09-current-public-source-pins.v1','authority':'NONE','refs':list(refs.values()),'current_Source_toolchain_dispatcher_match_two_original_C19':True,'private_resource_reads':0})
        closed_value=guard.close();closed=True
        closed_ref=lib.savejson('final-source-guard.closed.json',closed_value)
        controls=json.loads((Q/'source-controls-v5.result.json').read_text(encoding='utf-8'))
        decision={'schema':'researchos.w09-profile-v5-source-delivery.v1','Source_status':'PREPARED_FOR_NON_AUTHOR_REVIEW','authority':'NONE','Source_author':'codex:/root/backup_regression_resources','Scope':'W09_PROFILE_AND_CM40_PROPOSAL_ONLY','original_gap_report_ref':discovery['gap_report_ref'],'current_before':{'profile':main_profile,'index':main_index,'commands':cm39},'candidate_profile_ref':lib.pin(Q/'candidate-root/execution/v2.4/formal_profile_w09.py',candidate),'candidate_CM40_ref':route_proposal['proposal_ref'],'calling_contract_ref':lib.pin(Q/'ROOT_CALLING_CONTRACT.source.md',(Q/'ROOT_CALLING_CONTRACT.source.md').read_bytes()),'public_Source_pins_ref':final_pins,'source_guard_ref':closed_ref,'pure_controls':{'preserved_v4':controls['inherited_v4_count'],'new_v5':controls['new_control_count'],'status':controls['status'],'formal_acceptance':False},'original_failures_retained':[1018,1020],'actual_Native_dispatcher_model_SQLite':'NOTRUN','actual_role_registry':'PENDING_ROOT_ISSUANCE','actual_Canon_adoption':'NOTRUN','actual_new_four_routes':'NOTRUN','current_formal_C19_reuse_authority':False,'self_acceptance':False,'Main_writes':0,'Canon_writes':0,'root_actual_formal_capture_writes':0,'required_next':'Non-author Source review; Root actual Scope/adoption/roles/route invocations; independent formal delivery with unchanged full gates'}
        delivery=lib.savejson('Source-delivery.json',decision)
        print(json.dumps({'Source_delivery_ref':delivery,'public_pins_ref':final_pins,'guard_ref':closed_ref,'pins':len(refs),'retained_handles':0,'authority':'NONE'},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
