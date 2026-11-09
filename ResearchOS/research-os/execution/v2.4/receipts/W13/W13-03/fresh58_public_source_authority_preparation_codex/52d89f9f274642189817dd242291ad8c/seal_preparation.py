"""Seal only this author's preparation evidence, never publish Root metadata."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
P = ROOT/'execution/v2.4/receipts'


def ref(p):
    raw = p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def put(name, value):
    with (HERE/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


extras = [
    P/'W13/W13-03/desktop58_forward_registration_evidence_independent_review_codex/b3d1bdad7b514ee592faa041db1576f3/review.json',
    P/'W13/W13-03/desktop58_forward_registration_evidence_independent_review_codex/b3d1bdad7b514ee592faa041db1576f3/manifest.json',
    P/'W05/W05-99/cli43_fresh_compiler_preparation_codex/7bf10c8e8cc54412ba7bb89b53f5a622/read_public_inputs.py']
extra_refs = [ref(p) for p in extras]
assert extra_refs[0]['sha256']=='f14dcdf6cfa2676db6022e7a852abd38e2095bc45a0529566b10997001a03624'
assert extra_refs[1]['sha256']=='17ec566a09de448495f31a5bee52b0470c60f63dafec8636c7c71352f66728f7'
put('additional-inputs.json',{'files':extra_refs,'purpose':'Independent closed r333 review plus unchanged historical catalog producer algorithm; no execution'})
audit = json.loads((HERE/'static-audit.json').read_bytes())
assert audit['failed']==0 and ref(HERE/'publish.proposed.py')==audit['source_publisher_ref']
frozen = json.loads((HERE/'inputs.after.static.json').read_bytes())['files']
for item in frozen:
    assert ref(Path(item['path']))==item
for p in HERE.glob('*.py'):
    ast.parse(p.read_bytes())
put('seal-static.json',{'input_refs_rechecked':len(frozen),'input_drift':0,
    'additional_refs':extra_refs,'Python_AST_files':3,'candidate_or_gate_imported':False,
    'candidate_executed':False,'native_exit_separately_sampled':None,'new_failure_origins':[],
    'actual_authority_publications':0,'new_Root_grants':0,'source_acceptance':False})
put('handoff.json',{'schema':'researchos.fresh58-source-catalog-producer-preparation-handoff.v1',
    'author':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED',
    'producer_ref':ref(HERE/'publish.proposed.py'),'contract_ref':ref(HERE/'contract.json'),
    'fixed_inputs_ref':ref(HERE/'fixed-inputs.json'),'selection_ref':ref(HERE/'selection.static.json'),
    'static_audit_ref':ref(HERE/'static-audit.json'),'additional_input_refs':extra_refs,
    'provenance_inverse_ref':ref(HERE/'provenance-and-inverse.json'),
    'controls_ref':ref(HERE/'future-controls.NOT_RUN.json'),'tool_observations_ref':ref(HERE/'tool-observations.json'),
    'source_commit':'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7',
    'source_parent':'a510dbef4a7e08fb5c428df44c39b133f3ffa856',
    'old_public_source_names':597,'new_source_files':639,'Go_files':559,'added_paths':42,
    'changed_old_paths':0,'combined_source_paths':58,'checks':657,'static_failures':0,
    'candidate_imports':0,'candidate_executions':0,'gate_imports':0,
    'Git_Go_Node_SQL_SDK_Dll_Job_HTTP_models':0,'actual_source_publication':False,
    'source_acceptance':False,'formal_increment':0,'execution_grant':None,'new_failure_origins':[],
    'Root_required_next':['Independent preparation review with contract fields',
       'New literal Root request, UUID, UTC and ordered canonical copies matching reviewed r333',
       'Root-only pure-IO publisher invocation with original argv/stdout/stderr/exit receipts',
       'Separate new actual compiler/runtime graph, fresh validation scope and grant'],
    'limits':['No old catalog digest reuse; fresh byte/Git blob proofs for all selected rows',
      'Current43 wire name retained but only exact current58 source set applies',
      'Full dependency/module/runtime/GUI/compile/test qualification remains OPEN',
      'Missing or mismatching Main bytes stop; no loose/packed object fallback or restoration',
      'No publisher or gate source predicate executed during this preparation']})
members = [ref(p) for p in sorted(HERE.iterdir()) if p.is_file()]
put('manifest.json',{'schema':'researchos.immutable-public-preparation-manifest.v1','count':len(members),
    'entries':members,'excluded_only':'manifest.json','self_excluded':True})
print(json.dumps({'handoff':ref(HERE/'handoff.json'),'manifest':ref(HERE/'manifest.json'),
                  'producer':ref(HERE/'publish.proposed.py'),'files':len(members)},ensure_ascii=False))
