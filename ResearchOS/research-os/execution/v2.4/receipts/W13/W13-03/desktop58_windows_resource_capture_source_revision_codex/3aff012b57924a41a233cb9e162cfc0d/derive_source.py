"""Prepare a source-only, byte-invertible Windows resource constructor revision."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
base = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882/construct_root_inputs.desktop58.v3.py')
old_raw = base.read_bytes()
assert (hashlib.sha256(old_raw).hexdigest(), len(old_raw)) == ('2735a4c19b84721fe343662648766f9ffaf09b470ecd8c958a6ef5587d685df4',24167)
old = old_raw.decode('utf-8')
changes = [
 ("              'controller_evidence_reserve_seconds', 'launcher_evidence_reserve_seconds')\n    need(all(q.get(key) is not None for key in future)",
  "              'controller_evidence_reserve_seconds', 'launcher_evidence_reserve_seconds',\n              'wldp_static_ref', 'wldp_candidate_report_ref')\n    need(all(q.get(key) is not None for key in future)"),
 ("    correction = parse(frozen(q['mandatory_correction_ref']))\n    resource_map = parse(frozen(q['resource_map_ref']))",
  "    correction = parse(frozen(q['mandatory_correction_ref']))\n    resource_map = parse(frozen(q['resource_map_ref']))\n    wldp_report = parse(frozen(q['wldp_candidate_report_ref']))\n    need(wldp_report['stage'] == 'SOURCE_RESOURCE_CANDIDATE_ONLY' and\n         wldp_report['actual_qualification'] is False and\n         wldp_report['native_target_executed'] is False and\n         len(wldp_report['candidate_additions']) == 1,\n         'Wldp static evidence only, never prior native qualification')\n    candidate = wldp_report['candidate_additions'][0]\n    wldp_ref = {key: candidate[key] for key in ('path', 'sha256', 'bytes')}\n    need(q['wldp_static_ref'] == wldp_ref and\n         Path(wldp_ref['path']) == Path('C:/Windows/System32/wldp.dll') and\n         candidate['canonical_path'] == wldp_ref['path'],\n         'Root explicit canonical Wldp pin')\n    pe = parse(frozen(wldp_report['fresh_evidence_refs']['pe_explicit']))\n    names = parse(frozen(wldp_report['fresh_evidence_refs']['direct_import_name_matches']))\n    need(pe['targets']['wldp']['sha256'] == wldp_ref['sha256'] and\n         pe['targets']['wldp']['bytes'] == wldp_ref['bytes'] and\n         'wldp.dll' in [name.casefold() for name in pe['targets']['cmd']['pe']['delay_imports']] and\n         any(edge['from'] == pe['targets']['cmd']['path'] and\n             edge['raw_name'].casefold() == 'wldp.dll' and\n             edge['import_kind'] == 'delay_imports' and\n             edge['system32_filename_matches'] == [wldp_ref['path']] and\n             edge['catalog_matches'] == [] for edge in names['edges']),\n         'Direct static PE dependency and old-catalog gap')"),
 ("    for ref in runtime['files'] + correction['missing_Windows_refs']:\n        add(runtime_rows, ref)\n    need(len(runtime_rows) == 1282, 'Runtime base plus Windows40 identity count')",
  "    for ref in runtime['files'] + correction['missing_Windows_refs'] + [wldp_ref]:\n        add(runtime_rows, ref)\n    need(len(runtime_rows) == 1283, 'Runtime base plus Windows40 plus Wldp identity count')"),
 ("        'Windows40_correction_ref': q['mandatory_correction_ref'],\n        'metadata8_refs':",
  "        'Windows40_correction_ref': q['mandatory_correction_ref'],\n        'Windows_Wldp_static_ref': actual(wldp_ref),\n        'Windows_Wldp_static_evidence_ref': q['wldp_candidate_report_ref'],\n        'Windows_Wldp_actual_loaded_proven': False,\n        'metadata8_refs':"),
]
new = old
for before, after in changes:
    assert new.count(before) == 1, 'Expected exact source anchor once'
    new = new.replace(before, after, 1)
assert all(new.count(after) == 1 for _, after in changes)
inverse = new
for before, after in reversed(changes):
    inverse = inverse.replace(after, before, 1)
assert inverse.encode('utf-8') == old_raw
old_ast, new_ast = ast.parse(old), ast.parse(new)
old_funcs = {n.name:ast.dump(n, include_attributes=False) for n in old_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
new_funcs = {n.name:ast.dump(n, include_attributes=False) for n in new_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert set(old_funcs) == set(new_funcs)
assert [name for name in old_funcs if old_funcs[name] != new_funcs[name]] == ['run']
compile(new, '<proposed-source-only>', 'exec')
source_path = here / 'construct_root_inputs.desktop58.wldp.proposed.py'
with source_path.open('xb') as stream: stream.write(new.encode('utf-8'))
diff = ''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(base),tofile=str(source_path)))
with (here/'source.patch').open('xb') as stream: stream.write(diff.encode('utf-8'))
audit = {'schema':'researchos.desktop58-wldp-source-inverse.v1',
         'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY',
         'base_ref':{'path':str(base),'sha256':hashlib.sha256(old_raw).hexdigest(),'bytes':len(old_raw)},
         'proposed_ref':{'path':str(source_path),'sha256':hashlib.sha256(new.encode('utf-8')).hexdigest(),'bytes':len(new.encode('utf-8'))},
         'changed_exact_anchors':len(changes),'inverse_full_bytes_equal':True,
         'ast_changed_functions':['run'],'ast_unchanged_functions':sorted(set(old_funcs)-{'run'}),
         'static_compile':True,'candidate_executed':False}
with (here/'source-inverse.json').open('xb') as stream:
    stream.write((json.dumps(audit,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'))
print('source',audit['proposed_ref']['sha256'],audit['proposed_ref']['bytes'],'anchors',len(changes),'inverse',audit['inverse_full_bytes_equal'])
