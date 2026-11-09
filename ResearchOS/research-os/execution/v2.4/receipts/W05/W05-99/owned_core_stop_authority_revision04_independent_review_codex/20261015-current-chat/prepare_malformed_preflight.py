import pathlib,hashlib,json,difflib
E=pathlib.Path(__file__).resolve().parent
src=E/'fixture_e2e_review.py';dst=E/'fixture_e2e_malformed_preflight.py'
before=src.read_text(encoding='utf-8');after=before.replace('if MODE not in ("positive",','if MODE not in ("review_malformed_effect_preflight","positive",',1)
needle='    desc=json.loads(run("fixture-describe",[FIXTURE,"--mode","describe","--root",data,"--out",out,"--pid",core_pid]))'
inject='''    if MODE=="review_malformed_effect_preflight":
        db=sqlite3.connect(data/"researchos.sqlite",timeout=5)
        subject=same_subject()
        db.execute("INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)",(subject["project"],subject["run"],"review-extra-malformed-model",json.dumps({"payload":{"capability":"MODEL"}})))
        db.commit();db.close()
'''
assert needle in after;after=after.replace(needle,inject+needle,1)
needle='    if MODE in ("bad_exit_missing","bad_wait_missing"):'
inject='''    if MODE=="review_malformed_effect_preflight":
        plan=json.loads((out/"plan.json").read_text(encoding="utf-8"))
        unexpected=plan["eligibility"]=="ELIGIBLE_FOR_INDEPENDENT_REVIEW"
        record={"case":str(CASE),"mode":MODE,"preflight_eligibility":plan["eligibility"],"preflight_missing":plan.get("missing",[]),"preflight_safety":plan["preflight_safety"],"baseline":plan["baseline"],"additional_effect_body":{"payload":{"capability":"MODEL"}},"stop_grant_built":False,"native_signal_count":0,"source_safety_failure_reproduced":unexpected}
        write_json(CASE/"case-result.json",record)
        print(json.dumps(record,indent=2),flush=True)
        if unexpected:raise AssertionError("STOP-R4-F01: actual compiled preflight authorized malformed additional MODEL effect")
        sys.exit(0)
'''
assert needle in after;after=after.replace(needle,inject+needle,1)
dst.write_text(after,encoding='utf-8',newline='\n')
(E/'malformed-preflight-harness.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(src),tofile=str(dst))),encoding='utf-8')
record={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'copy':str(dst),'copy_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()}
(E/'malformed-preflight-harness-lineage.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(record)
