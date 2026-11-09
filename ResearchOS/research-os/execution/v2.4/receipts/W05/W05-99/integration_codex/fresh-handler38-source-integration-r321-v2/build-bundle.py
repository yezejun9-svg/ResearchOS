import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
assert len(sys.argv) == 3
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent

def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    raw = p.read_bytes()
    item = {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item

base = 'execution/v2.4/receipts/'
root14 = base + 'W05/W05-99/session_list_root14_bounded_evidence_independent_review_codex/e555f38adda740979172f876cfdd33f3/'
go3 = base + 'W13/W13-03/desktop_go3_debug_component_evidence_independent_review_codex/35ff2da3523e4619b3f7bd763b2c91f2/'
w09 = '.local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8/' + base + 'W09/W09-99/test_only_causal_exact4_executor_codex/9a15d49131e846159a16b8125ed79c99/'
v2 = base + 'W05/W05-99/main_exact38_integration_preparation_codex/revision-v2-ed1a1dab301a40b293dd6a177980cfaf/'
meta = base + 'W05/W05-99/integration_codex/root-continuation-after320/'
oldreview = base + 'W05/W05-99/exact38_integration_controller_independent_review_codex/22c9358b53a4439d88c8230bab0cf477/'
pins = {}
for key, path, digest in [
    ('previous_handoff', base + 'W05/W05-99/integration_codex/parallel-source-and-go3-r320/handoff-r320-running.json', '4662143410950f0073eabc93aac36a2b16ea77e866ac2c103dda983a203ea3fc'),
    ('previous_manifest', base + 'W05/W05-99/integration_codex/parallel-source-and-go3-r320/manifest.json', '5af93dcc4467da9736f39693e9f3cb48bbe8ac5d26068cf884ded2b5ad2b8e80'),
    ('root14_review', root14 + 'review.json', '043efd8e2397c1c5d219ff83822122e5ee4a11c59058d3508662edb03b13e5a0'),
    ('root14_review_manifest', root14 + 'manifest.json', '6e1d5b105293d223c2f96e2a52745f7aee9aae166be1961f3551b99bff4f4389'),
    ('root14_audit', base + 'W05/W05-99/root14_evidence_sealed_codex/e1b3d1e2a8404f6997dab28af163d25c/audit.json', '5444b4202ce69e82f4b39ad8216ed1ab849bf7a39c83b2cda4232a2c3eb31e58'),
    ('go3_review', go3 + 'review.json', 'a2f5729ba47437a158ca0857a91a732aa0ea099ce873a335f38998ec92a81de7'),
    ('go3_review_manifest', go3 + 'manifest.json', '0a1a21c5b007550153737733abfe71b89c527f5d66d276c6add5af79c17bc30c'),
    ('go3_audit', meta + 'audit.json', '16562b88cade459e8185b09a5827a7cb49634a9690ae6b764876742da377cf0b'),
    ('go3_closed_manifest', meta + 'manifest.json', '175c020bee79da6350c50c3554e759fb75e6f3169fb75b26ef91fdffde0b4c1b'),
    ('w09_handoff', w09 + 'handoff.json', '1340758a56842800acef0c2a3384195d95d741eaa5b88698fd044dae90f07de0'),
    ('w09_author_manifest', w09 + 'manifest.json', '466734e217bab0ffc0dac5c3be90a8c6d04f76f0993349d8a2f0e6baf6afc564'),
    ('w09_review', base + 'W09/W09-99/test_only_causal_exact4_source_independent_review_codex/09742ae11ada43268282343cc78c6e0d/review.json', '227a4a32deace4f6212ead2b36c6c6c5ef896eacbacd9615cdb7ecee2630d344'),
    ('w09_review_manifest', base + 'W09/W09-99/test_only_causal_exact4_source_independent_review_codex/09742ae11ada43268282343cc78c6e0d/manifest.json', '66e28fa05c87454f33ad56006d1838cde315bf3fe93d93ae032728388d5e98fa'),
    ('integration_preparation_handoff', v2 + 'handoff.json', '424f16f455f464ad899bb1d77de740d2fa6085ffe26aa1e41b15363ce6bb715b'),
    ('integration_preparation_manifest', v2 + 'manifest.json', 'd0f188833adec9b098f872c21134352f0ac4b67588b133472fe7d6abffecde7f'),
    ('integration_controller', v2 + 'integrate_exact38.v2.py', 'e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff'),
    ('scope', OUT / 'scope_registration.json', '254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90'),
    ('scope_derivation_audit', OUT / 'derivation-audit.json', '9751c876133bf07f823b55914948960e9fe2a949cf5f263ef24bb2745d7e2254'),
    ('grant_producer', OUT / 'grant-producer.py', 'dfbed4a9feb172a46aafa426775605428a1dc1f47d69b3d1c6cf91c50b0d6577'),
    ('integration_launcher', OUT / 'launcher.v2.py', 'be5fdfae7c321376dc60f964167a92f06725bfe83e97a826e50a6eae8f2a2bc2'),
    ('original_controller_REQUEST_CHANGES', oldreview + 'review.json', '6857f4bbe96363996708b707943e89e3855a69e6cadcc58ad5fc2e92c6efc852'),
    ('task_packet_handoff', base + 'W05/W05-99/integration_codex/package-packet-and-zeroexit-lookups-r320/handoff.json', '1572419110be7501759a57a79c2496104d8d21b3c7293459b0368871d852e6ee'),
]:
    pins[key] = ref(path, digest)
pins['integration_controller_review'] = ref(sys.argv[1], sys.argv[2])
pins['integration_controller_review_manifest'] = ref(Path(sys.argv[1]).parent / 'manifest.json',
    'a43d3d36012a25abe36a0837171788dbb000d873dd83568a3a48ab475b83678b')
pins['integration_controller_review_handoff'] = ref(Path(sys.argv[1]).parent / 'handoff.json',
    '5ba0096d16c1b688ec8f4dbe3186c02f9294fd57c5130fe1b7c3304646a38432')
review = json.loads((ROOT / pins['integration_controller_review']['path']).read_bytes())
assert review['schema'] == 'researchos.exact38-integration-controller-review.v1'
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['decision'] == 'READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE' and review['requested_changes'] == []
assert review['actual_integration_executed'] is False
assert review['controller_sha256'] == pins['integration_controller']['sha256']
assert review['scope_sha256'] == pins['scope']['sha256']
assert review['launcher_sha256'] == pins['integration_launcher']['sha256']
origin_refs = [ref(path, digest) for path, digest in [
    (root14 + 'failure-origin.61f965.json', '1040fb9c39bdd843452cb8d19a4ae219907bf7085e3a0cf91dd56e3a4e8e6986'),
    (root14 + 'failure-origin.69b4cc.json', 'caebfd991b2a88f4d5ce6c944d5f4276f08ab11f2250dd34213d0b20a25634e3'),
    (meta + 'failure-origin.d2cc6b.json', 'cddee98164c9720ceaa45bf3ffbc49d9ebe36f76e7e037f58a41ec504ea65ee4'),
    (meta + 'failure-origin.efbf62.json', '854e41fb74d5c1b4c4ecbf5940ea17d902750571f9521b4ba7aaebb102feff5b'),
    (oldreview + 'failure-origin.828f8b.json', '74d3421c2ea6c8e2fb79d94bc5faf8f0aaa27fb10d948944608804de58d678df'),
]]
pending = [ref(path, digest) for path, digest in [
    (base + 'W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0/diagnostics/eeed61/origin.json', '60ec973a6e27c14c218bb78e9ab087f2e1018c420abbc1059a2e5908fa995252'),
    (v2 + 'failure-origin.df6aba.json', 'ebea7746632fe761ff2bd79725e7ac9a89b49a62a3fbf4b437daf9730acd2949'),
]]
pins['pending_source_AST_origin'], pins['pending_controller_derivation_origin'] = pending
bundle = {'schema': 'researchos.root321-registration-pin-bundle.v2',
    'expected_before': [320, 148, 417], 'expected_after': [321, 149, 422],
    'pins': pins, 'origin_refs': origin_refs, 'pending_origin_refs': pending,
    'root_scope': json.loads((ROOT / pins['scope']['path']).read_bytes()),
    'go3_review_decision': 'READY_FOR_ROOT_REGISTERING_BOUNDED_GO3_DEBUG_COMPONENT_EVIDENCE_WITH_DECLARED_OPEN_GATES',
    'integration_controller_review_decision': 'READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE'}
raw = (json.dumps(bundle, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
with (OUT / 'pin-bundle.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'pin_bundle_ref': ref(OUT / 'pin-bundle.json')}, ensure_ascii=True))
