from pathlib import Path
import json,hashlib,sqlite3,datetime
O=Path(__file__).resolve().parent;R=O.parents[6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size}
def save(n,x):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
result=json.loads((O/'result.json').read_text(encoding='utf-8'));assert result['stable'];v=json.loads((O/'test_inputs.before.json').read_text(encoding='utf-8'));current=json.loads((O/'inputs.current.json').read_text(encoding='utf-8'));assert v==current
for cohort in ['domain','cli','api','host']:assert v==json.loads((O/('inputs.after-'+cohort+'.json')).read_text(encoding='utf-8'))
programs=json.loads((O/'programs.freeze.json').read_text(encoding='utf-8'));assert all(sha(Path(x['path']))==x['sha256'] for x in programs)
passes={};refs=[]
for cohort in ['domain','cli','api','host']:
 p=O/('test-'+cohort+'.stdout.raw');inv=json.loads((O/('test-'+cohort+'.invocation.json')).read_text(encoding='utf-8'));assert inv['exit']==0
 for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  x=json.loads(line)
  if x.get('Test') and x.get('Action')=='pass':passes[cohort+':'+x['Test']]={'raw':ref(p),'line':i}
 refs.extend([ref(O/('test-'+cohort+'.invocation.json')),ref(p),ref(O/('test-'+cohort+'.stderr.raw'))])
assert len(passes)==444;save('actual_test_coverage.json',{'pass':444,'top_pass':123,'fail':0,'skip':0,'test_locators':passes})
dbs=[]
for p in sorted((O/'actual-fixtures').rglob('*.sqlite')):
 b=sha(p);db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True);versions=[x[0] for x in db.execute('select version from schema_migrations order by version')];tables={x[0] for x in db.execute("select name from sqlite_master where type='table'")};counts={t:db.execute('select count(*) from "'+t+'"').fetchone()[0] for t in ['host_model_configurations','host_model_config_heads','client_command_identities','client_sessions','client_command_queue','client_control_receipts','idempotency','resource_effects'] if t in tables};integrity=db.execute('pragma integrity_check').fetchone()[0];db.close();assert sha(p)==b;dbs.append({'file':ref(p),'versions':versions,'row_counts':counts,'integrity':integrity,'immutable_unchanged':True})
save('closed_public_sqlite_audit.json',{'db_count':len(dbs),'files':dbs,'read_mode':'mode=ro&immutable=1','actual_user_private_db_reads':0})
old=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec/source_review.json';assert sha(old)=='8c58e9d9986da7103cb729a4e2b5fa54412b78319eda8d70a4e52c266c317ad3';old_review=json.loads(old.read_text(encoding='utf-8'));gates=old_review['gates']
for g in gates:
 if g['id']=='G12':g['verdict']='PASS_CURRENT_MAIN_COMPOSITION';g['finding']='Main1b3cda2 exact16 plus existing L02/stream current inputs:191 domain+234CLI+13API+6Host=444 PASS,123 top,0FAIL/0SKIP;42555 source/tool inputs+6 new current exe=42561 unchanged at every stage/current. No replay or skip.'
 if g['id']=='G01':g['finding']+=' Current Main apps/control and ops/backup were separately built and pinned; exact191 native upgrade invoked current Main ops/backup upgrade-local, not an obsolete binary. apps/control is a separate Host entrypoint with no upgrade-local verb.'
 if g['id']=='G09':g['finding']+=' Current Main frozen22 writer-lock controls passed in this run.'
 for cohort,pattern in [('domain','TestConfiguration'),('domain','TestBackupHostConfiguration'),('host','TestW1802')]:
  if g['id'] in ['G01','G03','G05','G06','G07','G09','G12']:
   g.setdefault('current_raw_refs',[]).append(ref(O/('test-'+cohort+'.stdout.raw')))
def deletions(path):return sorted(x for x in path.read_text(encoding='utf-8').splitlines() if x.startswith(' D '))
a=deletions(O/'status-before.stdout.raw');z=deletions(O/'status-after.stdout.raw');assert a==z and len(a)==11
save('tracked_deletions_audit.json',{'before':a,'after':z,'preserved':True,'canonical_note':'Reviewer did not modify canonical state; Root concurrent metadata registration is not claimed globally immutable.'})
diag=json.loads((O/'preparation_diagnostics.json').read_text(encoding='utf-8'));save('failure_origins.json',{'origins':diag['origins'],'product_test_failed_invocations':0,'skipped_tests':0,'native_raw_limitation':diag['limitations'],'models_paid':0})
review={'schema':'researchos.main-configuration.independent-composition-review.v1','decision':'MAIN_CONFIGURATION_COMPOSITION_VERIFIED_WITH_DECLARED_OPEN_GATES','reviewer':'codex:/root/w05_merge_review','main_head':'1b3cda2ee974916f864b9a0af988076d01ca65bd','scope':ref(O/'scope.original.json'),'prior_independent_source_review':ref(old),'source_delta':ref(O/'source-delta.audit.json'),'test_result':ref(O/'result.json'),'counts':{'pass':444,'top_pass':123,'fail':0,'skip':0},'cohorts':result['tests'],'actual_test_refs':refs,'source_inputs':42555,'test_inputs':42561,'source_current_vectors':[ref(O/n) for n in ['inputs.before.json','inputs.after_compile.json','test_inputs.before.json','inputs.after-domain.json','inputs.after-cli.json','inputs.after-api.json','inputs.after-host.json','inputs.current.json','inventory.before.json','inventory.after.json']],'programs':programs,'sdk':{'original_files_verified':5083,'bundle':result['bundle_sha256'],'rebuilt_this_review':False,'actual_local_evidence':ref(O/'cli_local_sdk_evidence.json'),'passed_sdk_exercising_leaf_cases':13,'causal_flush_witnesses':65,'one_logged_queue_fixture_actual_http_calls':4,'global_loopback_http_total':'not independently instrumented; do not derive from count of MODEL state rows'},'public_db_audit':ref(O/'closed_public_sqlite_audit.json'),'protected_original_deletions':ref(O/'tracked_deletions_audit.json'),'gates':gates,'open':['Historical14 ActiveRecovery remains inherited OPEN; no rerun/reclassification here.','F08 CANCEL finalization/schema24 remains OPEN.','Public host.configure/session runtime binding and provider9/LIVE qualification remain OPEN.','Source composition and local fixture verification do not accept W05/A04/42 or any parent/formal gate.','Current native source/program identity established by external actual build inputs and hash; no self-attestation protocol invented.'],'external_provider_calls':0,'provider9_held_runs':0,'paid':0,'actual_user_private_data_reads':0,'product_source_changes':0,'canonical_mutations_by_reviewer':0,'formal_increment':0,'failure_origins':ref(O/'failure_origins.json'),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save('review.json',review)
files=[ref(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['manifest.json','handoff.json']];save('manifest.json',{'files':files,'count':len(files),'excludes':['manifest.json','handoff.json']});save('handoff.json',{'decision':review['decision'],'review':ref(O/'review.json'),'manifest':ref(O/'manifest.json'),'failure_origins':ref(O/'failure_origins.json'),'head':review['main_head'],'counts':review['counts'],'formal_increment':0});print(json.dumps({'review':ref(O/'review.json'),'manifest':ref(O/'manifest.json'),'handoff':ref(O/'handoff.json'),'failure':ref(O/'failure_origins.json'),'closed_db':len(dbs)},ensure_ascii=False))
