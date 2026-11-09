"""Seal a source-only Windows resource candidate from already captured bytes."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
repo = Path('D:/作品集/ResearchOS/research-os')
inv = repo / 'execution/v2.4/receipts/W13/W13-03/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882/build-current58.invocation.json'
cat = repo / 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882/runtime-resources.desktop58.json'
def pin(path):
    raw = path.read_bytes()
    return {'path':str(path), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
def save(name, payload):
    path = here / name
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream: stream.write(raw)
    return pin(path)
inv_pin, cat_pin = pin(inv), pin(cat)
assert (inv_pin['sha256'],inv_pin['bytes']) == ('c8914f095d0b29bfccebf898da89f58ef9e718e4d0aa1008177ebd291346b764',8359619)
assert (cat_pin['sha256'],cat_pin['bytes']) == ('fb0f6e6dbf6d85c212925bd5861a4f429fcd444f201ff259036b8fc099300af5',308090)
pe = json.loads((here/'pe-explicit-static-read.json').read_text(encoding='utf-8'))
matched = json.loads((here/'direct-import-name-matches.json').read_text(encoding='utf-8'))
wldp = pe['targets']['wldp']
cmd = pe['targets']['cmd']
edges = matched['edges']
direct = [e for e in edges if e['from'].casefold() == cmd['path'].casefold() and e['raw_name'].casefold() == 'wldp.dll']
assert len(direct)==1 and direct[0]['import_kind']=='delay_imports'
assert direct[0]['system32_filename_matches']==[wldp['path']] and not direct[0]['catalog_matches']
assert (wldp['sha256'],wldp['bytes']) == ('ecf34c9c64b2e6be9f622f0ca3a6ca7b95dcfdb88eb0419b045b853934bae0ba',443664)
assert all(not p['reparse'] and not p['is_junction'] and not p['is_symlink'] for p in wldp['parents'])
non_api = [e for e in edges if not e['api_set_unresolved']]
missing = sorted({p for e in non_api if not e['catalog_matches'] for p in e['system32_filename_matches']})
assert missing == [wldp['path']]
unresolved = sorted({e['raw_name'] for e in edges if e['api_set_unresolved']})
report = {
  'schema':'researchos.desktop58-windows-resource-static-candidate.v1',
  'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY',
  'actual_qualification':False, 'formal_case_accepted_delta':0, 'native_target_executed':False,
  'input_refs':{'failed_build_invocation':inv_pin,'selected_runtime_catalog':cat_pin},
  'fresh_evidence_refs':{'pe_explicit':pin(here/'pe-explicit-static-read.json'),
                         'direct_import_name_matches':pin(here/'direct-import-name-matches.json'),
                         'version_and_tool_io':pin(here/'tool-io.selected.json')},
  'candidate_additions':[{'path':wldp['path'],'canonical_path':wldp['canonical_path'],
                          'sha256':wldp['sha256'],'bytes':wldp['bytes'],
                          'reason':'cmd.exe PE delay-import Wldp.dll; direct System32 filename resolution; absent selected runtime catalog',
                          'file_version':'10.0.26100.8875 (WinBuild.160101.0800)',
                          'product_version':'10.0.26100.8875'}],
  'static_dependency':{'cmd_sha256':cmd['sha256'],'cmd_bytes':cmd['bytes'],
                       'direct_import_edges_examined':len(edges),
                       'system32_entries_examined':matched['system32_entries_examined'],
                       'direct_non_api_missing_count':len(missing),
                       'wldp_direct_delay_import':True,
                       'wldp_non_api_direct_imports_present_in_catalog':all(e['catalog_matches'] for e in non_api if e['from'].casefold()==wldp['path'].casefold()),
                       'api_set_names_unresolved':unresolved},
  'open': ['API-set and ext-ms host mappings are not resolved from PE filenames.',
           'Delay imports are conditional; static PE metadata does not prove the full actual loaded-module set.',
           'The selected catalog remains incomplete; the failed run cannot be converted to a qualification by unioning this candidate.'],
  'next_action':'Root must perform a fresh complete runtime resource capture, independent review, fresh scope/registration/grant and one execution; preserve failed run and frozen catalog.',
  'new_tool_failure_count':1, 'new_tool_failure_origin_ref':pin(here/'failure-origin-001/origin.json'),
  'old_canonical_modified':False, 'old_catalog_modified':False,
}
report_pin = save('report.json',report)
files = [p for p in here.rglob('*') if p.is_file() and p.name not in {'manifest.json','handoff.json'}]
manifest = {'schema':'researchos.desktop58-static-candidate-manifest.v1',
            'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY',
            'members':[pin(p) for p in sorted(files,key=lambda x:str(x).casefold())],
            'report_ref':report_pin,'immutable_seal':'xb'}
manifest_pin=save('manifest.json',manifest)
handoff={'schema':'researchos.desktop58-static-candidate-handoff.v1','stage':'SOURCE_RESOURCE_CANDIDATE_ONLY',
         'report_ref':report_pin,'manifest_ref':manifest_pin,
         'candidate_count':1,'candidate_path':wldp['path'],
         'qualification':False,'formal_case_delta':0,'tool_failure_count_delta':1,
         'failure_origin_ref':pin(here/'failure-origin-001/origin.json'),
         'stop':'STOPPED'}
handoff_pin=save('handoff.json',handoff)
for label,item in [('report',report_pin),('manifest',manifest_pin),('handoff',handoff_pin),('failure_origin',handoff['failure_origin_ref'])]:
    print(label,item['sha256'],item['bytes'])
