import sys
sys.dont_write_bytecode = True
import hashlib, json, re, difflib
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
T5 = R / '.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
Q = Path(__file__).resolve().parent
C = Q / 'candidate-root'
expected = {
 'internal/domain/runtime_permission_windows_test.go': ('3f6d2131e55d197c056f7e495606d5e8e892bd1a044eaf558f3cd6fee356a6ce',18547),
 'internal/domain/runtime_tool_integration_windows_test.go': ('1fa85aa7c4d690ad180e89e459714854da8b858b1f85f06a25c032f7405cce9c',11954),
 'internal/domain/runtime_session_events_windows_test.go': ('e29b87008af1ff3908f2c1f6f1b389ab7ce72d28b94f216163a3a5ae3d5143da',24903),
 'internal/domain/client_protocol_goal_test.go': ('3aebfa43aa5131a1c809ec3d64d800351b87f30155be0428f545799520ae319f',14343),
}
tops = {
 'internal/domain/runtime_permission_windows_test.go': [
  'TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite',
  'TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite',
  'TestRuntimePermissionDecisionWaitsForAnotherRequiredResource',
 ],
 'internal/domain/runtime_tool_integration_windows_test.go': [
  'TestRuntimeMuSessionToolAndIndependentAcceptance',
  'TestRuntimeMuToolRefusalAllowsNextTurn',
 ],
 'internal/domain/runtime_session_events_windows_test.go': [
  'TestW05RuntimeEventBrokerBeforeIOAndRollback',
 ],
}
scope = [
 ('TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite/ALLOW_ONCE','internal/domain/runtime_permission_windows_test.go','ALLOW_ONCE original frozen write only once; provider/physical IO/permission/replay/state assertions remain'),
 ('TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite/DENY','internal/domain/runtime_permission_windows_test.go','DENY no physical write and original ResourceRequest/Run/Task assertions remain'),
 ('TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite','internal/domain/runtime_permission_windows_test.go','expired permission no physical write; original timeout/settlement assertions remain'),
 ('TestRuntimePermissionDecisionWaitsForAnotherRequiredResource','internal/domain/runtime_permission_windows_test.go','resolved permission cannot bypass another required resource; original blocked/no-write assertions remain'),
 ('TestRuntimeMuSessionToolAndIndependentAcceptance','internal/domain/runtime_tool_integration_windows_test.go','MODEL/TOOL/MODEL, actual file witness, independent acceptance, recovery, call counts and single assistant projection remain'),
 ('TestRuntimeMuToolRefusalAllowsNextTurn','internal/domain/runtime_tool_integration_windows_test.go','FAILED Task/Run, NOT_APPLIED, no automatic retry and next explicit turn assertions remain'),
 ('TestW05RuntimeEventBrokerBeforeIOAndRollback/rollback=false','internal/domain/runtime_session_events_windows_test.go','committed TOOL_STARTED before IO, one actual TOOL_RESULT and projection replay assertions remain'),
 ('TestW05RuntimeEventBrokerBeforeIOAndRollback/rollback=true','internal/domain/runtime_session_events_windows_test.go','failed event transaction leaves no physical IO, TOOL_STARTED or STARTED effect assertions remain'),
 ('TestClientGoalSessionWriterAndSettlementGates/expired_lease','internal/domain/client_protocol_goal_test.go','LEASE_EXPIRED and goals=1/tasks=1/runs=0 assertions remain'),
 ('TestClientGoalSessionWriterAndSettlementGates/missing_lease','internal/domain/client_protocol_goal_test.go','LEASE_EXPIRED and goals=1/tasks=1/runs=0 assertions remain'),
]

