"""Seal own PUB-01 source preparation; no target import or live-canonical read."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def ref(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def put(name,value):
    with (HERE/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


inputs=json.loads((HERE/'inputs.before.json').read_bytes())['files']
assert [ref(Path(x['path'])) for x in inputs]==inputs
proof=json.loads((HERE/'inverse.json').read_bytes())
raw=(HERE/'publish.v2.proposed.py').read_bytes()
assert ref(HERE/'publish.v2.proposed.py')==proof['candidate_ref']
reversed_raw=raw
for edit in reversed(proof['edits']):
    new,old=edit['new'].encode(),edit['old'].encode()
    assert reversed_raw.count(new)==edit['occurrences']
    reversed_raw=reversed_raw.replace(new,old)
assert reversed_raw==Path(proof['baseline_ref']['path']).read_bytes()
for p in HERE.glob('*.py'):
    ast.parse(p.read_bytes())
put('handoff.json',{'schema':'researchos.fresh58-public-source-producer-revision-handoff.v1',
    'author':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED',
    'finding':'PUB-01','selected_producer_ref':ref(HERE/'publish.v2.proposed.py'),
    'baseline_ref':proof['baseline_ref'],'old_review_ref':inputs[4],
    'old_review_handoff_ref':inputs[5],'old_review_manifest_ref':inputs[6],
    'fixed_inputs_ref':inputs[1],'contract_revision_ref':ref(HERE/'contract-revision.json'),
    'inverse_ref':ref(HERE/'inverse.json'),'source_diff_ref':ref(HERE/'source.diff'),
    'static_audit_ref':ref(HERE/'static-audit.json'),'tool_observations_ref':ref(HERE/'tool-observations.json'),
    'whole_byte_inverse':True,'inverse_hunks':len(proof['edits']),
    'unchanged_definitions':proof['unchanged_definitions_byte_and_AST'],
    'input_drift':0,'AST_files':3,'candidate_or_gate_imported':False,'candidate_executed':False,
    'live_canonical_read_during_preparation':False,'actual_authority_published':False,
    'product_CAS_Git_Go_Node_SQL_Job_HTTP_model_calls':0,'source_acceptance':False,'formal_increment':0,
    'new_failure_origins':[],'future_controls':'NOT_RUN',
    'open':['Nonauthor revision review','Root actual immutable request and copies','Root pure-IO publication',
            'All runtime/compile/test qualification and execution grants'],
    'summary':'All four current canonical byte buffers are compared to reviewed copies across original publication guards; mutable observations are separated from immutable READS.'})
members=[ref(p) for p in sorted(HERE.iterdir()) if p.is_file()]
put('manifest.json',{'schema':'researchos.immutable-public-preparation-manifest.v1','entries':members,
                    'count':len(members),'self_excluded':True,'excluded_only':'manifest.json'})
print(json.dumps({'handoff':ref(HERE/'handoff.json'),'manifest':ref(HERE/'manifest.json'),
                  'producer':ref(HERE/'publish.v2.proposed.py'),'member_count':len(members)},ensure_ascii=False))
