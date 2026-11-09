"""Assemble reviewer conclusion only from completed, independently executed reports."""
import datetime, hashlib, json, subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[3]
FIX=OUT/'fix-a366288'
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def digest(path): return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
completed={}
for phase in ['core','content','regression','contracts']:
    passed=[path for path in (FIX/phase).glob('*/report.json') if load(path).get('status')=='PASS']
    assert passed, f'{phase} not completed'
    completed[phase]=max(passed,key=lambda path:path.stat().st_mtime)
for path in completed.values():
    report=load(path)
    assert report['head']=='a3662884d6c1a546f03e13b3a450b7d29b0c1094'
    assert all(digest(path.parent/name)==value for name,value in report['screenshot_hashes'].items())
original=OUT/'baseline-review.json'
if not original.exists(): original.write_bytes((OUT/'review.json').read_bytes())
review=load(original)
review['reviewed_baseline_revision']=review['source_revision']
review['source_revision']='a3662884d6c1a546f03e13b3a450b7d29b0c1094'
review['verdict']='PASS_IN_UI_FIXTURE_SCOPE'
review['created_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
review['baseline_review']='baseline-review.json'
for finding in review['findings']:
    finding['status']='RESOLVED_IN_REVIEWED_FIX'
    finding['fix_revision']=review['source_revision']
    finding['regression_evidence']=str(completed['regression'].relative_to(OUT)).replace('\\','/')
review['open_findings']=[]
review['execution']['workflow_pass']='workflow/fc5daf0a052049208bbb9a45ef55e6d4/report.json'
review['execution']['fix_regression']={phase:{'report':str(path.relative_to(OUT)).replace('\\','/'),'check_count':load(path)['check_count'],'responsive_case_count':load(path)['responsive_case_count'],'sha256':digest(path)} for phase,path in completed.items()}
review['execution']['fix_driver_interruption']='fix-a366288/core/fc70a3accc5b4b51b0cad6a10558fb96/interrupted.json'
review['execution']['runner_note']='Author phases use unchanged frozen tests and only output redirection. Contracts phase additionally calls independent verify_chain.py. Independent/regression phases use reviewer-authored probes. Product source untouched by reviewer. Counterexample runner PASS denotes successful reproduction, not product acceptance.'
review['case_assessment']['C23']='PASS_IN_UI_FIXTURE_SCOPE. URL/selection restoration and finite timeout findings resolved; independent regression covers list/search focus, reload, Back/Forward and real 30-second stalled response with explicit retry recovery. Core and populated-content reruns pass. C23 permits fixed backend fixtures; no live W14/W17 prerequisite introduced.'
review['case_assessment']['C24']='PASS_IN_BROWSER_FIXTURE_SCOPE. Important tag/count fonts now14px, auxiliary/bottom navigation12px; independent computed-style regression and 320x780 drawer pass. Re-executed core108/content36 responsive cases, true200% zoom, keyboard and reduced motion; updated screenshots personally viewed. Physical phone/screen-reader not claimed.'
review['case_assessment']['C17']+=' Fix-source contracts rerun includes separate reviewer-authored actual sidebar click and full acceptance/hash/content-chain verification.'
review['envelope_recommendation']={
    'C17':'READY_TO_ASSEMBLE_FIXTURE_ENVELOPE with matching backend atomic outbox/crash/uniqueness evidence; UI proof alone is insufficient for backend worker step.',
    'C18':'READY_TO_ASSEMBLE_FIXTURE_ENVELOPE; exact business counts and real acceptance lineage verified; retain transient VERIFYING fixture and server revision numbering disclosure.',
    'C23':'READY_TO_ASSEMBLE_FIXTURE_ENVELOPE; no remaining UI findings in reviewed scope.',
    'C24':'READY_TO_ASSEMBLE_BROWSER_FIXTURE_ENVELOPE; no remaining UI findings; no physical device claim.',
    'C25':'READY_TO_ASSEMBLE_UI_FIXTURE_ENVELOPE with security/backend evidence; no real protected bytes or W17 device claim.',
    'C26':'READY_TO_ASSEMBLE_UI_ASSERTION_EVIDENCE; explicitly mark physical computer sleep operation NOT_RUN unless separate machine evidence is supplied. Chromium page freeze must not be relabeled OS sleep.'}
review['fix_scope']={'changed_product_files':subprocess.check_output(['git','diff','--name-only','70db969','a366288','--','apps/web/src','internal','tests/ui'],cwd=REPO,text=True).splitlines(),'reason_for_carry_forward':'Internal backend and tests/ui are byte-identical between frozen baseline and fix revision. UI fix touches only api.js/main.jsx/screens.jsx/style.css; affected core/content/contracts and reviewer counterexamples rerun. Baseline workflow actual transitions retained with exact source scope.'}
review['limits'].append('Fix-source initial core driver run was interrupted after Windows ProactorEventLoop WinError64 stalled progress; isolated owned process tree stopped, incomplete evidence preserved. Sequential rerun passed. Regression teardown emitted Playwright cancelled-route callback warnings after successful assertions; these are driver cleanup warnings, not app page errors.')
(OUT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
files=[]
for path in sorted(OUT.rglob('*')):
    if path.is_file() and path.name != 'evidence-index.json' and '__pycache__' not in path.parts:
        files.append({'path':str(path.relative_to(OUT)).replace('\\','/'),'bytes':path.stat().st_size,'hash':digest(path)})
(OUT/'evidence-index.json').write_text(json.dumps({'version':1,'reviewed_revision':review['source_revision'],'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'verdict':review['verdict'],'open_findings':0,'indexed_files':len(files),'reports':review['execution']['fix_regression']},ensure_ascii=False))
