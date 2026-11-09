from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];MAIN=Path('D:/作品集/ResearchOS/research-os')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audits=[]
for version in (14,20):
    lane=HERE/('schema'+str(version));report=read(lane/'report.json');provenance=read(lane/'snapshot-provenance.json')
    assert report['status']=='PASS_HISTORICAL_CONTRACT_ONLY' and report['source_vector_equal'] and report['dependency_vector_equal']
    snapshot=ROOT/('.local/historical-fixtures-lanes/schema'+str(version)+'/source')
    actual={p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file()};expected={p['path'] for p in provenance['files']}
    assert actual==expected
    assert all(sha(snapshot/f['path'])==f['sha256'] for f in provenance['files'])
    origin=Path(provenance['origin']);origin_changed=[f['path'] for f in provenance['files'] if (origin/f['path']).is_file() and sha(origin/f['path'])!=f['sha256']]
    assert not origin_changed
    commands=[]
    for d in sorted(lane.iterdir()):
        if d.is_dir() and (d/'command.json').exists():
            r=read(d/'result.json');assert r['exit_code']==0
            for key in ('stdout','stderr'):assert sha(Path(r[key]['path']))==r[key]['sha256']
            commands.append({'command':ref(d/'command.json'),'result':ref(d/'result.json')})
    build_matches=None
    if version==20:
        proof=read(lane/'new-public-evidence/public-control-native-proof.json');binary=Path(report['control_reference_binary']['path'])
        build_matches=proof['stable_hash']==proof['candidate_hash']=='sha256:'+sha(binary)
        assert build_matches
    audits.append({'schema':version,'test_pass_count':len(report['tests']['pass']),'test_fail_count':0,'test_skip_count':0,'original_assertion_count':len(report['assertions']),'all_original_assertions_pass':all(a['status']=='PASS' for a in report['assertions']),'source_file_count':len(actual),'compiled_dependency_count':report['actual_dependency_count'],'source_and_dependencies_unchanged':True,'post_execution_extras':[],'preserved_origin_changed_files':origin_changed,'commands':commands,'test_binary':report['test_binary'],'new_control_binary':report['control_reference_binary'],'actual_fresh_control_proof_matches_reference':build_matches,'qualification':'HISTORICAL_CONTRACT_ONLY_NOT_CURRENT22','report':ref(lane/'report.json')})
registration=MAIN/'execution/v2.4/receipts/W05/W05-99/integration_codex/historical_fixture_root_registration.json'
review=MAIN/'execution/v2.4/receipts/W05/W05-99/resume_review_codex/historical_fixture_scope_63c2e06e-276a-44d0-8baf-4c9f2bd45ef8/review.json'
final={'classification':'AUTHORIZED_HISTORICAL_LANES_NOT_CURRENT22_OR_FORMAL_ACCEPTANCE','status':'PASS_SCOPED_HISTORICAL_CONTRACTS','source_candidate_commit':'3dffadd250cb4e5c312baf87e9136f7cfa8ba40a','selector_final_audit':ref(HERE/'selector-final-audit.json'),'registration_sha256':sha(registration),'independent_scope_sha256':sha(review),'lanes':audits,'reporting_corrections':[{'artifact':'selector-report.json','issue':'Original assertions parser expected W17_ASSERTION instead of W17_UPGRADE_ASSERTION; initial empty list retained. selector-final-audit.json verifies actual five assertion objects from unchanged raw.'},{'artifact':'schema20/report.json','issue':'Reference hash comparator used nonexistent baseline_hash; true field is stable_hash. Initial false field retained. Both actual stable_hash and candidate_hash equal SHA92b788bcabdd06f23613890f8f69f8f6c086bbf132e335538b5c86450fdd0b1b of independently rebuilt same-source control. No product run repeated.'}],'product_execution_failures':[],'expected_selector_negative_exits':[{'run':'missing-artifact','exit':1},{'run':'wrong-hash-artifact','exit':1}],'old4276_image':'NOT_LOCATED_NOT_USED','preserved203fe_image':'PROVENANCE_ONLY_NOT_INJECTED','provider_or_model_calls':0,'old_authority_or_private_holdout_opened':False,'current22_qualification':False,'Q10_closed':False,'four_original_current_main_failures_retained':True,'formal_acceptance_delta':0,'parent_acceptance_delta':0,'counter_reset':False}
write(HERE/'historical-final-audit.json',final)
(HERE/'README.md').write_text('''# Authorized historical fixture evidence\n\nMinimal source candidate `3dffadd250cb4e5c312baf87e9136f7cfa8ba40a` changes only original `backup_upgrade_test.go:975–981`. Both protected exterior byte hashes match. Strict opt-in uses the pinned schema14 artifact, verifies/stages its bytes, verifies the actual locked Go and exact buildinfo, and preserves the no-env build branch.\n\nCurrent upgrade CLI with fixed historical14 target: **1 test PASS / 0 skip**, all **5 original assertions PASS**. Missing artifact and wrong hash each produce the expected exit1/refusal before execution.3706 compiled/contract inputs remain unchanged.\n\nSeparate disposable historical lanes:\n\n* schema14 original ActiveRecovery: **1 PASS / 0 skip**, **7 original assertions PASS**,226 source files and3394 compilation dependencies unchanged.\n* schema20 original ReplayNative and BusinessNoGain: **2 PASS / 0 skip**, **21 original assertions PASS**,355 source files and3573 compilation dependencies unchanged. All206 recorded production inputs match; every extra source/test/helper/embed has explicit historical Git provenance.\n\nTest executables are hash-pinned. The real fresh control built inside original tests matches a separately rebuilt same-source image: `92b788bcabdd06f23613890f8f69f8f6c086bbf132e335538b5c86450fdd0b1b`. Old203fe image is provenance only; absent4276 image remains absent. Original public fixtures and canary are newly generated; no old authority/private store is opened.\n\n`historical-final-audit.json` is the consolidated audit. Two reporting-only parser mistakes are retained and explicitly corrected there using unchanged raw: initial W17 assertion-prefix parsing; baseline_hash versus actual stable_hash key. No product test was rerun to mask those mistakes.\n\nThese results prove historical contracts and the narrow current upgrade CLI targeting historical14. The four original current-main failures remain in their original receipts. Q10, current22 source qualification, LIVE/provider and formal/parent acceptance are not closed by this evidence.\n''',encoding='utf-8')
write(HERE/'historical-receipt-manifest.json',{'files':[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='historical-receipt-manifest.json']})
print(json.dumps({'final_audit_sha256':sha(HERE/'historical-final-audit.json'),'manifest_sha256':sha(HERE/'historical-receipt-manifest.json'),'lanes':[(a['schema'],a['test_pass_count'],a['original_assertion_count']) for a in audits]},indent=2))
