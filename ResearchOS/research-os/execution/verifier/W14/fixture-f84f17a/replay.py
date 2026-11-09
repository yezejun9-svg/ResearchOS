from pathlib import Path
import subprocess, tempfile, json, os, hashlib, sqlite3, time

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
WORK=ROOT/'.local/worktrees/e2e-cycle'
GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
RUN=OUT/'independent-rerun'
RUN.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip()=='5c179a047e040947a05727906567617ac938f3c4'
assert subprocess.check_output(['git','status','--porcelain'],cwd=WORK,text=True)==''
commands=[]
def run(name,args,env,cwd):
    started=time.monotonic()
    proc=subprocess.Popen([str(x)for x in args],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr=proc.communicate(timeout=180 if name=='build' else 100)
    (RUN/(name+'.stdout.txt')).write_bytes(stdout)
    (RUN/(name+'.stderr.txt')).write_bytes(stderr)
    commands.append({'name':name,'argv':[str(x)for x in args],'cwd':str(cwd),'parent_observed_child_pid':proc.pid,'exit':proc.returncode,'elapsed_seconds':time.monotonic()-started})
    (RUN/'commands.json').write_text(json.dumps(commands,indent=2))
    assert proc.returncode==0,(name,proc.returncode)
    return proc.pid

with tempfile.TemporaryDirectory(prefix='researchos-w14-review-') as tmp:
    temp=Path(tmp);db=temp/'domain.sqlite';exe=temp/'review.test.exe';overlay=temp/'overlay.json'
    overlay.write_text(json.dumps({'Replace':{str(WORK/'internal/domain/w14_cycle_overlay_test.go'):str(WORK/'tests/e2e_cycle/_fixture/cycle_test.go')}}))
    (RUN/'overlay.json').write_bytes(overlay.read_bytes())
    env={k:v for k,v in os.environ.items()if 'JEV'not in k.upper() and 'TYPESAFE'not in k.upper()}
    env.update(RESEARCHOS_TASK_ID='W14',GOTOOLCHAIN='local',GOENV='off',W14_DATABASE=str(db),W14_EVIDENCE_DIR=str(RUN),W14_PHASE='build')
    cwd=WORK/'internal/domain'
    run('build',[GO,'test','-c','-overlay',overlay,'-o',exe,'.'],env,cwd)
    binary_hash=sha(exe)
    pids={}
    for phase,test in [('vertical','TestW14VerticalCycle'),('resume','TestW14SessionResume'),('missing-source','TestW14MissingSource')]:
        pids[phase]=run(phase,[exe,'-test.run','^'+test+'$','-test.v','-test.timeout','90s'],dict(env,W14_PHASE=phase),cwd)
    con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    counts=dict(con.execute('SELECT kind,count(*) FROM domain_objects GROUP BY kind').fetchall())
    principals=[{'id':i,'roles':json.loads(roles),'revoked':revoked}for i,roles,revoked in con.execute('SELECT id,roles,revoked FROM auth_principals ORDER BY id')]
    safe=[]
    allowed=['status','outcome','measurement_mode','verifier_principal_id','executor_principal_ids','independence_basis','receipt_hash','subject_ref','run_id','acceptance_id','mode','selected','latest_release_id','current_decision_refs','follow_up_task_ids','required_experiment_ids','release_id','title','executor_principal_id','run_state']
    for kind,ident,revision,body in con.execute("SELECT kind,id,revision,body FROM domain_objects WHERE kind IN ('AcceptanceReceipt','Task','Goal','Experiment','ResearchCycle','ProjectState','Release','Notification','DecisionReceipt','Run') ORDER BY kind,id"):
        val=json.loads(body);safe.append({'kind':kind,'id':ident,'revision':revision,'fields':{k:val[k]for k in allowed if k in val}})
    observation_count=con.execute('SELECT count(*) FROM runtime_observations').fetchone()[0]
    con.close()
    (RUN/'sqlite-readonly.json').write_text(json.dumps({'domain_object_counts':counts,'principals':principals,'business_objects':safe,'runtime_observations':observation_count,'db_mutated_by_reviewer':False},indent=2))
    (RUN/'environment.json').write_text(json.dumps({'worktree_head':'5c179a047e040947a05727906567617ac938f3c4','go_sha256':sha(GO),'test_binary_sha256':binary_hash,'database_sha256_before_cleanup':sha(db),'parent_observed_child_pids':pids,'provider_network_calls':0,'scope':'FIXTURE_SYNTHETIC'},indent=2))
assert not temp.exists()
assert subprocess.check_output(['git','status','--porcelain'],cwd=WORK,text=True)==''
(RUN/'cleanup.json').write_text(json.dumps({'temporary_directory_removed':True,'worktree_clean_after':True},indent=2))
print(json.dumps({'status':'REPLAY_COMPLETE','phases':3,'distinct_child_pids':len(set(pids.values())),'worktree_clean':True}))
