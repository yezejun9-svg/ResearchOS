from pathlib import Path
import json,hashlib,subprocess,sys
sys.stdout.reconfigure(encoding='utf-8');R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-host-configuration-upgrade';O=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes())}
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
p='evaluation/development/jev-v2/dataset.json';c='c82f73cc6699b564f1357472e2859b90cafe6b0a';b=subprocess.check_output(['git','--no-replace-objects','-C',str(W),'show',c+':'+p]);oid=subprocess.check_output(['git','--no-replace-objects','-C',str(W),'rev-parse',c+':'+p]).decode().strip()
counts={'pass':0,'fail':0,'skip':0};fail=[]
for line in (O/'test.stdout.raw').read_text(encoding='utf-8').splitlines():
 x=json.loads(line)
 if x.get('Test') and x.get('Action') in counts:
  counts[x['Action']]+=1
  if x['Action']=='fail':fail.append(x['Test'])
before=json.loads((O/'inputs.before.json').read_text(encoding='utf-8'));after=[{'path':x['path'],'sha256':sha(Path(x['path']).read_bytes()),'bytes':Path(x['path']).stat().st_size} for x in before];save('inputs.after_failed_test.json',after)
leaf=[x for x in fail if not any(y.startswith(x+'/') for y in fail)]
origin={'id':'configuration-independent-9673a59f-test-prerequisite-development-fixture','invocation':ref(O/'test.invocation.json'),'stdout':ref(O/'test.stdout.raw'),'stderr':ref(O/'test.stderr.raw'),'exit':1,'counts':counts,'failed_leaves':leaf,'cause':'Independent checkout omitted public development dataset needed by upgradeSeedQualifications; no product assertion failure reached in these five leaves; no automatic rerun.','already_imported':False}
save('failure_origins.prerequisite.json',{'origins':[origin]})
save('development_fixture_recovery_request.json',{'candidate':c,'resource':{'path':p,'git_blob_oid':oid,'sha256':sha(b),'bytes':len(b)},'purpose':'backup_upgrade_test.go:312 upgradeSeedQualifications uploads public development bytes into ephemeral project fixture; synthetic upgradeFake qualificationSummary, no real holdout data read. Used by writer-lock and protected-continuity/fault tests.','original_closure':ref(O/'inputs.before.json'),'after_failed_test':ref(O/'inputs.after_failed_test.json'),'input_count':len(before),'zero_drift':before==after,'test_binary':ref(O/'domain.test.exe'),'origin':origin,'requested_action':'After Root exact registration, export only this Git blob into own checkout; freeze augmented vector, rerun only five failed leaves with unchanged executable/source; preserve original failed invocation.','models':0,'resource_restored':False})
print(json.dumps({'request':ref(O/'development_fixture_recovery_request.json'),'failure':ref(O/'failure_origins.prerequisite.json'),'resource':{'path':p,'oid':oid,'sha256':sha(b),'bytes':len(b)},'counts':counts,'leaves':leaf,'stable':before==after},ensure_ascii=False))
