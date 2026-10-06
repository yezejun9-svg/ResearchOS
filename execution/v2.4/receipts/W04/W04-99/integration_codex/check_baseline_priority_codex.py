"""Replay only the failed stale U09 unit expectation on the unchanged baseline."""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys, unittest
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]
raw=subprocess.check_output(['git','show','f5bc7f3e:bootstrap/v24_checkpoint.py'],cwd=ROOT)
assert hashlib.sha256(raw).hexdigest()=='319b4ad73e69577f70bd1775e4d2aed9f1d1af69c801fa4bcdf0e07508dc1d39'
baseline=HERE/'baseline_v24_checkpoint_before_accounting.py'; baseline.write_bytes(raw)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
test=module('original_u09_tests',ROOT/'tests/resources/value_checkpoint_test.py')
test.checkpoint=module('baseline_checkpoint',baseline)
suite=unittest.TestSuite([test.ValueCheckpointTest('test_next_selection_consumes_priority_and_never_retries_failed_cards')])
with (HERE/'baseline_priority_test.stderr.txt').open('x',encoding='utf8') as output:
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
assert result.testsRun==1 and len(result.failures)==1 and len(result.errors)==0
record={'schema':'researchos.baseline-regression-attribution.v1','status':'CONFIRMED_PREEXISTING_STALE_UNIT_EXPECTATION',
    'test_name':'test_next_selection_consumes_priority_and_never_retries_failed_cards','baseline_source_sha256':hashlib.sha256(raw).hexdigest(),
    'baseline_failures':len(result.failures),'baseline_errors':len(result.errors),'current_observed_failures':1,
    'detail':'Unchanged U09 parent-frontier selection returns W17-99; the historical unit expectation still requires None. Accounting does not change prioritized_step/flow_priority, no blocked card was retried.',
    'formal_case_count_delta':0}
with (HERE/'baseline_priority_attribution_codex.json').open('x',encoding='utf8') as f: json.dump(record,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps(record,ensure_ascii=False))
