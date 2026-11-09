import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'complete-public-graph-and-g2-r310'


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


assert sys.flags.isolated and not sys.flags.optimize and len(sys.argv) == 2
candidate = sys.argv[1]
assert re.fullmatch(r'[0-9a-f]{40}', candidate)
replay_id = uuid.uuid4().hex
source = (OLD / 'list_replay.v2.py').read_text(encoding='utf-8', errors='strict')
replacements = {
    "OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r310-534857db-public-plan'": "OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_codex/" + replay_id + "'",
    "EXPORT = ROOT / '.local/independent-session-list-r310-534857db-public-plan'": "EXPORT = ROOT / '.local/independent-session-list-closedcopy-root-" + replay_id + "'",
    "CANDIDATE = '534857db99fa5e694987f877af74c322eaa2a0b3'": "CANDIDATE = '" + candidate + "'\nSOURCE_PARENT = '534857db99fa5e694987f877af74c322eaa2a0b3'",
    "'e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0'": "'9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae'",
    "DRAFT / 'list_independent_scope.v2.json'": "DRAFT / 'root_finite14_scope.draft.json'",
    "assert cp['revision'] >= 310": "assert cp['revision'] >= 317",
    "cp['work_in_progress']['session_list_identity_independent_scope_ref']": "cp['work_in_progress']['session_list_closedcopy_root_finite14_scope_ref']",
    "assert set(delta) == set(SOURCES) and len(delta) == 2": "assert delta == ['internal/api/v2_sessions_test.go']",
    "CANDIDATE + '^'], ROOT).decode().strip() == BASE": "CANDIDATE + '^'], ROOT).decode().strip() == SOURCE_PARENT",
    "path.read_text(encoding='utf-8').splitlines()": "path.read_text(encoding='utf-8', errors='strict').splitlines()",
    "generated_mains[0].read_text(encoding='utf-8')": "generated_mains[0].read_text(encoding='utf-8', errors='strict')"
}
for old, new in replacements.items():
    assert source.count(old) == 1, old
    source = source.replace(old, new)
assert "BASE = '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'" in source
assert source.count("'c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1'") == 1
ast.parse(source)
with (OUT / 'root_finite14_replay.py').open('xb') as stream:
    stream.write(source.encode('utf-8'))
tree = ast.parse(source)
literal = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ['NAMES', 'SOURCES', 'RESOURCE_PLAN_REF', 'PUBLIC_JEV']:
                literal[target.id] = ast.literal_eval(node.value)
assert len(literal['NAMES']) == 14 and len(literal['PUBLIC_JEV']) == 36
scope = save('root_finite14_scope.draft.json', {
    'schema': 'researchos.session-list-closedcopy-root-independent-replay-scope.v1',
    'state': 'DRAFT_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED',
    'owner': 'codex:/root', 'author': 'codex:/root/command_queue_impl',
    'source_commit': candidate, 'actual_candidate_parent_expected': '534857db99fa5e694987f877af74c322eaa2a0b3',
    'protected_body_source_base': '22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
    'protected_body_bytes': 14633, 'protected_body_sha256': 'c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1',
    'runner_ref': ref(OUT / 'root_finite14_replay.py'),
    'owned_process_helper_ref': ref(OUT.parent / 'independent-cli-list-scopes-r308/windows_owned_process.py'),
    'previous_root_driver_ref': ref(OLD / 'list_replay.v2.py'),
    'ordered_cases': literal['NAMES'], 'source_paths_sha256': literal['SOURCES'],
    'actual_source_delta_paths': ['internal/api/v2_sessions_test.go'],
    'public_compiler_catalog_ref': literal['RESOURCE_PLAN_REF'],
    'individually_approved_public_Go_resources': literal['PUBLIC_JEV'],
    'new_output_root': 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_codex/' + replay_id,
    'new_export_root': '.local/independent-session-list-closedcopy-root-' + replay_id,
    'authorization_prerequisites': ['Author source-only exact1 commit and sealed actual14/full closure current evidence.', 'Non-author source/evidence review.', 'Independent static review of this exact runner/scope.', 'Root actual canonical registration and exact prelaunch hash grant.'],
    'limits': {'cases': 14, 'per_case_HTTP_maximum': 16, 'total_HTTP_maximum': 224, 'SDK_MODEL_Node_external_paid_private_calls': 0},
    'same_input_automatic_retry': False, 'counter_reset': False, 'first_unexpected_stop': True,
    'database_policy': 'New native fixture originals closed; closed copy read only with immutable=1; full main hash/schema/columns/typed-row multisets; pre/post no sidecars; no DB deletion.',
    'input_policy': 'Fresh full public Git export plus approved518 Go catalog and36 extra public compiler resources; full compiled variants, WORK/importcfg/generated/archives/OS/Python/source/exe frozen and checked before/native-after/proof-after each of14 cases.',
    'retained_limits': ['Implicit rowid not independently exported.', 'Same-user path validation TOCTOU is not excluded.'],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0
})
print(json.dumps({'runner': ref(OUT / 'root_finite14_replay.py'), 'scope': scope, 'actual_export_compile_tests': 0}, ensure_ascii=True))
