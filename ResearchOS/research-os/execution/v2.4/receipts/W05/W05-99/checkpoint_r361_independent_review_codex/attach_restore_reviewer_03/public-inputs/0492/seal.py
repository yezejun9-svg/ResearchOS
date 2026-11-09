import pathlib,json,hashlib,datetime
O=pathlib.Path(__file__).resolve().parent
Q=O.parents[1]/'legacy_migration_fixture_source_revision_codex/fc052947b4d14f769bff1e735151c52d'
def pin(p):
 p=pathlib.Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(n):return json.loads((O/n).read_bytes())
def write(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
sv=read('static-verification.json');cl=read('closing-pins.json');g=read('sourceguard.close.json')
assert sv['all_passed'] and cl['all_unchanged'] and g['closed'] and g['retained_handles_count']==0 and not g['errors']
assert pin(Q/'HDF.json')['sha256']=='aea3953e6bccad7c09d9939fbe521b432987ce7e0a22ab1b9d826232224f10eb'
assert pin(Q/'MF.json')['sha256']=='21fc3d154c4fbadc4fd75a070b73c4306d248786f9aa0f0df02fe9aab5b7817d'
findings=write('findings.json',dict(status='SOURCE_ACCEPTED_WITH_EXECUTION_GATES',blocking_source_findings=[],resolved_findings=[dict(id='LEGACY-ROLLBACK-001',resolution='schema-only database binding removes missing-Project early-return precondition; runtime not tested')],nonblocking_notes=[dict(id='LEGACY2-MANIFEST-EXCLUSIONS',detail='41 members; copied review MF and postseal IO separately pinned and verified')],execution_gates=['fresh guarded Root compile/component actual','BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE'],reviewer_mechanical_errors=[dict(ordinal=844,actual_outer_exit=None,actual_marked_Python_exit=None,native_exit=None,process_started=False,origin_ref=pin(O/'diagnostic-844.json'))],authority='NONE',formal_acceptance=False))
handoff=write('HDF.json',dict(schema='researchos.independent-source-review-handoff.v1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='SOURCE_ACCEPTED_WITH_EXECUTION_GATES',authority='NONE',formal_acceptance=False,source_HDF_ref=pin(Q/'HDF.json'),source_MF_ref=pin(Q/'MF.json'),candidate_refs=sv['candidate_refs'],report_ref=pin(O/'report.md'),findings_ref=findings,independent_checks_ref=pin(O/'static-verification.json'),input_pins_ref=pin(O/'input-pins.json'),closing_pins_ref=pin(O/'closing-pins.json'),sourceguard_close_ref=pin(O/'sourceguard.close.json'),original_tool_io_ref=pin(O/'tool-io.json'),sourceguard_entries=len(g['entries']),sourceguard_closed=True,retained_handles_count=0,all_pins_unchanged=True,canonical_refs=cl['canonical_refs'],Main_refs=cl['Main_refs'],original_Test_names=12,original_assertion_calls=126,unrelated_Test_bodies_byte_equal=9,other_candidates_unchanged=3,exact_inverse_v1=True,source_manifest_member_count=sv['manifest_members'],source_manifest_excluded_actual=sv['manifest_excluded_actual'],ordinary=sv['ordinary'],component_acceptance='NOT_RUN',execution=dict(audit_actual_outer_exit=0,audit_actual_marked_Python_exit=0,Go_AST=None,Go=None,gofmt=None,compiler=None,SQL=None,native=None,model=None),mechanical_error_844_ref=pin(O/'diagnostic-844.json'),counts_reset=False,writes='unique review namespace only',next_actor='Root independent fresh guarded compile/component execution when gates permit',state='STOP',manifest_exclusions=['MF.json self fingerprint','postseal-tool-io.json later invocation result, separately pinned']))
rows=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p not in [O/'MF.json',O/'postseal-tool-io.json']:
  rows.append(dict(relative_path=str(p.relative_to(O)),**pin(p)))
manifest=write('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',authority='NONE',formal_acceptance=False,status='SOURCE_ACCEPTED_WITH_EXECUTION_GATES',members=rows,member_count=len(rows),exclusions=['MF.json self fingerprint','postseal-tool-io.json later invocation result, separately pinned']))
print(json.dumps(dict(HDF=handoff,MF=manifest,members=len(rows),all_input_pins_unchanged=True,status='SOURCE_ACCEPTED_WITH_EXECUTION_GATES'),ensure_ascii=False))

