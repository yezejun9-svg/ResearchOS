import pathlib, json, hashlib, difflib
E=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat')
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_independent_review_codex/20261015-current-chat'
W=R/'.local/worktrees/owned-core-stop-effect-state-r5-20261015'
T=R/'.local/owned-core-stop-r5-independent-review-20261015-tmp'
C=pathlib.Path('C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r5-independent-review-20261015')
C.mkdir(exist_ok=False); (T/'gotmp').mkdir(exist_ok=True)
lineage=[]
def copy(name,dest=None,transform=lambda s:s):
    src=A/name; dst=E/(dest or name); before=src.read_text(encoding='utf-8');after=transform(before)
    dst.write_text(after,encoding='utf-8',newline='\n')
    patch=dst.name+'.patch';(E/patch).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(src),tofile=str(dst))),encoding='utf-8')
    lineage.append(dict(source=str(src),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),copy=str(dst),copy_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),diff=patch))
def paths(s):return s.replace('owned-core-stop-authority-r4-20261015','owned-core-stop-effect-state-r5-20261015').replace('owned-core-stop-r4-independent-review-20261015','owned-core-stop-r5-independent-review-20261015')
copy('reviewer_logger.py',transform=lambda s:paths(s).replace("if code == 0 and args[-1].replace", "if False and args[-1].replace"))
copy('run_logged.py');copy('fixture_parent_r4.go');copy('independent_store_review_windows_test.go')
copy('fixture_e2e_review.py',transform=paths)
def negative(s):
    s=paths(s).replace('if MODE not in ("positive",','if MODE not in ("review_missing","review_null","positive",',1)
    needle='    desc=json.loads(run("fixture-describe",[FIXTURE,"--mode","describe","--root",data,"--out",out,"--pid",core_pid]))'
    inject='''    if MODE in ("review_missing","review_null"):
        body={"payload":{"capability":"MODEL"}}
        if MODE=="review_null":body["state"]=None
        db=sqlite3.connect(data/"researchos.sqlite",timeout=5)
        subject=same_subject()
        db.execute("INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)",(subject["project"],subject["run"],"review-extra-malformed-model",json.dumps(body)))
        db.commit();db.close()
'''
    assert needle in s;s=s.replace(needle,inject+needle,1)
    needle='    if MODE in ("bad_exit_missing","bad_wait_missing"):'
    inject='''    if MODE in ("review_missing","review_null"):
        plan=json.loads((out/"plan.json").read_text(encoding="utf-8"))
        safety=plan["preflight_safety"]
        assert plan["eligibility"]=="STOP_UNAVAILABLE",plan
        assert safety["non_model_effects"]==1 and safety["confirmed_model_effects"]==1,safety
        assert not (out/"STOP_ATTEMPT.json").exists() and not (out/"TERMINATE_INTENT.json").exists()
        assert core.poll() is None
        observed=json.loads(run("fixture-describe-after-rejection",[FIXTURE,"--mode","describe","--root",data,"--out",out,"--pid",core_pid]))
        assert observed["native"]==desc["native"]
        assert observed["census"]==desc["census"]
        record={"mode":MODE,"case":str(CASE),"preflight_eligibility":plan["eligibility"],"missing":plan.get("missing",[]),"preflight_safety":safety,"baseline":plan["baseline"],"preflight_grant_sha256":sha(pre_grant_path.read_bytes()),"preflight_executable_sha256":sha(pre_exe.read_bytes()),"stop_grant_built":False,"native_signal_count":0,"same_native_alive":True,"census_unchanged":True,"additional_effect_body":body}
        write_json(CASE/"case-result.json",record)
        print(json.dumps(record,indent=2),flush=True)
        sys.exit(0)
'''
    assert needle in s;return s.replace(needle,inject+needle,1)
copy('fixture_e2e_review.py','fixture_e2e_negative.py',negative)
(E/'store-overlay.json').write_text(json.dumps({'Replace':{str(W/'internal/store/independent_store_review_windows_test.go'):str(E/'independent_store_review_windows_test.go')}},indent=2),encoding='utf-8')
(E/'fixture-lineage.json').write_text(json.dumps(lineage,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(lineage,ensure_ascii=False,indent=2))
