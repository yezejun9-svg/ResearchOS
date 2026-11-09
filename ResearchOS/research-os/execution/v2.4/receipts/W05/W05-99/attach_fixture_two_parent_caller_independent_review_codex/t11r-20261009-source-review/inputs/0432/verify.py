import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,re,ast
from collections import Counter
Q=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
C=R/'execution/v2.4/receipts/W05/W05-99/remaining_full_failure_cause_review_codex/8c83a215358ce0e859da44f08b8a69d3'
F=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/current-composition-full-domain-root-0d2a82e73b754a5f/full-domain-and-native-authority-offline.stdout.raw'
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
construction=json.loads((Q/'construction.json').read_text(encoding='utf-8'))
for row in construction['member_refs']:
 if pin(Path(row['path']))!=row:raise RuntimeError('candidate Source drift')
manifest=json.loads((C/'manifest.json').read_text(encoding='utf-8'))
cause_refs=[]
for key in ['report_ref','report_md_ref','source_pins_ref']:
 ref=manifest[key]
 p=Path(ref['path']);actual=pin(p)
 if actual['sha256']!=ref['sha256'] or actual['bytes']!=ref['bytes']:raise RuntimeError('cause manifest input drift')
 cause_refs.append(actual)
events=[]
for number,line in enumerate(F.read_text(encoding='utf-8').splitlines(),1):
 event=json.loads(line)
 case=event.get('Test','')
 if (case.startswith('TestClientTranscriptIndexUpgradesExistingSessionTable') or case=='TestW09LegacyRootMigrationRevokesUnidentifiedRoot') and (event.get('Action')=='fail' or any(s in event.get('Output','') for s in ['MIGRATION_PREBACKUP_REQUIRED','MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION'])):
  events.append({'raw_line':number,'event':event})
util=R/'execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931/construct.py'
tree=ast.parse(util.read_text(encoding='utf-8'))
env={'re':re,'Counter':Counter}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tokens','close_index','call_nodes','assertion_if_nodes','balanced']]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(util),'exec'),env)
def bodies(text):
 ts=env['tokens'](text);out={}
 for i,(tok,a,b) in enumerate(ts):
  if tok=='func' and i+1<len(ts) and ts[i+1][0].startswith('Test'):
   name=ts[i+1][0]
   opening=next(j for j in range(i+2,len(ts)) if ts[j][0]=='{')
   end=env['close_index'](ts,opening,'{','}')
   out[name]=text[a:ts[end][2]]
 return out
checks=[]
changed={'TestClientTranscriptIndexUpgradesExistingSessionTable','TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction','TestW09LegacyRootMigrationRevokesUnidentifiedRoot'}
for item in construction['static_checks']:
 if 'base_ref' not in item:continue
 name=item['name']
 before=(T/'internal/domain'/name).read_text(encoding='utf-8')
 after=(Q/'candidate-root/internal/domain'/name).read_text(encoding='utf-8')
 old,new=bodies(before),bodies(after)
 unchanged=[n for n in old if n not in changed and old[n]==new[n]]
 required=[n for n in old if n not in changed]
 if unchanged!=required:raise RuntimeError('unrelated original Test changed')
 bt,at=env['tokens'](before),env['tokens'](after)
 checks.append({'name':name,'unrelated_original_Test_bodies_byte_equal':unchanged,'original_assertion_call_count':len(env['call_nodes'](bt)),'candidate_assertion_call_count':len(env['call_nodes'](at)),'original_assertion_or_error_if_count':len(env['assertion_if_nodes'](bt)),'candidate_assertion_or_error_if_count':len(env['assertion_if_nodes'](at)),'original_Test_count':len(old),'candidate_Test_count':len(new)})
predicates=['if project != f.project || revision != 7 || epoch != 3 || watermark != 19 || writer != "transcript-upgrade" || upstream != "existing-session" || transcript != nil {','if identity != "" || revoked != 1 || revision != 2 {']
for text in predicates:
 both=''.join((T/'internal/domain'/n).read_text(encoding='utf-8') for n in ['client_session_bootstrap_test.go','retrieval_test.go'])
 revised=''.join((Q/'candidate-root/internal/domain'/n).read_text(encoding='utf-8') for n in ['client_session_bootstrap_test.go','retrieval_test.go'])
 if text not in both or text not in revised:raise RuntimeError('business preservation predicate differs')
source_files=[T/'internal/domain/store.go',T/'internal/domain/backup_migration.go',T/'internal/domain/client_session_fence.go',T/'internal/domain/v24_sessions.go',T/'internal/store/sqlite.go']
resources=json.loads((Q/'migration-resources.json').read_text(encoding='utf-8'))
pins=[pin(p) for p in source_files]+[r['actual_source_ref'] for r in resources['migration_sources']]+[pin(C/'manifest.json'),*cause_refs,pin(F)]
out={'authority':'NONE','formal_acceptance':False,'original_FULL_raw_ref':pin(F),'original_failed_nodes_preserved':events,'static_checks':checks,'original_business_predicates_preserved':predicates,'source_contract_refs':pins,'candidate_Source_refs':construction['member_refs'],'no_Go_AST_compiler_native_SQL_model_execution':True,'mechanical_failures_this_branch':0,'prior_826_failure_not_reset':True}
with (Q/'verification.json').open('x',encoding='utf-8') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':checks,'original_failure_events':events,'mechanical_failures_this_branch':0,'Source_changed_production':0},ensure_ascii=False))
