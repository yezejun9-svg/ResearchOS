import pathlib,json,hashlib,datetime
O=pathlib.Path(__file__).resolve().parent
B=O.parents[1];N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r361-provenance-qualified-source-ready-revision'
def pin(p):
 p=pathlib.Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(n):return json.loads((O/n).read_bytes())
def write(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
checks=read('review-checks.json');closing=read('closing-pins.json');guard=read('sourceguard.close.json')
assert checks['all_passed'] and closing['all_unchanged'] and guard['closed'] and guard['retained_handles_count']==0 and not guard['errors']
current=[]
for x in closing['refs']:
 ref=x['expected'];actual=pin(ref['path']);current.append(dict(expected=ref,actual=actual,matched=actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']))
final=write('final-pins.json',dict(refs=current,all_unchanged=all(x['matched'] for x in current)));assert all(x['matched'] for x in current)
findings=write('findings.json',dict(blocking_findings=[],resolved_findings=[dict(id='CP360-EXIT-833-001',resolution='Effective CP361 actual Python exit NULL; original source-reported and inferred1 retained with exact original counterproof')],qualified_evidence=[dict(ordinal=835,resolution='Exact decimal FILETIME identities from pinned raw native invocations; source-reported inexact values remain immutable')],critical_count=0,important_count=0,new_mechanical_failures=0,authority='CHECKPOINT_CONSISTENCY_REVIEW_ONLY',product_authority='NONE',formal_acceptance=False))
hdf=write('HDF.json',dict(schema='researchos.independent-checkpoint-review-handoff.v1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='CP361_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY',checkpoint_revision=361,source_handoff_ref=pin(N/'handoff.json'),source_manifest_ref=pin(N/'manifest.json'),canonical_refs=checks['canonical_refs'],report_ref=pin(O/'report.md'),findings_ref=findings,verification_ref=pin(O/'review-checks.json'),input_pins_ref=pin(O/'input-pins.json'),sourceguard_close_ref=pin(O/'sourceguard.close.json'),closing_pins_ref=pin(O/'closing-pins.json'),final_pins_ref=final,public_copy_index_ref=pin(O/'public-copy-index.json'),original_tool_io_ref=pin(O/'original-tool-io.json'),Root_original_tool_io_ref=checks['root_original_tool_io_ref'],old836_outer_fields_preserved=True,old834_unqualified_records_byte_exact=True,only_old_payloads_qualified=[833,835],new_original_ordinals=list(range(839,848)),registered_failures=845,highest_observed_ordinal=847,next_failure_ordinal=848,counter_reset=False,sourceguard_entries=len(guard['entries']),sourceguard_closed=True,retained_handles_count=0,all_pins_unchanged=True,independent_actual_outer_exit=0,independent_actual_marked_Python_exit=0,new_mechanical_failures=0,important_count=0,critical_count=0,authority='CHECKPOINT_CONSISTENCY_REVIEW_ONLY',product_authority='NONE',formal_acceptance=False,reviewer_Go_SQL_native_model_executed=False,Main_canonical_Source_writes=False,STOP=True,manifest_exclusions=['MF.json self fingerprint','postseal-tool-io.json later execution result separately pinned']))
rows=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p not in [O/'MF.json',O/'postseal-tool-io.json']:rows.append(dict(relative_path=str(p.relative_to(O)),**pin(p)))
mf=write('MF.json',dict(schema='researchos.independent-checkpoint-review-manifest.v1',members=rows,member_count=len(rows),authority='CHECKPOINT_CONSISTENCY_REVIEW_ONLY',product_authority='NONE',formal_acceptance=False,exclusions=['MF.json self fingerprint','postseal-tool-io.json later execution result separately pinned']))
print(json.dumps(dict(HDF=hdf,MF=mf,members=len(rows),decision='CP361_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY'),ensure_ascii=False))

