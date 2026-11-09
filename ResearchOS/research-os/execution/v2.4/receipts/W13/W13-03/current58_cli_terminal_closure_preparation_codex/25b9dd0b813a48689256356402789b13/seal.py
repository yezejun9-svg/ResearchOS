"""Seal only preparation source and metadata; never execute candidate."""
import ast
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
def save(name, doc):
    with (OUT/name).open('xb') as f:
        f.write((json.dumps(doc, ensure_ascii=False, indent=2)+'\n').encode())
inputs = json.loads((OUT/'inputs.before.json').read_bytes()) + json.loads((OUT/'additional-inputs.json').read_bytes())
assert all(ref(Path(row['path'])) == row for row in inputs)
asts = []
for path in sorted(OUT.glob('*.py')):
    ast.parse(path.read_bytes())
    asts.append(ref(path))
save('static.final.json', {'input_count': len(inputs), 'input_drift_count': 0, 'inputs': inputs, 'AST_checked': asts, 'candidate_imports': 0, 'candidate_calls': 0, 'Go_Node_SQL_Dll_Job_HTTP_SDK_model_calls': 0, 'actual_current_E_L_export_reads': 0, 'current_run_completion_claimed': False, 'new_failure_origins': [], 'two_step_byte_inverse_to_old_producer': True, 'Root_future_review_required': True})
handoff = {'schema': 'researchos.current58-root-terminal-closure-preparation.v1', 'author': 'codex:/root/command_queue_impl', 'status': 'SOURCE_PREPARATION_REPORTED_STOPPED', 'selected_producer_ref': ref(OUT/'close-root-launch.current58.final.proposed.py'), 'contract_ref': ref(OUT/'contract.final.json'), 'request_template_ref': ref(OUT/'request.proposed.json'), 'static_audit_ref': ref(OUT/'static.final.json'), 'original_tool_results_ref': ref(OUT/'tool-observations.json'), 'inverse_refs': [ref(OUT/'whole-inverse.json'), ref(OUT/'wire-compatibility.inverse.json')], 'old_producer_ref': inputs[0], 'source_commit': 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'run_uuid': '0e298790cd484ec9ba319a379e7e34ed', 'execution_authorized': False, 'actual_terminal_result': None, 'actual_target_calls': 0, 'source_acceptance': False, 'case_qualification': False, 'formal_increment': 0, 'candidate_imported_or_executed': False, 'new_origins': [], 'OPEN': ['Root authentic final tool input/result and explicit native marker or NULL; no current running files read.', 'Root exact request/ref/SHA and ended E/L full manifests, reviewed selected producer.', 'Original terminal action/source/grant/intent/invocation/raw refs and additional sealed source-review/stage refs fixed by Root.', 'Root explicit new closure UUID output and pending count; no canonical mutation.', 'Non-author actual qualification remains separate: exit0 never grants case/current58/formal qualification.'], 'limits': ['Caller OS lifecycle remains false.', 'Original wire members dynamic exact union, not guessed11.', 'Metadata-only sealer fails closed on incomplete MF or contradictory evidence and does not rerun targets.', 'Future producer exception must be captured by Root; no metadata self-success or fake native status.']}
save('handoff.json', handoff)
members = [ref(path) for path in sorted(OUT.iterdir()) if path.is_file() and path.name != 'manifest.json']
save('manifest.json', {'schema': 'researchos.source-preparation-manifest.v1', 'members': members, 'count': len(members), 'excluded_only_self': True, 'source_acceptance': False})
print(json.dumps({'handoff_ref': ref(OUT/'handoff.json'), 'manifest_ref': ref(OUT/'manifest.json'), 'selected_producer_ref': handoff['selected_producer_ref'], 'members': len(members), 'input_drift_count': 0}, ensure_ascii=False))
