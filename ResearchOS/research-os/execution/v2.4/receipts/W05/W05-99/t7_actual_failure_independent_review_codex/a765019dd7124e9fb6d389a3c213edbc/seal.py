from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def dump(name,v):(O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
v=read('final-verification.json');a=read('root-delivered-anchor-checks.json')
issues=[]
if v['reference_failures']:issues.append('reference failure')
if v['guard_failures']:issues.append('guard failure')
if any(not x['closed'] for x in v['jobs']):issues.append('unclosed job')
if any(not x['match'] for x in a):issues.append('anchor mismatch')
if not v['release_specific_snapshot_inspection_binding_valid']:issues.append('release binding')
if not v['whole_SQL_read_receipt']['typed_rows_digest_matches']:issues.append('typed rows digest')
h=dict(schema='researchos.independent-actual-failure-review-handoff.v1',authority='NONE',formal_acceptance=False,decision=v['decision'] if not issues else 'REVIEW_NOT_ACCEPTED',scope='failed actual execution + whole readonly SQLite inspection + specific release and Job/guard cleanup only',native_positive_accepted=False,Owner_accepted=False,original_business_accepted=False,nine_cases_accepted=False,issues=issues,important_followup='T7-ENV-001 isolated TEMP/TMP omitted from backup child environment; new frozen Source/build/actual required',namespace=str(O),report_ref=pin(O/'report.md'),verification_ref=pin(O/'final-verification.json'),input_pins_ref=pin(O/'final-input-pins.json'),anchor_checks_ref=pin(O/'root-delivered-anchor-checks.json'),guard_checks_ref=pin(O/'guard-closure-checks.json'),Root_original_tool_io_ref=pin(O/'inputs/final-release/original-tool-io.json'),jobs=v['jobs'],historical_only=['deleted DB/WAL/SHM','server-close canonical refs'],new_mechanical_errors=0,Root_failure_ordinals_preserved=[835,836,837],prior_failure_prefix_and_FULL_not_reset=True,reviewer_Go_SQL_native_model_execution=False,canonical_or_Source_writes=False,stop=True)
dump('HDF.json',h)
members=[dict(relative_path=p.relative_to(O).as_posix(),**pin(p)) for p in sorted(O.rglob('*')) if p.is_file() and p.relative_to(O).as_posix() not in ('MF.json','postseal-tool-io.json')]
dump('MF.json',dict(schema='researchos.independent-actual-review-manifest.v1',authority='NONE',members=members,exclusions={'MF.json':'self fingerprint','postseal-tool-io.json':'original seal return appended afterward and separately pinned'},formal_acceptance=False))
print(json.dumps(dict(decision=h['decision'],issues=issues,member_count=len(members),refs={n:pin(O/n) for n in ('HDF.json','MF.json','report.md','final-verification.json')},new_mechanical_errors=0,formal_acceptance=False),ensure_ascii=False))

