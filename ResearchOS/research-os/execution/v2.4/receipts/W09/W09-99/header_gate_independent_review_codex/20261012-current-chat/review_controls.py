"""Independent source checks; no native execution, Canon edits or review fabrication."""
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

OUT = Path(__file__).resolve().parent
REPO = next(p for p in OUT.parents if (p / 'execution/project_identity.json').is_file())
CAND = REPO / '.local/candidates/w09-header-recovery-20261012'
test_path = CAND / 'tests/test_header_correction.py'
# Keep the exact 22 author test methods, relocate only its temporary drift leaf
# into the reviewer write scope. The source itself is never modified.
source = test_path.read_text(encoding='utf-8')
source = source.replace('scratch = CANDIDATE / "tests" /', 'scratch = REVIEW_OUT /')
ns = {'__file__': str(test_path), '__name__': 'independent_author_suite', 'REVIEW_OUT': OUT}
exec(compile(source, str(test_path), 'exec'), ns)
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['CorrectionControls']))
(OUT / 'candidate22-tests.txt').write_text(log.getvalue(), encoding='utf-8')
assert result.wasSuccessful() and result.testsRun == 22
base = ns['CorrectionControls']; base.setUpClass()
api, profile, helper = base.api, base.profile, base.m
outcomes = []
def reject(name, fn):
    try:
        fn()
    except api.InvalidEvidence as exc:
        outcomes.append({'name': name, 'status': 'PASS', 'rejection': exc.code})
    else:
        raise AssertionError(name + ' was accepted')

# Empty fake capture descriptors cannot stand in for current original delivery.
class DeliveryReader:
    def ref(self, ref, prefix=None): return self
    def stat(self): return type('Stat', (), {'st_size': 1})()
    def read(self, path): return self.capture
delivery_reader = DeliveryReader()
delivery_ref = {'path': helper['PREFIX']+'test-not-written', 'sha256': '0'*64, 'bytes': 1}
delivery_reader.capture = {'schema': 'researchos.w09.correction-review-delivery.v1',
    'source_audit_path': helper['OLD_LOG'], 'thread_id': helper['OLD_THREAD'],
    'original_capture_ref': {}, 'source_line_offsets': [], 'original_line_sha256': []}
reject('old_chat_capture_refused', lambda: helper['_review_delivery'](api, delivery_reader, base.cert_ref, {}, {}, delivery_ref))
delivery_reader.capture.update(source_audit_path=helper['CURRENT_LOG'], thread_id=helper['CURRENT_THREAD'])
reject('current_claim_without_real_capture_refused', lambda: helper['_review_delivery'](api, delivery_reader, base.cert_ref, {}, {}, delivery_ref))

# Real source vector: changing an old business-source pin still fails even when
# the exact profile transition is present; no test weakens the production API.
context = json.loads(base.roots['context'].read_text(encoding='utf-8'))
business = next(r for r in context['version_vector']['source_files'] if r['path'].startswith('internal/domain/'))
changed = copy.deepcopy(context)
next(r for r in changed['version_vector']['source_files'] if r['path']==business['path'])['sha256']='0'*64
reader = api.Reader(REPO); reader.w09_header_correction = {'certificate': base.cert}
reject('business_source_hash_still_verified', lambda: profile['_vector'](api, reader, changed))

# Isolated modeled Canon authority in this review scope. No file in Main changes.
# Deliberately minimal malicious helper tests whether the profile authenticates
# the independent review before granting execution to authority-selected code.
fixture = OUT / 'isolated-loader-fixture'
module_path = fixture / helper['MODULE_PATH']
module_path.parent.mkdir(parents=True, exist_ok=True)
raw = b'def authorize(*args):\n    return {"unreviewed_helper_ran": True}\ndef audit_line(*args):\n    return {}\n'
module_path.write_bytes(raw)
module_ref = {'path': helper['MODULE_PATH'], 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
authority = {'schema': 'researchos.w09.header-correction-authority.v1', 'certificate_ref': {},
             'verifier_module_ref': module_ref, 'review_ref': {}, 'delivery_ref': {}}
checkpoint = fixture / 'execution/v2.4/checkpoint.json'
checkpoint.write_text(json.dumps({'work_in_progress': {'w09_header_metadata_correction': authority}}), encoding='utf-8')
reader = api.Reader(fixture)
actual = profile['_header_correction'](api, reader, {})
outcomes.append({'name': 'repinned_unreviewed_helper_with_no_review', 'status': 'BYPASS_REPRODUCED',
    'result': actual['certificate'], 'review_ref': {}, 'delivery_ref': {},
    'executed_source_sha256': module_ref['sha256']})
module_path.write_bytes(raw+b'\n')
reject('helper_drift_without_repin_refused', lambda: profile['_header_correction'](api, api.Reader(fixture), {}))
# Remove only the precise disposable fixture files, then empty directories.
module_path.unlink(); checkpoint.unlink()
module_path.parent.rmdir(); module_path.parent.parent.rmdir(); fixture.rmdir()
summary = {'schema': 'researchos.independent-source-controls.v1', 'reviewer_id': '/root/w09_header_gate_review',
    'candidate22_passed': True, 'additional_controls': outcomes,
    'native_or_consumer_calls': False, 'main_or_canon_writes': False,
    'generated_real_delivery_or_acceptance': False}
(OUT / 'controls-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
