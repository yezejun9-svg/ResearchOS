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

def follow(path, expected):
    item = ref(path, expected)
    return json.loads((ROOT / item['path']).read_bytes()), item

base = 'execution/v2.4/receipts/'
root14_dir = base + 'W05/W05-99/session_list_root14_bounded_evidence_independent_review_codex/e555f38adda740979172f876cfdd33f3/'
go3_dir = base + 'W13/W13-03/desktop_go3_debug_component_evidence_independent_review_codex/35ff2da3523e4619b3f7bd763b2c91f2/'
w09_dir = '.local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8/' + base + 'W09/W09-99/test_only_causal_exact4_executor_codex/9a15d49131e846159a16b8125ed79c99/'
main38_dir = base + 'W05/W05-99/main_exact38_integration_preparation_codex/7b236231f51d42319f8c21c0db715b01/'
rootmeta = base + 'W05/W05-99/integration_codex/root-continuation-after320/'
pins = {}
for key, path, digest in [
    ('previous_handoff', base + 'W05/W05-99/integration_codex/parallel-source-and-go3-r320/handoff-r320-running.json', '4662143410950f0073eabc93aac36a2b16ea77e866ac2c103dda983a203ea3fc'),
    ('previous_manifest', base + 'W05/W05-99/integration_codex/parallel-source-and-go3-r320/manifest.json', '5af93dcc4467da9736f39693e9f3cb48bbe8ac5d26068cf884ded2b5ad2b8e80'),
    ('root14_review', root14_dir + 'review.json', '043efd8e2397c1c5d219ff83822122e5ee4a11c59058d3508662edb03b13e5a0'),
    ('root14_review_manifest', root14_dir + 'manifest.json', '6e1d5b105293d223c2f96e2a52745f7aee9aae166be1961f3551b99bff4f4389'),
    ('root14_review_handoff', root14_dir + 'handoff.json', '03260dca361d03a8b711cb21b77909f629366ff13735ed60848e19cc5e2efbf2'),
    ('root14_audit', base + 'W05/W05-99/root14_evidence_sealed_codex/e1b3d1e2a8404f6997dab28af163d25c/audit.json', '5444b4202ce69e82f4b39ad8216ed1ab849bf7a39c83b2cda4232a2c3eb31e58'),
    ('go3_review', go3_dir + 'review.json', 'a2f5729ba47437a158ca0857a91a732aa0ea099ce873a335f38998ec92a81de7'),
    ('go3_review_manifest', go3_dir + 'manifest.json', '0a1a21c5b007550153737733abfe71b89c527f5d66d276c6add5af79c17bc30c'),
    ('go3_review_handoff', go3_dir + 'handoff.json', '5e172221796b79870b6cd29944e61520ec1f428dc5c1fc5f98a77e7b9b021c63'),
    ('go3_audit', rootmeta + 'audit.json', '16562b88cade459e8185b09a5827a7cb49634a9690ae6b764876742da377cf0b'),
    ('go3_closed_manifest', rootmeta + 'manifest.json', '175c020bee79da6350c50c3554e759fb75e6f3169fb75b26ef91fdffde0b4c1b'),
    ('w09_handoff', w09_dir + 'handoff.json', '1340758a56842800acef0c2a3384195d95d741eaa5b88698fd044dae90f07de0'),
    ('w09_author_manifest', w09_dir + 'manifest.json', '466734e217bab0ffc0dac5c3be90a8c6d04f76f0993349d8a2f0e6baf6afc564'),
    ('w09_review', base + 'W09/W09-99/test_only_causal_exact4_source_independent_review_codex/09742ae11ada43268282343cc78c6e0d/review.json', '227a4a32deace4f6212ead2b36c6c6c5ef896eacbacd9615cdb7ecee2630d344'),
    ('w09_review_manifest', base + 'W09/W09-99/test_only_causal_exact4_source_independent_review_codex/09742ae11ada43268282343cc78c6e0d/manifest.json', '66e28fa05c87454f33ad56006d1838cde315bf3fe93d93ae032728388d5e98fa'),
    ('w09_review_handoff', base + 'W09/W09-99/test_only_causal_exact4_source_independent_review_codex/09742ae11ada43268282343cc78c6e0d/handoff.json', '85439079a5bd9307ef350e757f84a37ee386f3a3d9da6dfbfc278ec7f6aad57a'),
    ('integration_preparation_handoff', main38_dir + 'handoff.json', '6599312aca492d4830d8fb8013f3b0f4d7e8482b66f13bbea46e983a08ac87b7'),
    ('integration_preparation_manifest', main38_dir + 'manifest.json', 'c4f68af65250d5f3a0500b8568ee4a4b9a0a972ed17212b0c95d361db93cb5c1'),
    ('integration_controller', main38_dir + 'integrate_exact38.py', '7ca8b3dcdfdfc4135da349bacefba7eb41ba18c425db43abb3e51df0fc2e155c'),
    ('scope', OUT / 'scope_registration.json', 'b3412116292c8e30d7e29f546ac399ee9f25c4bf5f6f39c0bb62ed16142fa30b'),
    ('scope_freeze_audit', OUT / 'scope-freeze-audit.json', '7ae456fd62c75b008ab2263da5a14998be1e6977fe718c208f8296a54bbeaa4f'),
    ('task_packet_handoff', base + 'W05/W05-99/integration_codex/package-packet-and-zeroexit-lookups-r320/handoff.json', '1572419110be7501759a57a79c2496104d8d21b3c7293459b0368871d852e6ee'),
]:
    pins[key] = ref(path, digest)
review, pins['integration_controller_review'] = follow(sys.argv[1], sys.argv[2])
assert review['schema'] == 'researchos.exact38-integration-controller-review.v1'
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['decision'] == 'READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE'
assert review['requested_changes'] == [] and review['actual_integration_executed'] is False
assert review['controller_sha256'] == pins['integration_controller']['sha256']
assert review['scope_sha256'] == pins['scope']['sha256']
root_scope = json.loads((ROOT / pins['scope']['path']).read_bytes())
origin_refs = [ref(path, digest) for path, digest in [
    (root14_dir + 'failure-origin.61f965.json', '1040fb9c39bdd843452cb8d19a4ae219907bf7085e3a0cf91dd56e3a4e8e6986'),
    (root14_dir + 'failure-origin.69b4cc.json', 'caebfd991b2a88f4d5ce6c944d5f4276f08ab11f2250dd34213d0b20a25634e3'),
    (rootmeta + 'failure-origin.d2cc6b.json', 'cddee98164c9720ceaa45bf3ffbc49d9ebe36f76e7e037f58a41ec504ea65ee4'),
    (rootmeta + 'failure-origin.efbf62.json', '854e41fb74d5c1b4c4ecbf5940ea17d902750571f9521b4ba7aaebb102feff5b'),
]]
bundle = {'schema': 'researchos.root321-registration-pin-bundle.v1',
    'expected_before': [320, 148, 417], 'expected_after': [321, 149, 421],
    'pins': pins, 'origin_refs': origin_refs, 'root_scope': root_scope,
    'go3_review_decision': 'READY_FOR_ROOT_REGISTERING_BOUNDED_GO3_DEBUG_COMPONENT_EVIDENCE_WITH_DECLARED_OPEN_GATES',
    'integration_controller_review_decision': 'READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE'}
raw = (json.dumps(bundle, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
with (OUT / 'pin-bundle.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'pin_bundle_ref': ref(OUT / 'pin-bundle.json')}, ensure_ascii=True))
