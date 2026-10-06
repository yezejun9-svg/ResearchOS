import pathlib,json,runpy,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[6];RAW=pathlib.Path(__file__).resolve().parent
namespace=runpy.run_path(str(ROOT/'tests/ui/w1303/check.py'),run_name='independent_dependency_freeze_review')
current=namespace['source_hashes']();old=json.loads((ROOT/'execution/v2.4/receipts/W13/W13-03/registered-20261005T193205Z-1fc0aadf/report.json').read_text(encoding='utf-8-sig'))['source_hashes'];checks=[]
def check(name,result):
 checks.append({'id':name,'pass':bool(result)})
 if not result:raise AssertionError(name)
required=['tests/ui/scenarios.py','tests/ui/workflow.py','runtime_tool_go','runtime_tool_node','runtime_tool_python','runtime_tool_electron']
for key in required:check('PRESENT_'+key,key in current)
namespace['prior_stage'].__globals__['RECEIPTS']=RAW/'cache-fixtures/case-001'
for stage in namespace['STAGE_DRIVER_FILES']:
 check(stage+'_MISSING_PREVIOUS_INPUTS_FORCE_MISS',namespace['prior_stage'](stage,current) is None)
 for key in required:
  changed=dict(current);changed[key]='changed-required-input'
  check(stage+'_PINS_'+key,namespace['stage_inputs'](stage,changed)!=namespace['stage_inputs'](stage,current))
result={'status':'PASS','checker_sha256':hashlib.sha256((ROOT/'tests/ui/w1303/check.py').read_bytes()).hexdigest(),'permission_driver_sha256':hashlib.sha256((ROOT/'tests/ui/w1303/permission.cjs').read_bytes()).hexdigest(),'current_input_count':len(current),'prior_input_count':len(old),'added_keys':sorted(set(current)-set(old)),'changed_keys':sorted(p for p,h in old.items() if current.get(p)!=h),'checks':checks,'check_count':len(checks),'production_changes_simulated_in_memory_only':True,'new_gui_runs':0,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(RAW/'cache-input-expansion-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','checks':len(checks),'current_input_count':len(current),'added_keys':len(result['added_keys'])}))
