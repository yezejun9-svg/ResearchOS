import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp513'
M = R / 'execution/v2.4/receipts/W05/W05-99/qualification_repair_composition_input_map_codex/20261015-current-chat'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    b = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def new(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    temp = p.with_name(p.name + '.cp513.pending')
    with temp.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(temp, p)


assert ref(M / 'COLLECTION-manifest.json')['sha256'] == '8f48ee1f9cdd1068052ad3f7796b36dd6aeed8d9bb77c2f9ddb39557b7dd4b4d'
for item in read(M / 'COLLECTION-manifest.json')['files']:
    p = R / item['path']
    assert ref(p) == item
assert ref(R / read(M / 'COLLECTION-manifest.json')['helper']['path']) == read(M / 'COLLECTION-manifest.json')['helper']
cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 512 and ow['revision'] == 298 and len(cp['failure_counters']) == 1643
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=R, text=True).splitlines()) == 20
for item in read(R / 'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']
O.mkdir(exist_ok=False)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
diagnostics = [
    {'tool_chunk': 'a8402c', 'native_exit': 1, 'kind': 'ROOT_MISSING_OUTER_AGENTS_READ', 'detail': 'Get-Content of D:/作品集/ResearchOS/AGENTS.md failed because that file is absent. The user-supplied instructions remain effective; canonical project research-os/AGENTS.md was read successfully in the same batch. No source or shared write.'},
    {'tool_chunk': '22df6c', 'native_exit': 0, 'kind': 'ROOT_OVERSIZED_RESUME_DISPLAY', 'detail': 'Full CP512 resume display was truncated by the tool output limit. Original complete hashed RESUME.current.json exists unchanged; required selected facts were recovered from the compact checkpoint and later registrar input. No complete display capture is claimed.'},
]
new(O / 'root-read-diagnostics.json', diagnostics)
old = list(cp['failure_counters'])
for index, item in enumerate(diagnostics, 1):
    origin = '20261015|root-cp513-read-diagnostic-' + str(index)
    assert not any(v.get('origin_key') == origin for v in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'READ_DIAGNOSTIC_PRESERVED', 'detail': item, 'evidence_ref': ref(O / 'root-read-diagnostics.json'), 'counter_reset': False})
assert cp['failure_counters'][:1643] == old
resume = read(B / 'continuation-cp512/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v91', at=now, checkpoint_revision=513, ownership_revision=299, failure_records_preserved=len(cp['failure_counters']), qualification_repair_composition_input_map_ref=ref(M / 'COLLECTION-manifest.json'))
resume['next_command'] = 'Continue CP508 STOP and CP512 B Source; freeze then independent Source reviews. Readonly verifier init audit preliminarily NOT_PROVABLE because original Close/Wait postreturn proof absent; wait frozen exact residual, do not invent operational proof. Composition input map verifies15A/19STOP/9B/51C/17D,106unique paths; map is not Source/actual authority. Main4f/dirty20/indexempty/originalCore/RunUNKNOWN preserved. No actual action. Formal0/42/all22open.'
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=513, expected_previous_revision=512, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp513=rr, qualification_repair_composition_input_map_ref=ref(M / 'COLLECTION-manifest.json'))
cp['evidence_index'].append({'kind': 'READONLY_QUALIFICATION_REPAIR_COMPOSITION_INPUT_MAP', 'ref': rr, 'formal_increment': 0})
ow.update(revision=299, expected_previous_revision=298, updated_at=now, updated_by='codex:/root')
ow['special_paths']['qualification_repair_composition_input_map'] = {'owner': 'codex:/root', 'mode': 'READ_ONLY_RESOURCE_MAP', 'state': 'FROZEN_RESOURCE_ONLY', 'evidence_ref': ref(M / 'COLLECTION-manifest.json'), 'write_scope': [str(M)], 'source_authority': False, 'actual_authority': False}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, data in raw.items():
    assert p.read_bytes() == data
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP513\n\nRead `' + rr['path'] + '` first. STOP and B are active Source cards; composition input map is resource-only. Verifier audit preliminary NOT_PROVABLE; original data/Run/processes preserved. Formal0/42/all22open; preserved records' + str(len(cp['failure_counters'])) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 513, 'ownership': 299, 'failure_records': len(cp['failure_counters']), 'resume': rr, 'map': ref(M / 'COLLECTION-manifest.json')}))
