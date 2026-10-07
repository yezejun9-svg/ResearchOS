from pathlib import Path
import importlib.util,hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
sys.path.insert(0,str(OUT/'SYNTHETIC_HELPER_SOURCE'))
import register as r
os.environ['GIT_DIR']=str(OUT/'NONEXISTENT_GIT_DIR')
os.environ['GIT_WORK_TREE']=str(OUT/'NONEXISTENT_WORK_TREE')
os.environ['GIT_REPLACE_REF_BASE']='refs/REVIEW_POISON/'
os.environ['GIT_CONFIG_COUNT']='1';os.environ['GIT_CONFIG_KEY_0']='core.worktree';os.environ['GIT_CONFIG_VALUE_0']='NONEXISTENT'
os.chdir(OUT)
actualrun=r.subprocess.run;calls=[]
def checkedrun(argv,**kw):
 if argv[0]=='git':
  r.need('--no-replace-objects' in argv and kw['cwd']==ROOT.anchor,'INDEPENDENT_GIT_CALL','replace/cwd')
  r.need(not any(k.upper().startswith('GIT_') for k in kw['env']),'INDEPENDENT_GIT_ENV','poison escaped')
 result=actualrun(argv,**kw)
 calls.append({'argv':argv,'cwd':kw.get('cwd'),'exit_code':result.returncode,'stdout_sha256':r.sha(result.stdout),'stderr_sha256':r.sha(result.stderr),'git_variables_in_child':[k for k in kw.get('env',{}) if k.upper().startswith('GIT_')]})
 return result
r.subprocess.run=checkedrun
class MetadataOnlyAudit(r.Audit):
 def bytes(self,ref,historical=False):
  normalized=r.normalized_ref(self.repo,ref)
  r.need(normalized is None or normalized['path']!=r.STATE,'INDEPENDENT_CURRENT_STATE_FORBIDDEN',ref)
  r.need(Path(ref['path']).suffix.lower() not in {'.db','.sqlite','.sqlite3'},'INDEPENDENT_PRIVATE_DB_FORBIDDEN',ref)
  return super().bytes(ref,historical)
audit=MetadataOnlyAudit(ROOT)
assignment=audit.doc({'path':r.SCOPE_DIR+'actor_assignment.json','sha256':r.ASSIGNMENT_SHA})
graph=r.historical(audit,audit.doc(assignment['old_owner_ref']))
r.need(len(audit.historical_observations)==2 and r.STATE not in audit.observed,'EXACT_TWO_OBSERVATIONS',audit.historical_observations)
r.save(OUT/'independent_historical_graph.json',graph)
r.save(OUT/'historical_readonly_audit.json',{'schema':'researchos.w04.independent-readonly-historical-check.v1','scope':'READONLY_METADATA_NOT_PREPARE','at':datetime.now(timezone.utc).isoformat(),'status':'PASS','helper_sha256':r.sha(Path(r.__file__).read_bytes()),'historical_observations':audit.historical_observations,'observed_hashes':audit.observed,'drifts':audit.drifts,'actual_git_calls':calls,'parent_git_environment_poisoned':True,'current_state_read':False,'private_db_read':False,'actual_prepare_apply_recover':False,'graph_ref':r.reference(ROOT,OUT/'independent_historical_graph.json')})
print(json.dumps({'status':'PASS','observed_files':len(audit.observed),'historical_observations':len(audit.historical_observations),'actual_git_calls':len(calls),'drifts':len(audit.drifts),'audit_sha256':r.sha((OUT/'historical_readonly_audit.json').read_bytes())}))
