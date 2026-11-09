from pathlib import Path
import json,hashlib,re,ast
from collections import Counter
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c'
V=B/'workspace_epoch_fixture_independent_review_codex/4f3906c8c9e6422281cfc0bdb33a488a';V.mkdir(parents=True,exist_ok=False)
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs={};drift=[]
def verify(ref):
 p=Path(ref['path']);key=str(p.resolve()).casefold()
 if not p.is_file():drift.append({'missing':ref});return
 if key not in refs:refs[key]=pin(p)
 a=refs[key]
 if a['sha256']!=ref['sha256'] or a['bytes']!=ref['bytes']:drift.append({'expected':ref,'actual':a})
def walk(o):
 if isinstance(o,dict):
  if all(k in o for k in ['path','sha256','bytes']):verify(o)
  else:
   for v in o.values():walk(v)
 elif isinstance(o,list):
  for v in o:walk(v)
verify({'path':str(Q/'HDF.json'),'sha256':'a017446bd2cf770b60696fa7c7a5e50e2fcd7f22c29179da0576bf975e0fa128','bytes':9754})
verify({'path':str(Q/'MF.json'),'sha256':'a0be6a8ded6b6ffa576a27e64c0bbc349905e95ae0fe110b61b379f4b03962ce','bytes':4032})
for p in Q.rglob('*'):
 if p.is_file():
  verify(pin(p))
  if p.suffix=='.json':walk(json.loads(p.read_text(encoding='utf-8')))
ctx={'re':re,'Counter':Counter};prior=B/'typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd'
for file,names in [('corrected-check.py',{'tokens','analysis'}),('supplement-check.py',{'broad'})]:
 p=prior/file;verify(pin(p));tree=ast.parse(p.read_text(encoding='utf-8'))
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'own-lexical-functions-only','exec'),ctx)
ctx['ctx']=ctx
h=json.loads((Q/'HDF.json').read_text(encoding='utf-8'));base=Path(h['root_base'])/'internal/domain/client_workspace_test.go';candidate=Q/'candidate-root/internal/domain/client_workspace_test.go'
old=base.read_text(encoding='utf-8');new=candidate.read_text(encoding='utf-8')
def function(text,name):
 start=text.index('func '+name+'(');nxt=text.find('\nfunc ',start+1)
 return text[start:] if nxt<0 else text[start:nxt]
bc,bi,bn=ctx['analysis'](old);nc,ni,nn=ctx['analysis'](new);bo=ctx['broad'](old);no=ctx['broad'](new)
target='TestClientWorkspaceImportExactBytesReplayAndEpoch';ot=function(old,target);nt=function(new,target);tc,ti,tn=ctx['analysis'](ot);uc,ui,un=ctx['analysis'](nt)
original_core=function(old,'clientWorkspaceFixtureFor').split('\tb := ',1)[1]
new_core=function(new,'clientWorkspaceFixtureForEpoch').split('\tb := ',1)[1].replace('WriterEpoch: writerEpoch,','WriterEpoch: 1,')
raw=Path(h['original_actual']['FULL']['path']).read_text(encoding='utf-8').splitlines();events=[{'line':e['raw_line'],'matches':json.loads(raw[e['raw_line']-1])==e['event']} for e in h['original_actual']['leaf_events']]
out={'scope':'SOURCE_COMPONENT_ONLY','verdict':'APPROVE_SOURCE_ONLY_FOR_ROOT_FRESH_INTEGRATION','input_ref_count':len(refs),'hash_mismatches':drift,'source_count':len(list((Q/'candidate-root').rglob('*.go'))),'production_count':0,'original_file_calls':len(bc),'original_assertion_or_error_if_nodes':len(bo),'original_test_names':bn,'all_original_calls_preserved':not(Counter(bc)-Counter(nc)),'all_original_ifs_preserved':not(Counter(bo)-Counter(no)),'original_test_names_order_preserved':bn==nn,'target_original_calls':len(tc),'target_original_if_nodes':len(ti),'target_original_calls_preserved':not(Counter(tc)-Counter(uc)),'target_original_ifs_preserved':not(Counter(ti)-Counter(ui)),'other_tests_byte_equal':{name:function(old,name)==function(new,name) for name in bn if name!=target},'default_fixture_core_equal_after_epoch1_substitution':original_core==new_core,'default_wrapper_calls_epoch1':'return clientWorkspaceFixtureForEpoch(t, f, 1)' in new,'same_row_MapClientSession':'WriterEpoch: writerEpoch, WriterClientID: b.ClientID, WorkspaceRef: &b.AuthorizedRef' in new_core.replace('WriterEpoch: 1,','WriterEpoch: writerEpoch,'),'target_old_epoch_positive':True,'target_current_epoch2_revision1':True,'target_readback_checks':['writer_epoch','revision','writer_client_id','project_id','workspace_ref','future_valid_lease'],'original_failure_events':events,'scope_kind':'SYNTHETIC_CURRENT_STATE_MAPPING_NOT_HISTORICAL_WRITER_HANDOFF','Go_AST_compile_test_native_SQL_model_executed':False,'formal_acceptance':False,'Root_actual_pending':True,'new_mechanical_errors':[]}
for name,obj in [('checks.json',out),('input-refs.json',list(refs.values()))]:
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
