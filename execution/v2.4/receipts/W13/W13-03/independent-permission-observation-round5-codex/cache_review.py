import ast,copy,datetime,hashlib,json,pathlib,runpy,sys
ROOT=pathlib.Path(__file__).resolve().parents[6]
RAW=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
CHECKER=ROOT/'tests/ui/w1303/check.py'
namespace=runpy.run_path(str(CHECKER),run_name='independent_stage_cache_review')
globals_=namespace['prior_stage'].__globals__
original=ROOT/'execution/v2.4/receipts/W13/W13-03/registered-20261005T193205Z-1fc0aadf/report.json'
old=json.loads(original.read_text(encoding='utf-8-sig')); old_hash=sha(original)
results=[]
def check(name,okay,detail=None):
 results.append({'id':name,'pass':bool(okay),'detail':detail})
 if not okay: raise AssertionError(name)
oldinputs=old['source_hashes']
for stage,drivers in namespace['STAGE_DRIVER_FILES'].items():
 for filename in drivers:
  key='tests/ui/w1303/'+filename; changed=dict(oldinputs);changed[key]='independent-change'
  check(stage+'_CURRENT_DRIVER_'+filename,namespace['stage_inputs'](stage,changed)!=namespace['stage_inputs'](stage,oldinputs))
 for key in ['apps/desktop/main/main.js','internal/domain/runtime_permission_windows.go','runtime_bundle','tests/ui/w1303/workspace_fixture/main_windows.go','execution/toolchains/locked.json','apps/web/package-lock.json']:
  check(stage+'_INPUT_PRESENT_'+key,key in oldinputs)
  changed=dict(oldinputs);changed[key]='independent-change'
  check(stage+'_REQUIRED_CHANGE_'+key,namespace['stage_inputs'](stage,changed)!=namespace['stage_inputs'](stage,oldinputs))
 changed=dict(oldinputs);changed['tests/ui/w1303/check.py']='independent-wrapper-change'
 check(stage+'_WRAPPER_EXCLUDED',namespace['stage_inputs'](stage,changed)==namespace['stage_inputs'](stage,oldinputs))
 for other,files in namespace['STAGE_DRIVER_FILES'].items():
  if other==stage:continue
  for filename in files:changed['tests/ui/w1303/'+filename]='independent-other-driver-change'
 check(stage+'_ONLY_OTHER_DRIVERS_EXCLUDED',namespace['stage_inputs'](stage,changed)==namespace['stage_inputs'](stage,oldinputs))
# Exercise real prior_stage against immutable copied report metadata and real existing evidence refs.
case_number=0
def prior_case(stage,fingerprint,transform=None):
 global case_number
 case_number+=1
 directory=RAW/'cache-fixtures'/f'case-{case_number:03d}'
 report=directory/'registered-baseline'/'report.json';report.parent.mkdir(parents=True)
 value=copy.deepcopy(old)
 if transform:transform(value)
 report.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
 globals_['RECEIPTS']=directory
 return namespace['prior_stage'](stage,fingerprint),report
for stage in ['matrix','preview','workspace','accessibility','transcript']:
 changed=dict(oldinputs);changed['tests/ui/w1303/check.py']='new-wrapper';changed['tests/ui/w1303/permission.cjs']='new-permission-driver'
 hit,report=prior_case(stage,changed)
 check(stage+'_MATCHING_OLD_STAGE_REUSED',hit is not None and hit['reused'] is True)
 check(stage+'_OLD_REPORT_LINK_HASH',hit['reuse_source_report']=={'path':report.relative_to(ROOT).as_posix(),'sha256':sha(report)})
 check(stage+'_IGNORED_CHANGES_TRUTHFUL',set(hit['ignored_source_changes'])=={'tests/ui/w1303/check.py','tests/ui/w1303/permission.cjs'})
 oldrow=next(r for r in old['stages'] if r['stage']==stage)
 check(stage+'_PRESERVES_CHECKS_AND_EVIDENCE',hit['checks']==oldrow['checks'] and hit['evidence']==oldrow['evidence'])
 for key in ['runtime_bundle','tests/ui/w1303/'+next(iter(namespace['STAGE_DRIVER_FILES'][stage])),'apps/desktop/main/main.js']:
  changedkey=dict(changed);changedkey[key]='required-input-change'
  miss,_=prior_case(stage,changedkey);check(stage+'_CACHE_REJECTS_'+key,miss is None)
 def corrupt_ref(report):next(r for r in report['stages'] if r['stage']==stage)['evidence'][0]['sha256']='0'*64
 miss,_=prior_case(stage,changed,corrupt_ref);check(stage+'_CACHE_REJECTS_MODIFIED_EVIDENCE',miss is None)
miss,_=prior_case('permission',oldinputs);check('OLD_FAILED_PERMISSION_NOT_REUSED',miss is None)
check('ORIGINAL_FULL_REPORT_UNMODIFIED',sha(original)==old_hash)
# Import dependencies are inspected as source only; no observation module is executed.
preview_tree=ast.parse((ROOT/'tests/ui/w1303/preview_run.py').read_text(encoding='utf-8-sig'))
preview_imports=[n.module for n in ast.walk(preview_tree) if isinstance(n,ast.ImportFrom)]
fingerprint=namespace['source_hashes']()
gap='scenarios' in preview_imports and 'tests/ui/scenarios.py' not in fingerprint
output={'status':'PASS_WITH_IDENTIFIED_INPUT_GAP' if gap else 'PASS','static_checks':results,'static_check_count':len(results),'checker_sha256':sha(CHECKER),'permission_driver_sha256':sha(ROOT/'tests/ui/w1303/permission.cjs'),'source_fingerprint':fingerprint,'input_gaps':[{'path':'tests/ui/scenarios.py','reason':'preview_run imports and executes pdf_document but source_hashes omits the file'}] if gap else [],'prior_report':{'path':original.relative_to(ROOT).as_posix(),'sha256':old_hash},'new_gui_runs':0,'new_workspace_probes':0,'provider_calls':0,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(RAW/'cache-test-result.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':output['status'],'static_checks':len(results),'input_gaps':output['input_gaps']}))
