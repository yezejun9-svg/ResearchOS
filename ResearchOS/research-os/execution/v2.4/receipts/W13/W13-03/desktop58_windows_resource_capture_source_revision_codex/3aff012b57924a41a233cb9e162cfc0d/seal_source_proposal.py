"""Seal source-only proposal; never imports or executes proposed constructor."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
repo = Path('D:/作品集/ResearchOS/research-os')
static = repo/'execution/v2.4/receipts/W05/W05-99/desktop58_windows_runtime_static_candidate_codex/1d68f5262a334f82b63d21abd4a350ca/report.json'
old_reg = repo/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882'
old_q = old_reg/'root-construction.parameters.desktop58.json'
old_runtime = old_reg/'runtime-resources.desktop58.json'
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,obj):
    path=here/name
    raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as f: f.write(raw)
    return pin(path)
static_pin=pin(static)
assert (static_pin['sha256'],static_pin['bytes']) == ('2b21ee05cfafd36494a96761e4a4420429686ce9174ca3fe2a0c41bf3be8d88b',6760)
old_runtime_pin=pin(old_runtime)
assert (old_runtime_pin['sha256'],old_runtime_pin['bytes']) == ('fb0f6e6dbf6d85c212925bd5861a4f429fcd444f201ff259036b8fc099300af5',308090)
src=pin(here/'construct_root_inputs.desktop58.wldp.proposed.py')
inverse=json.loads((here/'source-inverse.json').read_text(encoding='utf-8'))
assert inverse['proposed_ref']==src and inverse['inverse_full_bytes_equal'] is True
prior=json.loads(static.read_text(encoding='utf-8'))
candidate=prior['candidate_additions'][0]
wldp_ref={key:candidate[key] for key in ('path','sha256','bytes')}
assert pin(Path(wldp_ref['path']))==wldp_ref
old_rows=json.loads(old_runtime.read_text(encoding='utf-8'))['files']
assert len(old_rows)==1296 and wldp_ref['path'].casefold() not in {r['path'].casefold() for r in old_rows}
field_additions={'schema':'researchos.desktop58-fresh-root-resource-field-additions.v1',
                 'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY',
                 'new_root_q_fields':{'wldp_static_ref':wldp_ref,'wldp_candidate_report_ref':static_pin},
                 'all_prior_root_run_values_reusable':False,
                 'future_new_root_uuid':None,'future_canonical_before':None,
                 'future_failure_origin_cut':None,'authorization':False,
                 'expected_runtime_old_count':1296,'expected_runtime_static_candidate_count':1297,
                 'actual_loaded_complete':False}
fields_pin=save('root-q.resource-fields.proposed.json',field_additions)
origins=[pin(here/'failure-origin-001.json'),pin(here/'failure-origin-002.json')]
report={'schema':'researchos.desktop58-wldp-capture-source-proposal.v1',
        'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY','source_ready_for_independent_review':True,
        'candidate_executed':False,'actual_runtime_qualification':False,
        'formal_case_accepted_delta':0,'new_tool_failure_count':2,
        'prior_frozen_failure_count_modified':False,
        'basis_refs':{'failed_reg_q':pin(old_q),'failed_runtime_catalog':old_runtime_pin,
                      'static_candidate_report':static_pin},
        'proposed_source_ref':src,'source_patch_ref':pin(here/'source.patch'),
        'source_inverse_ref':pin(here/'source-inverse.json'),
        'future_q_field_additions_ref':fields_pin,'new_failure_origin_refs':origins,
        'source_delta':['Require Root literal Wldp ref and pinned source-only report.',
                        'Bind independent cmd.exe PE delay-import evidence and exact Wldp file pin.',
                        'Extend runtime base plus Windows40 set by one Wldp row; expected 1283 before metadata14.',
                        'Record Wldp static provenance and actual-loaded-proven false in runtime overlay.'],
        'static_audit':{'source_bytes_inverse_equal':True,'changed_functions':['run'],
                        'other_functions_ast_unchanged':inverse['ast_unchanged_functions'],
                        'candidate_compiles_without_import':True,'old_runtime_file_count':1296,
                        'expected_new_runtime_file_count':1297},
        'open':['API-set mapping unresolved.','Actual loaded-module complete set unresolved.',
                'Source has not been independently reviewed or selected by a fresh Root scope.',
                'Old 72ff registration, q, catalog and failed native output cannot be reused as qualification.'],
        'root_next':'Allocate fresh registration and origin cut; populate all future literals independently, copy reviewed proposed constructor, perform fresh complete static capture, independent review, new scope/grant, then one bounded run.',
        'main_or_canonical_modified':False,'old_source_or_catalog_modified':False}
report_pin=save('report.json',report)
members=[pin(p) for p in sorted(here.iterdir(),key=lambda x:x.name.casefold()) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
manifest_pin=save('manifest.json',{'schema':'researchos.desktop58-wldp-capture-source-manifest.v1',
                                    'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY','report_ref':report_pin,
                                    'members':members,'immutable_seal':'xb'})
handoff_pin=save('handoff.json',{'schema':'researchos.desktop58-wldp-capture-source-handoff.v1',
                               'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY','report_ref':report_pin,
                               'manifest_ref':manifest_pin,'source_ref':src,
                               'root_q_field_additions_ref':fields_pin,
                               'source_review_required':True,'candidate_executed':False,
                               'formal_case_accepted_delta':0,'failure_count_delta':2,'stop':'STOPPED'})
for name,ref in [('source',src),('report',report_pin),('manifest',manifest_pin),('handoff',handoff_pin),('origin1',origins[0]),('origin2',origins[1])]:
    print(name,ref['sha256'],ref['bytes'])
