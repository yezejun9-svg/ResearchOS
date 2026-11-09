"""Independent read-only audit; no Go/product commands or Canon writes."""
import collections
import hashlib
import json
from pathlib import Path
import re
import runpy
import zipfile
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
SRC=REPO/'execution/v2.4/receipts/W09/W09-99/current_main24_revalidation_codex/20261012-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
    raw=p.read_bytes();return {'path':p.relative_to(REPO).as_posix(),'sha256':digest(raw),'bytes':len(raw)}
def check(r):
    p=REPO/r['path'];assert pin(p)==r,r['path'];return p
assert pin(SRC/'handoff-manifest.json')['sha256']=='1d3f2c2f5628bf3421b9c43819ce2bd7dbd49d5173112c5e47b9cdfc03f845ec'
assert pin(SRC/'result.json')['sha256']=='1d2ee656c748a463caaaacd621d3872f6a3d0935c45b76782861341583a881e1'
for r in read(SRC/'handoff-manifest.json')['files']:check(r)
result=read(SRC/'result.json');mapping=read(SRC/'assertion-map.json')
snapshots=[]
for version,suffix in ((1,''),(2,'-v2')):
    snap=read(SRC/f'source-snapshot{suffix}.json');archive=SRC/f'current-source-snapshot{suffix}.zip'
    assert digest(archive.read_bytes())==snap['archive_sha256']
    files={r['path']:r for r in snap['files']};assert len(files)==len(snap['files'])
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())==set(files)
        for name,r in files.items():
            raw=z.read(name);assert digest(raw)==r['sha256'] and len(raw)==r['bytes'],name
            assert digest((REPO/name).read_bytes())==r['sha256'],('Main source drift',name)
            assert digest((Path(snap['execution_snapshot'])/name).read_bytes())==r['sha256'],('execution snapshot drift',name)
    snapshots.append(files)
assert len(snapshots[1])==581 and all(snapshots[1][p]==r for p,r in snapshots[0].items())

all_pass=[];assertions=[];attempt_results=[]
for directory in (SRC,SRC/'attempt-002'):
    invocation=read(directory/'invocation.json');stdout=directory/'go-test.stdout.jsonl';stderr=directory/'go-test.stderr.txt'
    assert digest(stdout.read_bytes())==invocation['stdout_sha256'] and digest(stderr.read_bytes())==invocation['stderr_sha256']
    tool=invocation['go_executable'];assert digest(Path(tool['path']).read_bytes())==tool['sha256'] and Path(tool['path']).stat().st_size==tool['bytes']
    argv=invocation['argv'];assert argv[:4]==[tool['path'],'test','-count=1','-json']
    wanted=invocation['selected_tests'];regex=argv[argv.index('-run')+1]
    assert regex=='^(?:'+'|'.join(wanted)+')$'
    events=[json.loads(x) for x in stdout.read_bytes().splitlines()]
    started={};passed=[];pending={};fails=[];buildfails=[]
    for event in events:
        name=event.get('Test');owner=(event.get('Package'),name);action=event['Action']
        if action=='run' and name:
            assert owner not in started;started[owner]=event
        if action=='pass' and name:
            assert owner in started and owner not in passed;passed.append(owner)
            assert name.split('/')[0] in wanted
        if action=='fail':fails.append(event)
        if action=='build-fail':buildfails.append(event)
        joined=pending.get(owner,'')+event.get('Output','');parts=joined.split('\n');pending[owner]=parts.pop()
        for line in parts:
            for family in ('W09_ASSERTION','W18_ASSERTION'):
                if line.startswith(family+' '):
                    record=json.loads(line[len(family)+1:]);assert record['status']=='PASS'
                    assertions.append({'family':family,'test':name,'record':record,'stdout_ref':pin(stdout)})
    assert not any(pending.values())
    tops=[n for _,n in passed if '/' not in n]
    if directory==SRC:
        assert invocation['exit_code']==1 and len(tops)==2 and buildfails and not any(x.get('Test') for x in fails)
    else:
        assert invocation['exit_code']==0 and len(tops)==13 and not fails and not buildfails
        assert set(tops)==set(wanted)
    all_pass.extend(passed)
    attempt_results.append({'invocation_ref':pin(directory/'invocation.json'),'exit_code':invocation['exit_code'],
      'top_level_pass':tops,'pass_with_subtests':len(passed),'build_failure_count':len(buildfails)})
assert len(all_pass)==21 and len({n for _,n in all_pass if '/' not in n})==15
assert assertions==mapping['assertions']
assert collections.Counter(x['family'] for x in assertions)=={'W09_ASSERTION':19,'W18_ASSERTION':22}
assert set(mapping['actual_tests'])=={n for _,n in all_pass}

members={};events={};envelopes=0
owned_pins=mapping['owned_raw_pins'];assert len(owned_pins)==586
assert {r['path'] for r in owned_pins}=={p.relative_to(REPO).as_posix() for d in (SRC/'owned',SRC/'attempt-002/owned') for p in d.rglob('*.raw')}
inv2=read(SRC/'attempt-002/invocation.json')
for r in owned_pins:
    path=check(r).resolve();members[path]=r
    label=path.name.split('-',1)[1][:-4]
    try:value=json.loads(path.read_bytes())
    except (json.JSONDecodeError,UnicodeDecodeError):continue
    if isinstance(value,dict) and '_run_id' in value:
        assert value['_run_id']==inv2['run_id']
        assert value['_test_name'].replace('/','_')==path.parent.name
        assert value['_test_name'] in mapping['actual_tests']
        events.setdefault(label,[]).append({'value':value,'path':path,'pin':r,'test':value['_test_name']});envelopes+=1