def pin(path):
 raw = path.read_bytes()
 return {'path': path.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def write_new(path,text):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8',newline='\n') as out:
  out.write(text)

def replace_one(text,before,after):
 if text.count(before) != 1:
  raise ValueError('exact replacement count differs: '+before[:110])
 return text.replace(before,after,1)

def tokens(text):
 out=[]; n=0
 while n<len(text):
  c=text[n]
  if c.isspace(): n+=1; continue
  if text.startswith('//',n):
   end=text.find('\n',n+2); n=len(text) if end<0 else end+1; continue
  if text.startswith('/*',n):
   end=text.find('*/',n+2)
   if end<0: raise ValueError('unclosed comment')
   n=end+2; continue
  start=n
  if c in ('"', "'", chr(96)):
   quote=c; n+=1
   while n<len(text):
    if text[n]==quote:
     n+=1; break
    if quote!=chr(96) and text[n]=='\\':
     n+=2
    else: n+=1
   else: raise ValueError('unclosed Go string')
  elif c.isalpha() or c=='_':
   n+=1
   while n<len(text) and (text[n].isalnum() or text[n]=='_'): n+=1
  elif c.isdigit():
   n+=1
   while n<len(text) and (text[n].isalnum() or text[n] in '._'): n+=1
  else: n+=1
  out.append((text[start:n],start,n))
 return out

def close_index(ts,start,opening,closing):
 depth=0
 for i in range(start,len(ts)):
  if ts[i][0]==opening: depth+=1
  elif ts[i][0]==closing:
   depth-=1
   if depth==0: return i
 raise ValueError('unclosed Go delimiter '+opening)

def call_nodes(ts):
 calls=[]
 for i in range(len(ts)-3):
  if ts[i][0]=='t' and ts[i+1][0]=='.' and ts[i+2][0] in ('Fatal','Fatalf','Error','Errorf','Skip','Skipf') and ts[i+3][0]=='(':
   end=close_index(ts,i+3,'(',')')
   calls.append(tuple(x[0] for x in ts[i:end+1]))
 return calls

def assertion_if_nodes(ts):
 nodes=[]
 for i in range(len(ts)):
  if ts[i][0]!='if': continue
  round_depth=square_depth=0; start=None
  for j in range(i+1,len(ts)):
   v=ts[j][0]
   if v=='(': round_depth+=1
   elif v==')': round_depth-=1
   elif v=='[': square_depth+=1
   elif v==']': square_depth-=1
   elif v=='{' and round_depth==0 and square_depth==0:
    start=j; break
  if start is None: raise ValueError('if without body')
  end=close_index(ts,start,'{','}')
  node=ts[i:end+1]
  if any(x[0] in ('Fatal','Fatalf','Error','Errorf') for x in node):
   nodes.append(tuple(x[0] for x in node))
 return nodes

def balanced(ts):
 stack=[]
 mates={')':'(',']':'[','}':'{'}
 for v,_,_ in ts:
  if v in ('(','[','{'): stack.append(v)
  elif v in mates:
   if not stack or stack.pop()!=mates[v]: return False
 return not stack

base=[]; changes=[]; checks=[]
for rel,prior in expected.items():
 path=T5/rel; raw=path.read_bytes()
 observed=(hashlib.sha256(raw).hexdigest(),len(raw))
 if observed!=prior: raise ValueError('T5 pinned base changed: '+rel)
 original=raw.decode('utf-8')
 revised=original
 if rel in tops:
  revised=replace_one(revised,'muBrokerFixtureProgram(t,','typedMuBrokerFixtureProgram(t,')
  for name in tops[rel]:
   header='func '+name+'(t *testing.T) {\n'
   revised=replace_one(revised,header,header+'\tif typedRuntimeFixtureChild(t) {\n\t\treturn\n\t}\n')
  if 'runtime_permission' in rel:
   revised=replace_one(revised,'SessionRuntime: c, WorkspaceAuthority: permissionWorkspaceFixture','SessionRuntime: c, ConfigurationAuthority: c.config.ConfigurationAuthority, WorkspaceAuthority: permissionWorkspaceFixture')
   revised=replace_one(revised,'Host: ClientHostInfo{CoreBuildID: "permission-fixture"','Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "permission-fixture"')
   revised=replace_one(revised,'\tcreated := muClientCall(t, f, service, env)\n','\tcreated := muClientCall(t, f, service, env)\n\tattachTypedRuntimeFixture(t, f, service, created, "permission-client")\n')
  elif 'runtime_tool_integration' in rel:
   revised=replace_one(revised,'SessionRuntime: c, Host: ClientHostInfo{CoreBuildID: "mu-tool-fixture"','SessionRuntime: c, ConfigurationAuthority: c.config.ConfigurationAuthority, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "mu-tool-fixture"')
   revised=replace_one(revised,'\tcreated := muClientCall(t, f, service, env)\n','\tcreated := muClientCall(t, f, service, env)\n\tattachTypedRuntimeFixture(t, f, service, created, "mu-client")\n')
  else:
   revised=replace_one(revised,'SessionRuntime: c, Host: ClientHostInfo{CoreBuildID: "event-fixture"','SessionRuntime: c, ConfigurationAuthority: c.config.ConfigurationAuthority, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "event-fixture"')
   revised=replace_one(revised,'\t\t\tsid := deref(created.SessionID)\n','\t\t\tattachTypedRuntimeFixture(t, f, svc, created, "event-client")\n\t\t\tsid := deref(created.SessionID)\n')
 else:
  revised=replace_one(revised,'type goalClientPort struct {\n','type goalClientPort struct {\n\tprincipal, project string\n')
  revised=replace_one(revised,'goalClientPort{workspace: workspace, model: "goal-model"','goalClientPort{principal: f.owner, project: f.project, workspace: workspace, model: "goal-model"')
  method='''// Synthetic Goal unit port: validate only this fixture's original Goal-created
// Session binding. It grants no native runtime/profile qualification or model IO.
func (p goalClientPort) ValidateLegacySession(ctx context.Context, tx *sql.Tx, principal, project, sid, model string) error {
 if tx == nil || principal == "" || sid == "" || principal != p.principal || project != p.project || model != p.model {
  return Fail(503, "MODEL_UNAVAILABLE", "synthetic Goal model scope differs")
 }
 creator, err := clientSessionCreationPrincipal(ctx, tx, project, sid)
 if err != nil || creator != principal {
  return Fail(503, "MODEL_UNAVAILABLE", "synthetic Goal creator unavailable")
 }
 var workspace, actualModel string
 if err = tx.QueryRowContext(ctx, "SELECT workspace_ref,model_config_ref FROM client_sessions WHERE id=? AND project_id=?", sid, project).Scan(&workspace, &actualModel); err != nil || workspace != p.workspace || actualModel != model {
  return Fail(503, "MODEL_UNAVAILABLE", "synthetic Goal Session binding differs")
 }
 var original int
 if err = tx.QueryRowContext(ctx, "SELECT count(*) FROM idempotency WHERE principal=? AND project=? AND operation='v2:goal.start' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.session_id') IS NULL AND json_extract(body,'$.result.snapshot.session_id')=? AND json_extract(body,'$.result.snapshot.workspace_ref')=? AND json_extract(body,'$.result.snapshot.model_config_ref')=?", principal, project, sid, workspace, model).Scan(&original); err != nil || original != 1 {
  return Fail(503, "MODEL_UNAVAILABLE", "synthetic Goal original creation differs")
 }
 return nil
}

'''.replace('\n ', '\n\t')
  revised=replace_one(revised,'func goalFixture(t *testing.T)',method+'func goalFixture(t *testing.T)')
 oldtokens,newtokens=tokens(original),tokens(revised)
 oldcalls,newcalls=call_nodes(oldtokens),call_nodes(newtokens)
 oldifs,newifs=assertion_if_nodes(oldtokens),assertion_if_nodes(newtokens)
 calls_preserved=all(newcalls.count(v)>=oldcalls.count(v) for v in set(oldcalls))
 ifs_preserved=all(newifs.count(v)>=oldifs.count(v) for v in set(oldifs))
 names=re.compile(r'func (Test\w+)\(t \*testing.T\)')
 tests_unchanged=names.findall(original)==names.findall(revised)
 item={'file':rel,'original_assertion_and_skip_calls':len(oldcalls),'original_assertion_if_nodes':len(oldifs),'original_calls_preserved':calls_preserved,'original_assertion_if_nodes_preserved':ifs_preserved,'original_test_names_preserved':tests_unchanged,'go_lexical_delimiters_balanced':balanced(newtokens),'not_compiled':True}
 if not all(item[k] for k in ('original_calls_preserved','original_assertion_if_nodes_preserved','original_test_names_preserved','go_lexical_delimiters_balanced')):
  raise ValueError('source preservation check failed: '+rel)
 write_new(C/rel,revised)
 base.append(pin(path)); changes.append(pin(C/rel)); checks.append(item)
 diff=''.join(difflib.unified_diff(original.splitlines(keepends=True),revised.splitlines(keepends=True),fromfile=path.as_posix(),tofile=(C/rel).as_posix()))
 write_new(Q/(Path(rel).stem+'.patch'),diff)
helper=C/'internal/domain/runtime_typed_client_fixture_windows_test.go'
helper_text=helper.read_text(encoding='utf-8')
helper_tokens=tokens(helper_text)
helper_check={'file':helper.relative_to(C).as_posix(),'go_lexical_delimiters_balanced':balanced(helper_tokens),'no_skip_call':not any(x[2] in ('Skip','Skipf') for x in call_nodes(helper_tokens)),'no_insecure_tls':not any(x[0]=='InsecureSkipVerify' for x in helper_tokens),'normal_x509_fallback_roots':'x509.SetFallbackRoots(pool)' in helper_text,'public_config_before_profile':helper_text.index('handlerCommand(t, f, service, env)')<helper_text.index('handlerTLSCoordinatorFixture(t, f,'),'explicit_attach_after_sequence':'Object{"after_sequence": 0, "request_write_owner": true}' in helper_text,'parent_child_raw_result_files':all(x in helper_text for x in ('child-invocation.json','child.stdout.raw','child.stderr.raw','child-result.json','parent-result.json')),'Root_job_closure_pending':'REQUIRES_ROOT_GO_JOB_RECEIPT' in helper_text,'formal_acceptance_false':'"formal_acceptance": false' in helper_text,'not_compiled':True}
# The lexical scanner preserves exact assertion nodes; it is not a Go AST/compiler.
helper_check['no_skip_call']=not any(len(x)>2 and x[2] in ('Skip','Skipf') for x in call_nodes(helper_tokens))
for key,value in helper_check.items():
 if isinstance(value,bool) and key!='not_compiled' and not value:
  raise ValueError('typed helper static check failed: '+key)
checks.append(helper_check); changes.append(pin(helper))
raw_path=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/current-composition-full-domain-root-0d2a82e73b754a5f/full-domain-and-native-authority-offline.stdout.raw'
raw=raw_path.read_bytes()
if hashlib.sha256(raw).hexdigest()!='b4d15819134bd1d16c976828022c76aad741859967bbf0a3617986b0ca0308ae':
 raise ValueError('original Root FULL pin changed')
wanted={name for name,_,_ in scope}; failures={name:[] for name in wanted}
totals={'pass':0,'fail':0,'skip':0}
for number,line in enumerate(raw.decode('utf-8').splitlines(),1):
 try: event=json.loads(line)
 except json.JSONDecodeError: continue
 if isinstance(event,dict) and event.get('Test') and event.get('Action') in totals:
  totals[event['Action']]+=1
 if isinstance(event,dict) and event.get('Action')=='fail' and event.get('Test') in wanted:
  failures[event['Test']].append({'raw_line':number,'actual_event':event})
if totals!={'pass':1261,'fail':25,'skip':4} or any(len(v)!=1 for v in failures.values()):
 raise ValueError('original FULL totals or ten scoped failure leaves differ')
mapping=[{'failed_leaf':name,'file':file,'original_failure':failures[name][0],'fixture_delta':'Goal mock exact original creator/Session/workspace/model proof' if 'client_protocol_goal' in file else 'isolated TLS + public host.configure before sealed profile + same typed ref/provider/credential + same-owner attach + original send','preserved_assertions':intent,'status':'SOURCE_ONLY_NOT_EXECUTED_NOT_ACCEPTED'} for name,file,intent in scope]
write_new(Q/'base-refs.json',json.dumps({'root':T5.as_posix(),'refs':base,'new_helper_has_no_base':not (T5/helper.relative_to(C)).exists()},ensure_ascii=False,indent=2)+'\n')
write_new(Q/'source-refs.json',json.dumps({'candidate_root':C.as_posix(),'refs':changes,'production_members':0,'authority':'NONE'},ensure_ascii=False,indent=2)+'\n')
write_new(Q/'static-checks.json',json.dumps({'mode':'GO_LEXICAL_TEXT_NODE_PRESERVATION_NOT_GO_AST','checks':checks,'compiled':False,'Go_native_SQL_model_executed':0,'formal_acceptance':False},ensure_ascii=False,indent=2)+'\n')
write_new(Q/'scope-map.json',json.dumps({'raw_ref':pin(raw_path),'original_test_totals':totals,'scope_leaf_count':10,'mapping':mapping,'authority':'NONE','formal_acceptance':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidate_root':C.as_posix(),'changed_test_members':len(changes),'scoped_failures':len(mapping),'static_checks':checks,'Source_refs':pin(Q/'source-refs.json'),'base_refs':pin(Q/'base-refs.json'),'scope_map':pin(Q/'scope-map.json')},ensure_ascii=False))

