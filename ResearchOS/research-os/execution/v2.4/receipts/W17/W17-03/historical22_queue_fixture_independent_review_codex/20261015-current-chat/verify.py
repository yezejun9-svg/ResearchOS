import datetime, hashlib, io, json, os, re, sqlite3, subprocess, sys, tarfile
from pathlib import Path, PurePosixPath

MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
AUTHOR=MAIN/'execution/v2.4/receipts/W17/W17-03/historical22_queue_fixture_repair_source_codex/20261015-current-chat'
SCOPE=MAIN/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp499/historical22-fixture-independent-review-scope.json'
SRC=MAIN/'.local/resources/historical22-active-queue-helper-20261015'
WT=MAIN/'.local/worktrees/historical22-queue-fixture-repair-20261015'
OLD=MAIN/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'
TEMP=MAIN/'.local/builds/historical22-independent-review-20261015'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
def save(name,obj):
    p=OUT/name
    with p.open('x',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def git(cwd,*args):
    r=subprocess.run(['git',*args],cwd=cwd,capture_output=True)
    if r.returncode: raise RuntimeError((args,r.returncode,r.stderr.decode(errors='replace')))
    return r.stdout.decode('utf-8').strip()
def pin(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def guards():
    dirty=git(MAIN,'diff','--name-only','-z').split('\0')
    return {'main_head':git(MAIN,'rev-parse','HEAD'),'main_index':git(MAIN,'diff','--cached','--name-only'),
      'main_dirty':{s:sha(MAIN/s) if (MAIN/s).is_file() else 'MISSING' for s in dirty if s},
      'candidate_head':git(WT,'rev-parse','HEAD'),'candidate_tree':git(WT,'rev-parse','HEAD^{tree}'),
      'candidate_status':git(WT,'status','--porcelain=v1','-uno'),
      'candidate_source':pin(WT/'internal/domain/backup_configuration_upgrade_test.go'),
      'helper':pin(SRC/'internal/domain/active_queue_fixture_child_test.go'),
      'db':pin(load(AUTHOR/'closed-source22-05.json')['db_path']),
      'record':pin(AUTHOR/'closed-source22-05.json')}
def log(entry):
    entry['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (OUT/'diagnostic-ledger.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(entry,ensure_ascii=False)+'\n')
def provenance():
    assert sha(SCOPE)=='244db7a4e655a5204d27dd144dfb79efa480fe18ea26edae35cda15176e83ea8'
    scope=load(SCOPE); checks=[]
    def check_ref(d):
        if isinstance(d,dict):
            if 'path' in d and 'sha256' in d:
                p=Path(d['path']);p=p if p.is_absolute() else MAIN/p
                actual=pin(p);assert actual['sha256']==d['sha256'].removeprefix('sha256:'),(str(p),'SHA')
                if 'bytes' in d: assert actual['bytes']==d['bytes'],(str(p),'bytes')
                checks.append(actual)
            for v in d.values():check_ref(v)
        elif isinstance(d,list):
            for v in d:check_ref(v)
    check_ref(scope)
    final=load(AUTHOR/'FINAL-02.json');check_ref(final['refs'])
    construction=load(MAIN/scope['construction_scope']['path']);check_ref(construction)
    pins=load(MAIN/construction['historical_pins_ref']['path']);check_ref(pins['archive_manifest'])
    expected={x['relative_path']:x for x in pins['files']};assert len(expected)==502
    archive=OLD/'git-archive.stdout';assert sha(archive)=='4a82f6471c644ef25489ebbedb3c32452391bcd0e00dcd58453f46200fb9a9b6'
    found=set()
    with tarfile.open(archive,'r:') as tf:
        for m in tf:
            name=m.name.rstrip('/');p=PurePosixPath(name)
            assert not p.is_absolute() and ':' not in name and '\\' not in name and '..' not in p.parts
            if m.isdir():continue
            assert m.isfile() and name in expected and name not in found
            data=tf.extractfile(m).read();want=expected[name]
            assert len(data)==want['bytes'] and hashlib.sha256(data).hexdigest()==want['sha256']
            found.add(name)
    assert found==set(expected)
    actual_files={p.relative_to(SRC).as_posix() for p in SRC.rglob('*') if p.is_file()}
    assert actual_files-set(expected)=={'internal/domain/active_queue_fixture_child_test.go'}
    for rel,want in expected.items():
        p=SRC/rel;assert p.is_file() and p.stat().st_size==want['bytes'] and sha(p)==want['sha256']
    vector=load(OLD/'source_after.json');assert len(vector)==5922
    resolved={};translated=0
    for name,want in vector.items():
        if '\\frozen_source\\' in name:
            p=SRC/name.split('\\frozen_source\\',1)[1];translated+=1
        else:p=Path(name)
        assert p.is_file() and sha(p)==want, name
        resolved[str(p)]=want
    native=load(AUTHOR/'fresh-native-pins.json');assert len(native['entries'])==29
    check_ref(native['entries'])
    build=load(AUTHOR/'build-helper-05.invocation.json')
    assert sha(SRC/'internal/domain/active_queue_fixture_child_test.go')==build['helper_sha256']==final['historical_helper_sha256']
    assert sha(build['actualargv'][0])==build['go_exe_sha256']
    assert sha(build['actualargv'][5])==build['test_exe_sha256']
    ledger=load(AUTHOR/'FAILURE-LEDGER.json');assert len(ledger['entries'])==18
    fails=0
    for entry in ledger['entries']:
        assert sha(entry['record_path'])==entry['record_sha256']
        inv=load(entry['record_path']);assert inv['native_exit']==entry['native_exit']
        check_ref(entry)
        fails+=entry['native_exit']!=0
    assert fails==7
    for phase in ('before','after'):
        inv=load(AUTHOR/f'historical-input-{phase}-05.json')
        assert len(inv)==503
        assert all(sha(SRC/k)==v for k,v in inv.items())
    assert git(WT,'diff','--name-only',scope['base_commit'],scope['candidate_commit']).splitlines()==scope['allowed_candidate_diff']
    original=load(AUTHOR/'closed-source22-05.json');db=Path(original['db_path'])
    assert 'sha256:'+sha(db)==original['db_sha256']
    conn=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    facts={'schema':conn.execute('SELECT min(version),max(version),count(*) FROM schema_migrations').fetchone(),
      'identities':conn.execute("SELECT count(*) FROM sqlite_master WHERE name='client_command_identities'").fetchone()[0],
      'queue_phases':conn.execute('SELECT state,count(*) FROM client_command_queue GROUP BY state').fetchall(),
      'table_counts':{t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('client_sessions','client_queue_fences','client_command_queue','client_control_requests','client_control_receipts','idempotency','resource_effects','domain_versions','runtime_dispatches')},
      'run':conn.execute("SELECT json_extract(body,'$.status'),json_extract(body,'$.lease_epoch') FROM domain_objects WHERE kind='Run' AND id=?",(original['run_id'],)).fetchone(),
      'effects':conn.execute("SELECT json_extract(body,'$.status'),count(*) FROM resource_effects GROUP BY json_extract(body,'$.status')").fetchall()}
    conn.close()
    assert facts['schema']==(1,22,22) and facts['identities']==0
    assert dict(facts['queue_phases'])=={'CONSUMED':1,'DROP_REQUESTED':3,'DROPPED':2,'UNKNOWN':1}
    assert all(facts['table_counts'][t]>0 for t in facts['table_counts'] if t!='runtime_dispatches')
    assert len(original['public_replies'])==9
    assert [r['method'] for r in original['public_replies']]==['goal.start']+['session.send']*7+['session.control']
    assert [r['response']['status'] for r in original['public_replies']]==['COMPLETED']*8+['ACKNOWLEDGED']
    assert 'sha256:'+sha(db)==original['db_sha256']
    save('input-provenance.json',{'scope':pin(SCOPE),'checked_refs':checks,'source_files':502,'archive_files':len(found),'extra_files':sorted(actual_files-set(expected)),'compiler_vector':5922,'translated':translated,'compiler_vector_file':pin(OLD/'source_after.json'),'native_pins':29,'historical_author_failures':fails,'historical_author_attempts':18,'db_facts':facts,'original_db_unchanged':True,'resolved_compiler_inputs':resolved})
    log({'kind':'provenance','result':'PASS','native_exit':0,'assertions':'exact scope/ref/source/archive/compiler/native/DB/ledger checks'})
    print('provenance PASS: 502 source, 5922 vector, 29 native, 7 retained failures',flush=True)
def run(label,mode):
    inv=load(AUTHOR/'candidate-active7.invocation.json')
    allow=inv['allowlist_env'].copy();tmp=TEMP/label;tmp.mkdir(parents=True,exist_ok=False)
    for k in ('TEMP','TMP','GOTMPDIR'):allow[k]=str(tmp)
    evidence=OUT/('snapshots-'+label);evidence.mkdir()
    allow['RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']=str(evidence)
    argv=inv['argv'].copy()
    if mode=='adjacent':argv[6]='^TestConfigurationUpgrade(Frozen22ProgramLock|NativeCLI)$'
    expected_marker=None
    if mode=='missing':
        allow['RESEARCHOS_HISTORICAL22_ACTIVE_RECORD']='';expected_marker='pinned historical22 active queue fixture record required'
    elif mode=='bad-record-pin':
        allow['RESEARCHOS_HISTORICAL22_ACTIVE_RECORD_SHA256']='sha256:'+'0'*64;expected_marker='fixture record pin'
    elif mode in ('bad-db-pin','bad-row-pin'):
        rec=load(AUTHOR/'closed-source22-05.json');rec['db_sha256' if mode=='bad-db-pin' else 'preupgrade_rows_hash']='sha256:'+'0'*64
        rp=OUT/(label+'-record.json');save(rp.name,rec)
        allow['RESEARCHOS_HISTORICAL22_ACTIVE_RECORD']=str(rp);allow['RESEARCHOS_HISTORICAL22_ACTIVE_RECORD_SHA256']='sha256:'+sha(rp)
        expected_marker='historical22 fixture bytes or claims' if mode=='bad-db-pin' else 'historical22 row pin'
    env=os.environ.copy();env.update(allow)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result=subprocess.run(argv,cwd=WT,env=env,capture_output=True)
    (OUT/(label+'.stdout.raw')).write_bytes(result.stdout);(OUT/(label+'.stderr.raw')).write_bytes(result.stderr)
    events=[json.loads(line) for line in result.stdout.splitlines() if line.startswith(b'{')]
    results={e['Test']:e['Action'] for e in events if e.get('Test') and e['Action'] in ('pass','fail','skip')}
    expected_tests=2 if mode=='adjacent' else 1
    correct=len(results)==expected_tests and all(v==('fail' if expected_marker else 'pass') for v in results.values()) and (result.returncode!=0 if expected_marker else result.returncode==0)
    if expected_marker:correct=correct and expected_marker.encode() in result.stdout
    rec={'argv':argv,'cwd':str(WT),'allowlist_env':allow,'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_exit':result.returncode,'test_results':results,'tests_executed':len(results),'tests_skipped':sum(v=='skip' for v in results.values()),'expected_failure_marker':expected_marker,'expectation_met':correct,'stdout':pin(OUT/(label+'.stdout.raw')),'stderr':pin(OUT/(label+'.stderr.raw'))}
    save(label+'.invocation.json',rec);log({'kind':'fresh-test','label':label,'native_exit':result.returncode,'test_results':results,'expected_rejection':bool(expected_marker),'expectation_met':correct})
    print(label,result.returncode,results,'expected',correct,flush=True)
    assert correct,label
if __name__=='__main__':
    try:
        if sys.argv[1]=='audit':
            log({'kind':'prior-review-tool-diagnostic','native_exit':1,'diagnosis':'One exploratory command used nonexistent client_goal_start_test.go and listed not-yet-created receipt directory; corrected to client_protocol_goal_test.go. No source write. Full status output overlarge; now using tracked-only guards.'})
            save('guards-before.json',guards());provenance()
        elif sys.argv[1]=='audit-resume':
            log({'kind':'review-checker-correction','native_exit':0,'diagnosis':'Initial expected seven distinct final queue states was incorrect: actual public CANCEL converts ENQUEUED to DROPPED and SENDING/SDK_ACCEPTED to DROP_REQUESTED. Original test also calls CANCEL after phase synthesis. Expected post-CANCEL distribution corrected; all prior failures retained.'})
            log({'kind':'prior-review-tool-diagnostic','native_exit':1,'diagnosis':'Exploratory Python omitted utf-8 when reading author record and rg guessed nonexistent client_protocol_control.go; corrected encoding and found actual client_protocol_queue_control.go. No input write.'})
            provenance()
        elif sys.argv[1]=='run':run(sys.argv[2],sys.argv[3])
        elif sys.argv[1]=='after':
            after=guards();save('guards-after.json',after);assert after==load(OUT/'guards-before.json');print('guards unchanged',flush=True)
    except Exception as exc:
        log({'kind':'review-check-failure','native_exit':1,'error':str(exc)});raise