# W0901 exports predate an expected-map entry; use the actual Go predicates
# independently, and report their null expected as a formal-consumer limitation.
extra_expected={
 'W0901-CROSS-PROJECT-SECOND-PROJECT-READS-ITS-OWN-SAME-NAME-BODY':{'hits':1,'content_status':200},
 'W0901-CROSS-PROJECT-SAME-NAME-ARTIFACT-METADATA-DENIED':{'status':404,'code':'NOT_FOUND'},
 'W0901-CROSS-PROJECT-SAME-NAME-SEALED-BODY-DENIED':{'status':404,'marker_leaks':0},
 'W0901-CROSS-PROJECT-SAME-NAME-SEARCH-DENIED':{'status':404,'code':'NOT_FOUND'},
 'W0901-CROSS-PROJECT-SAME-NAME-MARKER-ABSENT-FROM-FIRST-PROJECT-REPLIES':{'marker_leaks':0,'first_project_indexed_foreign_rows':0,'second_project_indexed_own_rows':1,'first_project_own_hits':1,'artifact_ids_distinct':True,'evidence_ids_distinct':True},
 'W0901-CROSS-PROJECT-SAME-NAME-CAPTURE-THROUGH-FIRST-ROOT-REFUSED':{'status':422,'code':'GATE_FAILED'},
 'W0901-SEALED-BODY-SERVED-BEFORE-REVOCATION':{'hits':1},
 'W0901-CREATE-REFUSED-WHEN-SNAPSHOT-NOT-CURRENT':{'status':422},
 'W0901-REVOKED-ROOT-IDEMPOTENT-REPLAY-DOES-NOT-SERVE-SEALED-BODY':{'status':412,'code':'STALE_REVISION','marker_leaks':0},
 'W0901-REVOKED-ROOT-FRESH-SEARCH-RETURNS-NO-HITS':{'hits':0,'marker_leaks':0},
 'W0901-REVOKED-ROOT-SEALED-BODY-READ-DENIED':{'status':409,'marker_leaks':0},
 'W0901-REVOKED-ROOT-CANNOT-CAPTURE-AGAIN':{'status':404,'code':'NOT_FOUND'}
}
null_expected=[]
for a in assertions:
    rec=a['record']
    if a['family']=='W18_ASSERTION':
        assert rec['actual']==rec['expected'] and rec.get('evidence')
    else:
        r=rec['owned_export_ref'];path=Path(r['path']).resolve();assert path in members
        assert digest(path.read_bytes())==r['sha256'] and len(path.read_bytes())==r['bytes']
        value=read(path);assert value['assertion_id']==rec['assertion_id'] and value['actual']==rec['evidence']
        if value['expected'] is None:
            wanted=extra_expected[rec['assertion_id']];null_expected.append(rec['assertion_id'])
        else:wanted=value['expected']
        assert wanted and all(value['actual'].get(k)==v for k,v in wanted.items())
        assert rec['test_name']==a['test'] and rec['run_id']==inv2['run_id']
for r in mapping['backup_owned_pins']:check(r)
closure=REPO/result['closure_source_ref']['path'];check(result['closure_source_ref'])
api=runpy.run_path(str(closure),run_name='independent_existing_a06_oracle')
api['verify_a06']({'members':members,'events':events})
native=read(SRC/'attempt-002/backup-owned/native-restore.json')
assert native['manifest']['migrations']==list(range(1,25))
assert native['report']['status']=='RESTORED_RECONCILIATION_REQUIRED'
assert native['report']['recovery']['credentials']=='REVOKED_REPROVISION_LOCALLY'
assert native['report']['recovery']['external_actions_dispatched']==0
delta=read(SRC/'source-delta.json');context=read(check(delta['original_context_ref']))
changed=[];unchanged=0
for old in context['version_vector']['source_files']:
    current=digest((REPO/old['path']).read_bytes())
    if current!=old['sha256']:changed.append({'path':old['path'],'old':old['sha256'],'current':current})
    else:unchanged+=1
assert changed==delta['changed'] and unchanged==delta['unchanged_count']
old_paths={x['path'] for x in context['version_vector']['source_files']}
added=sorted(p.relative_to(REPO).as_posix() for directory in ('internal/domain','adapters/retrieval') for p in (REPO/directory).glob('*.go') if p.relative_to(REPO).as_posix() not in old_paths)
assert added==delta['added']
summary={'schema':'researchos.w09.current-main-development-independent-audit.v1',
 'reviewer_id':'/root/w09_header_gate_review','author_id':'/root/resume_audit',
 'issued_at':datetime.now(timezone.utc).isoformat(),'status':'PASS_BOUNDED_DEVELOPMENT_EVIDENCE',
 'result_ref':pin(SRC/'result.json'),'manifest_ref':pin(SRC/'handoff-manifest.json'),
 'attempts':attempt_results,'snapshots_file_counts':list(map(len,snapshots)),
 'main_and_execution_snapshot_hashes':'MATCH_ALL581','original_snapshot_members_unchanged':True,
 'raw_assertion_counts':dict(collections.Counter(x['family'] for x in assertions)),
 'owned_raw_pins_verified':len(members),'owned_event_envelopes_verified':envelopes,
 'null_expected_exports_development_only':null_expected,
 'original_a06_oracle':'PASS','backup_migrations':native['manifest']['migrations'],
 'historical_source_changed':changed,'historical_source_added':added,
 'product_commands_rerun':False,'formal_acceptance_issued':False,'canon_modified':False}
target=OUT/'evidence-audit.json';assert not target.exists()
target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit_ref':pin(target),'tests':15,'pass_with_subtests':21,'assertion_counts':summary['raw_assertion_counts'],'owned':len(members),'A06':'PASS','snapshot_members':list(map(len,snapshots)),'source_changed':len(changed),'source_added':len(added)},ensure_ascii=False,indent=2))
