"""Freeze one explicitly supplied four-stage independent negative review."""
import argparse,datetime as dt,hashlib,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':'sha256:'+hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=True,indent=2);f.write('\n')
a=argparse.ArgumentParser();a.add_argument('--case-id',required=True)
for stage in ['release','grant','terminal','closure']:a.add_argument('--'+stage+'-report',required=True)
args=a.parse_args();assert re.fullmatch('[A-Za-z0-9_-]+',args.case_id);E=BASE/args.case_id;assert E.is_dir()
reports={};pins={};config_sha=None
for stage in ['release','grant','terminal','closure']:
 path=Path(getattr(args,stage+'_report'));assert path.is_relative_to(E);v=read(path)
 assert v['state']=='PASS' and v['case_id']==args.case_id and v['stage']==stage and v['inner_native_job_id_independently_observed'] is False and v['formal_increment']==0
 if config_sha is None:config_sha=v['config_ref']['sha256']
 assert config_sha==v['config_ref']['sha256'];source=v['reviewer_script_ref'];actual=ref(source['path']);assert actual['sha256']==source['sha256'] and actual['bytes']==source['bytes']
 reports[stage]=v;pins[stage]=ref(path)
assert reports['closure']['outer_test_exit']==0 and reports['terminal']['whole_original_rows_and_schema_unchanged']
assert reports['closure']['terminal_report_ref']==pins['terminal'] and reports['grant']['baseline_report_ref']==pins['release'] and reports['terminal']['baseline_report_ref']==pins['release']
attempts=[]
for p in sorted(E.glob('*/report.json')):
 v=read(p);attempts.append({'ref':ref(p),'stage':v['stage'],'state':v['state'],'error_type':v.get('error_type')})
save(E/'FINAL-report.json',{'schema':'researchos.independent-native25-negative-final/1','state':'ACCEPTED_ISOLATED_NATIVE_NEGATIVE_ONLY','case':reports['terminal']['case'],'case_id':args.case_id,'config_sha256':config_sha,'stage_report_refs':pins,'fresh_original_schema24_rows_and_schema_unchanged':True,'actual_rejection':reports['terminal']['actual_rejection'],'actual_native_exit':reports['terminal']['actual_native_exit'],'actual_native_pid':reports['terminal']['actual_native_pid'],'outer_test_exit':0,'source_guards_closed':reports['closure']['source_guards_closed'],'temp_public_files_retained':reports['closure']['retained_temp_public_files_verified'],'inner_native_job_id_independently_observed':False,'reviewer_attempts':attempts,'reviewer_failed_attempt_count':sum(v['state']!='PASS' for v in attempts),'formal_increment':0,'formal_accepted':'0/42','open_parents':22,'native_branch_complete':False,'root_authority_actions':0,'private_resource_reads':0,'product_database_reads':0,'at':dt.datetime.now(dt.timezone.utc).isoformat(),'boundary':'This one named isolated synthetic negative case only. Other negatives, formal acceptance, inner native Job identity observation and parent completion are not derived.'})
save(E/'manifest.json',{'schema':'researchos.independent-public-evidence-manifest/1','files':[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest.json']})
print(json.dumps({'report_ref':ref(E/'FINAL-report.json'),'manifest_ref':ref(E/'manifest.json')}))
