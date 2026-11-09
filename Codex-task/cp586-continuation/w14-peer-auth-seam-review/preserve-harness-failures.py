from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
out=ROOT/'harness-attempt-01'
out.mkdir(exist_ok=False)
current=(ROOT/'run-independent-qa.py').read_bytes()
old=current.replace(b'def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()',b'def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()',1)
old=old.replace(b"'harness_origin':'independent-w14-qa-harness-20261104','harness_attempt_index':2,'prior_failure_retained':'../harness-attempt-01/failure.json',",b'',1)
assert old!=current
(out/'controller-attempt-01.reconstructed-from-patch.txt').write_bytes(old)
(out/'controller-corrected-before-QA.txt').write_bytes(current)
diagnostics=[
 {'raw_chunk_id':'93963a','exit_code':1,'origin':'independent-w14-qa-harness-20261104','attempt_index':1,'classification':'REVIEW_HARNESS_PATH_COERCION_ERROR_BEFORE_GO','message':"AttributeError: 'str' object has no attribute 'read_bytes' at sha(tools[name]['path'])",'Go_commands_started':0,'fresh_databases_opened':0,'original_controller_evidence':'Exact prior text reconstructed by reversing the two recorded apply_patch changes, explicitly not a contemporaneous file copy.','reconstructed_controller_sha256':hashlib.sha256(old).hexdigest()},
 {'raw_chunk_id':'74b034','exit_code':1,'origin':'independent-w14-review-evidence-preservation-20261104','attempt_index':1,'classification':'REVIEW_EVIDENCE_SHELL_QUOTING_ERROR_BEFORE_PYTHON_LAUNCH','message':"tools[name][path]: The term 'tools[name][path]' is not recognized as a name of a cmdlet, function, script file, or executable program.",'outcome_checked':'Subsequent filesystem inspection found no failure directory and no run directory; the corrected controller patch had applied.','Go_commands_started':0,'fresh_databases_opened':0}
]
record={'status':'HARNESS_FAILURES_PRESERVED_NOT_PRODUCT_FAILURE','run_root_existed':(ROOT/'run-01').exists(),'diagnostics':diagnostics,'source_changes':0,'counter_reset':False}
with (out/'failure.json').open('x',encoding='utf-8') as stream:json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps({'evidence':str(out/'failure.json'),'sha256':hashlib.sha256((out/'failure.json').read_bytes()).hexdigest(),'run_root_existed':record['run_root_existed']}))
