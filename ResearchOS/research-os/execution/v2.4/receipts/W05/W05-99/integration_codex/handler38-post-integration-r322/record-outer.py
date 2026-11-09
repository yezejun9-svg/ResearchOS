"""Record known completed outer tool fields, without fabricating native streams."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
LAUNCHER_OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_root_launcher_codex/9f028224a18f4d0fb49f854014ace6d0'
LAUNCHER = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2/launcher.v2.py'

def ref(path, expected=None):
    p = Path(path).resolve()
    raw = p.read_bytes()
    item = {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item

for name in ['grant-preflight', 'source-only-integration']:
    observed = json.loads((LAUNCHER_OUT / (name + '.owned-result.json')).read_bytes())
    assert observed['actual_native_exit'] == observed['result']['actual_exit'] == 0
completed = json.loads((LAUNCHER_OUT / 'completed.json').read_bytes())
assert completed['actual_controller_native_exit'] == 0
record = {'schema': 'researchos.main38-root-launch-outer-completion.v1', 'actor': 'codex:/root',
    'initial_tool_chunk': 'c822f3', 'actual_tool_session': 65537, 'completion_tool_chunk': 'eab84b',
    'session_state': 'CLOSED_DO_NOT_POLL_OR_RERUN', 'actual_outer_exit': 0,
    'reported_root_launcher_exit': 0, 'actual_root_launcher_native_exit_separately_observed': None,
    'launcher_output_root': LAUNCHER_OUT.relative_to(ROOT).as_posix(),
    'launcher_ref': ref(LAUNCHER, 'be5fdfae7c321376dc60f964167a92f06725bfe83e97a826e50a6eae8f2a2bc2'),
    'launcher_completed_ref': ref(LAUNCHER_OUT / 'completed.json'),
    'launcher_manifest_ref': ref(LAUNCHER_OUT / 'manifest.json'),
    'actual_root_launcher_report_first_failure': None,
    'known_tool_fields_transcribed_from_original_conversation': True,
    'this_record_is_not_original_native_stdout_or_stderr': True,
    'original_outer_tool_response_locator': 'conversation tools.exec_command c822f3 / tools.write_stdin eab84b',
    'native_owned_child_streams_retained_in_launcher_receipt': True,
    'automatic_retry': False, 'counter_reset': False, 'source_acceptance': False, 'formal_increment': 0}
raw = (json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
with (OUT / 'outer-completion.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'outer_completion_ref': ref(OUT / 'outer-completion.json')}, ensure_ascii=True))
