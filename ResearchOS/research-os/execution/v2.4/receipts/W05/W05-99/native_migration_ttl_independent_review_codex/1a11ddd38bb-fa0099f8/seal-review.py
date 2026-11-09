from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
B=HERE.parent.parent
S=B/'native_migration_credential_ttl_revision_codex/1a11dd62452c7c895d4e2f51'
refs={}
def pin(path):
    p=Path(path);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
    actual=pin(ref['path'])
    assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'],str(Path(ref['path']).name)
    key=str(Path(ref['path']).resolve()).casefold()
    if key in refs: assert refs[key]['sha256']==actual['sha256']
    refs[key]=actual
    return Path(ref['path']).read_bytes()
def write(name,obj):
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    with (HERE/name).open('xb') as f:f.write(raw)
h=json.loads(verify(dict(path=str(S/'HDF.json'),sha256='9f9d502682e1666155a46a7a3c3a50b6b4c37a537852ebf068a40c851cea0c9d',bytes=5623)))
m=json.loads(verify(dict(path=str(S/'MF.json'),sha256='873b884ace4efb4a7750d163cdf26c8667bdc1e1b8617c2aa2700a83133d4445',bytes=3619)))
assert len(m['members'])==10
for ref in m['members'].values():verify(ref)
inputs=json.loads((S/'public-input-pins.json').read_bytes())['inputs']
assert len(inputs)==12
for ref in inputs:verify(ref)
base=verify(h['actual_formatted_T5_baseline_ref']);candidate=verify(h['source_ref'])
replacements=json.loads((S/'ttl-replacements.json').read_bytes())
assert len(replacements)==2
rest=candidate
for pair in replacements:
    old,new=pair['before'].encode(),pair['after'].encode()
    assert base.count(old)==1 and candidate.count(new)==1
    rest=rest.replace(new,old)
assert rest==base
changes=[i+1 for i,(a,b) in enumerate(zip(base.splitlines(),candidate.splitlines())) if a!=b]
assert changes==[466,470]
assert len(base.splitlines())==len(candidate.splitlines())
auth=Path(inputs[1]['path']).read_bytes()
assert b'if ttl <= 0 || ttl > 15*time.Minute {' in auth
assert b'if e != nil || !time.Now().Before(t) {' in auth
assert candidate.count(b'.IssueCredential(')==base.count(b'.IssueCredential(')==2
assert candidate.count(b't.Fatal(')==base.count(b't.Fatal(')==84
assert b'now.Add(4 * time.Minute)' in candidate
case_block=candidate.split(b'cases := map[string]string{',1)[1].split(b'\n\t}',1)[0]
cases=re.findall(rb'"([^"]+)"\s*:',case_block)
assert len(cases)==9
inventory=json.loads(Path(inputs[7]['path']).read_bytes())
matches=[]
def walk(v):
    if isinstance(v,dict):
        if v.get('sha256')==h['actual_formatted_T5_baseline_ref']['sha256']:matches.append(v)
        for z in v.values():walk(z)
    elif isinstance(v,list):
        for z in v:walk(z)
walk(inventory)
assert len(matches)==2 and all(x['bytes']==len(base) and Path(x['path'])==Path(h['actual_formatted_T5_baseline_ref']['path']) for x in matches)
old=B/'native_positive_failed_closed_independent_review_codex/1a11dd67f1a9f3b2848ac45b8'
prior=json.loads(verify(dict(path=str(old/'HDF.json'),sha256='8850ada4a694f314a2766e51bbc17da76b2c22520f6ae5d5c9ed2c48194eefc8',bytes=1597)))
verify(prior['manifest_ref'])
assert prior['Go_actual_exit']==1 and prior['two_Jobs_closed'] and not prior['native_case_pass']
d=json.loads((HERE/'diagnostics.json').read_bytes())
assert [x['ordinal'] for x in d['events']]==[824,825] and d['counterReset'] is False
assert all(x['actual_outer']==1 and x['actual_python'] is None and x['actual_native'] is None for x in d['events'])
review=dict(schema='researchos.independent-minimal-ttl-source-review.v1',
 decision='TTL_MINIMAL_SOURCE_ACCEPTED_FRESH_ISOLATED_BUILD_REQUIRED',
 candidate_ref=h['source_ref'],baseline_ref=h['actual_formatted_T5_baseline_ref'],
 changed_lines=changes,inverse_entire_baseline_bytes=True,
 original_IssueCredential_count=2,original_t_Fatal_count=84,cases=[x.decode() for x in cases],
 actual_compiler_inventory_matches=len(matches),production_auth_ref=inputs[1],
 production_cap_unchanged='0 < ttl <= 15*time.Minute',expiry_unchanged='time.Now().Before(expires_at)',
 original_grant_interval_minutes=4,initial_credential_interval_minutes=15,
 refresh_retry_or_autoapproval_added=False,remaining_source_bytes_preserved=True,
 prior_closed_failure820_ref=pin(old/'HDF.json'),source_diagnostic822_preserved=True,
 new_review_tool_errors=[824,825],counterReset=False,
 actions=dict(source_read=True,Go_or_native_execution=False,SQL=False,private_or_signing=False,canonical_write=False,provider_requests=0),
 security_findings=dict(critical=0,high=0,medium=0,low=0),
 scope='Two-expression source delta only; no dependency change or runtime acceptance',
 limitations=['Initial credential deadlines remain absolute; review hold does not refresh them','T7 fresh isolated composition/build and new case/config remain Root work','Original failure 820 and T6 branch are not rerun or merged by this review'],
 authority='NONE',formal_acceptance=False,native_acceptance=False,Owner_or_original_business_acceptance=False,stop=True)
write('review.json',review)
for ref in list(refs.values()):verify(ref)
write('verified-input-pins.json',dict(schema='researchos.independent-verified-pins.v1',references=list(refs.values()),count=len(refs),drift_count=0))
files=sorted(x for x in HERE.iterdir() if x.is_file())
members={x.name:pin(x) for x in files}
write('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=members,base_refs=list(refs.values()),base_ref_count=len(refs),drift_count=0))
handoff=dict(schema='researchos.independent-review-handoff.v1',decision=review['decision'],
 manifest_ref=pin(HERE/'MF.json'),review_ref=pin(HERE/'review.json'),report_ref=pin(HERE/'report.md'),
 counts=dict(members=len(members),files=len(members)+2,base_refs=len(refs)),source_accepted=True,
 new_mechanical_errors=2,diagnostics_preserved=[820,822,824,825],counterReset=False,
 authority='NONE',formal_acceptance=False,native_acceptance=False,stop=True)
write('HDF.json',handoff)
for ref in members.values():assert pin(ref['path'])==ref
print(json.dumps(dict(HDF=pin(HERE/'HDF.json'),MF=pin(HERE/'MF.json'),counts=handoff['counts'],decision=review['decision'],drift=0),ensure_ascii=True))

