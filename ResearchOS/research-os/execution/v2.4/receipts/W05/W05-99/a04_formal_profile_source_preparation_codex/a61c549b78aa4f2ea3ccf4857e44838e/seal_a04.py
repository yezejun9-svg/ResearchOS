"""Seal this source proposal by pure file IO; no candidate is imported or run."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = ROOT / 'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e'
PACKAGE = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
FILES = {
    'execution/v2.4/formal_profile_w05.py': 'formal_profile_w05.proposed.py',
    'execution/v2.4/formal_case_index.py': 'formal_case_index.w05.proposed.py',
    'ops/ci/runtime_w05_live.py': 'runtime_w05_live.proposed.py',
    'ops/ci/runtime.py': 'runtime.w05.route.proposed.py',
    'ops/ci/export_a04_live.py': 'export_a04_live.proposed.py',
}
OLD = {
    'execution/v2.4/formal_case_index.py':
        '970ab391f2dd10a4f5e2713355a4a68757814994ef87b9aa92b9e555c12f1205',
    'ops/ci/runtime.py':
        '32189089f9bde198d4f846a907675edc0c1776722015646db5575d312ae4f7f8',
}


def pin(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT)
            else str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw)}


def put(name, value):
    path = HERE / name
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                      indent=2, allow_nan=False) + '\n').encode('utf-8')
    with path.open('xb') as output:
        output.write(raw)
    return pin(path)


def check(ok, message):
    if not ok:
        raise ValueError(message)


check(HERE.is_dir(), 'source namespace absent')
check(pin(PACKAGE / 'contracts/acceptance.json')['sha256'] ==
      'ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66',
      'v2.4 A04 baseline changed')
baseline = json.loads((PACKAGE / 'contracts/acceptance.json').read_text(encoding='utf-8'))
case = next(row for row in baseline['cases'] if row['id'] == 'A04')
check([row['id'] for row in case['assertions']] ==
      ['A04-01', 'A04-02', 'A04-03', 'A04-04', 'A04-05', 'A04-06'],
      'six frozen assertions changed')
check(case['mode'] == 'LIVE_WINDOWS' and case['status'] == 'NOT_RUN',
      'frozen status or mode changed')
pre = json.loads((HERE / 'precheck.a04.json').read_text(encoding='utf-8'))
check(pre['count'] == 25 and all(row['outcome'] in ('PASS', 'REJECT')
                                for row in pre['checks']) and
      pre['candidate_executions'] == 0 and pre['formal_increment'] == 0,
      'pure IO controls not closed')
source_pins, reverse = {}, []
for target, name in FILES.items():
    proposed = HERE / name
    ast.parse(proposed.read_text(encoding='utf-8'), filename=name)
    source_pins[target] = pin(proposed)
    old_path = ROOT / target
    if target in OLD:
        old = pin(old_path)
        check(old['sha256'] == OLD[target], 'Main changed: ' + target)
        before = old_path.read_text(encoding='utf-8').splitlines(True)
        after = proposed.read_text(encoding='utf-8').splitlines(True)
        backward = ''.join(difflib.unified_diff(
            after, before, fromfile='proposed/' + name,
            tofile='Main/' + target, n=3))
        check(bool(backward), 'missing inverse: ' + target)
        reverse.append({'target': target, 'before': old,
                        'proposed': source_pins[target],
                        'inverse_unified_diff': backward})
    else:
        check(not old_path.exists(), 'added target already exists: ' + target)
        reverse.append({'target': target, 'before': None,
                        'proposed': source_pins[target],
                        'inverse': 'remove newly installed target only if byte pin matches'})
check(pin(ROOT / 'execution/v2.4/formal_case_index.py')['sha256'] == OLD[
    'execution/v2.4/formal_case_index.py'], 'Main index changed during seal')
check(pin(ROOT / 'ops/ci/runtime.py')['sha256'] == OLD[
    'ops/ci/runtime.py'], 'Main runtime changed during seal')
inverse_ref = put('source.inverse.json', {
    'schema': 'researchos.a04-source-inverse.v1',
    'scope': 'SOURCE_PREPARATION_ONLY', 'entries': reverse})
report_ref = put('report.json', {
    'schema': 'researchos.w05.a04-source-preparation-report.v1',
    'status': 'SOURCE_PREPARATION_ONLY',
    'source_ready_for_independent_review': True,
    'source_accepted': False,
    'formal_case_accepted_increment': 0,
    'native_executions': 0, 'model_requests': 0,
    'Main_changed': False,
    'frozen_acceptance_ref': pin(PACKAGE / 'contracts/acceptance.json'),
    'frozen_assertions': [row['id'] for row in case['assertions']],
    'frozen_mode': case['mode'],
    'candidate_targets': source_pins,
    'checks': {'ast_parse_five': 'PASS', 'pure_io_25': 'PASS',
               'Main_before_hashes_unchanged': 'PASS',
               'inverse_complete': 'PASS'},
    'readiness_gates': {
        'five_scenarios': 'REQUIRES_CURRENT_ROOT_CAPTURE',
        'H08_nested': 'REQUIRES_REAL_ORIGINAL_DB_JSONL_AND_VERSION_MATRIX',
        'P01_own_cli': 'REQUIRES_INSTALLED_CLI_INTERACTIVE_JSONL_ORIGINALS',
        'U02_real_issue': 'REQUIRES_DELIVERY_SELECTION_FILE_TEST_ORIGINALS',
        'Root_authority': 'REQUIRES_ACTUAL_REGISTRATION_GRANT_JOB_AND_TOOL_IO',
        'GLOBAL_EVIDENCE_V1': 'FOUR_PRODUCER_PARTS_ONLY_FIFTH_INDEPENDENT_REVIEW_OPEN',
        'COST': 'UNKNOWN_MUST_REMAIN_NULL_UNLESS_ORIGINAL_ACCOUNTING_PINS',
        'current_context': 'REQUIRES_ROOT_CURRENT_SOURCE_AND_COVERAGE',
        'owner_acceptance': 'NOT_RUN'},
    'owner_handler': 'fixed trusted W05 profile in index; no receipt dynamic import',
    'live_handler': 'postcapture selector reader; G01 fixture route retained',
    'exporter': 'four producer parts and current context only; no reviewer/issuance',
    'limits': [
        'No actual H08/P01/U02 or five-scenario product original evidence exists in this Source namespace.',
        'A pinned JSON fact projection alone does not prove DB, JSONL, process and model provenance.',
        'Typed new Root registration/grant, reviewer delivery and original-accounting producers need independent validation before Main adoption.',
        'The separate SDK trial grant and prior CLI2 fixture qualification are not A04 LIVE authority.'
    ],
    'inverse_ref': inverse_ref,
    'selected_tool_io_ref': pin(HERE / 'tool-io.selected.json'),
    'pure_io_ref': pin(HERE / 'precheck.a04.json')})
members = [pin(HERE / name) for name in (
    'formal_profile_w05.proposed.py', 'formal_case_index.w05.proposed.py',
    'runtime_w05_live.proposed.py', 'runtime.w05.route.proposed.py',
    'export_a04_live.proposed.py', 'build_index.py', 'precheck_a04.py',
    'precheck.a04.json', 'tool-io.selected.json', 'source.inverse.json',
    'report.json')]
manifest_ref = put('manifest.json', {
    'schema': 'researchos.a04-source-manifest.v1',
    'namespace': HERE.relative_to(ROOT).as_posix(),
    'members': members, 'member_count': len(members),
    'formal_case_accepted_increment': 0})
handoff_ref = put('handoff.json', {
    'schema': 'researchos.a04-source-handoff.v1',
    'status': 'STOPPED_SOURCE_ONLY',
    'report_ref': report_ref, 'inverse_ref': inverse_ref,
    'manifest_ref': manifest_ref,
    'source_pins': source_pins,
    'pure_io_ref': pin(HERE / 'precheck.a04.json'),
    'tool_io_ref': pin(HERE / 'tool-io.selected.json'),
    'next_action': 'independent source review; then Root separately adopts and produces current LIVE originals',
    'formal_case_accepted_increment': 0})
print(json.dumps({'report': report_ref, 'manifest': manifest_ref,
                  'handoff': handoff_ref, 'inverse': inverse_ref},
                 ensure_ascii=False, separators=(',', ':')))
