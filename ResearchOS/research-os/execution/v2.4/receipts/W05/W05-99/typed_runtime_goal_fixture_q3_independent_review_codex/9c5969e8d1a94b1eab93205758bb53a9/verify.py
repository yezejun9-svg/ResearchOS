from pathlib import Path
import json,hashlib,ast,re,difflib
from collections import Counter
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49';Q2=B/'typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9';Q1=B/'typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931'
V=B/'typed_runtime_goal_fixture_q3_independent_review_codex/9c5969e8d1a94b1eab93205758bb53a9';V.mkdir(parents=True,exist_ok=False)
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
verify({'path':str(Q/'HDF.json'),'sha256':'d6ab61e0522ae7f4cae0621e73a648e046ccfe9a4372c2f3848a93f5fc279658','bytes':9879})
verify({'path':str(Q/'MF.json'),'sha256':'d6d631ceac02968a7884a278e21358ee6d3c59d55fa158acd5801a10caf81138','bytes':6435})
for p in Q.rglob('*'):
 if p.is_file():
  verify(pin(p))
  if p.suffix=='.json':walk(json.loads(p.read_text(encoding='utf-8')))
toolreview=B/'official_test2json_resource_independent_review_codex/fd737b147f004cb4be2e57a0f85d9c4e'
for p in [toolreview/'HDF.json',toolreview/'MF.json',toolreview/'report.md']:
 verify(pin(p))
 if p.name=='MF.json':walk(json.loads(p.read_text(encoding='utf-8')))
tool=R/'.local/official-test2json-resource-8a1fba36028c4c0b9ed30c0a7aca54cc/programs/test2json.exe'
verify({'path':str(tool),'sha256':'dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c','bytes':4932608})
ctx={'re':re,'Counter':Counter}
oldreview=B/'typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd'
for file,names in [('corrected-check.py',{'tokens','analysis'}),('supplement-check.py',{'broad'})]:
 p=oldreview/file;verify(pin(p));tree=ast.parse(p.read_text(encoding='utf-8'))
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'independent-lexical-functions-only','exec'),ctx)
ctx['ctx']=ctx
files=[]
for ref in json.loads((Q1/'base-refs.json').read_text(encoding='utf-8'))['refs']:
 verify(ref);base=Path(ref['path']);n=Q/'candidate-root/internal/domain'/base.name;old=Q2/'candidate-root/internal/domain'/base.name
 before=base.read_text(encoding='utf-8');after=n.read_text(encoding='utf-8');bc,bi,bn=ctx['analysis'](before);nc,ni,nn=ctx['analysis'](after);bo=ctx['broad'](before);no=ctx['broad'](after)
 files.append({'file':base.name,'byte_equal_Q2_and_Q1':n.read_bytes()==old.read_bytes()==(Q1/'candidate-root/internal/domain'/base.name).read_bytes(),'calls':len(bc),'names':len(bn),'lexical_if':len(bo),'strict_if':len(bi),'all_preserved':not(Counter(bc)-Counter(nc)) and not(Counter(bi)-Counter(ni)) and not(Counter(bo)-Counter(no)) and bn==nn})
helper='candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go';new=(Q/helper).read_bytes();old=(Q2/helper).read_bytes();h=new.decode('utf-8');ctx['analysis'](h)
sm=b'func typedRuntimeFixtureVerifyJSONL(';pm=b'func typedRuntimeFixturePin(';cm=b'func typedRuntimeFixtureChild('
state_equal=new.split(sm,1)[1].split(pm,1)[0]==old.split(sm,1)[1].split(pm,1)[0]
tail_equal=new.split(cm,1)[1]==old.split(cm,1)[1]
reconstructed=h.replace('\tOutputType *string\n','').replace('\t\tcase "OutputType":\n\t\t\tvar outputType string\n\t\t\terr = json.Unmarshal(value, &outputType)\n\t\t\tevent.OutputType = &outputType\n','').replace('\t// Fixed Go1.27.1 emits OutputType only on output; it never grants a\n\t// run/pass verdict. Preserve presence to reject it even empty on other actions.\n\tif event.OutputType != nil && (event.Action != "output" || (*event.OutputType != "" && *event.OutputType != "frame" && *event.OutputType != "error" && *event.OutputType != "error-continue")) {\n\t\treturn event, fmt.Errorf("OutputType differs from fixed Go1.27.1 output schema")\n\t}\n','').replace('Digest(raw) != "sha256:"+expectedSHA','Digest(raw) != expectedSHA')
go=R/'.local/tools/go1.27.1/go/bin/go.exe';gopin=pin(go);verify(gopin)
out={'scope':'SOURCE_COMPONENT_ONLY','verdict':'APPROVE_SOURCE_ONLY_FOR_ROOT_FRESH_INTEGRATION','input_ref_count':len(refs),'hash_mismatches':drift,'source_member_count':len(list((Q/'candidate-root').rglob('*.go'))),'production_members':0,'four_original_files':files,'totals':{k:sum(x[k] for x in files) for k in ['calls','names','lexical_if','strict_if']},'minimal_four_hunks_only':reconstructed.encode('utf-8')==old,'whole_JSONL_state_machine_byte_equal_Q2':state_equal,'whole_child_TLS_configuration_profile_provider_attach_tail_byte_equal_Q2':tail_equal,'Go_lexical_delimiters_balanced':True,'Digest_fix_static_relation':{'observed_bare_Go_SHA':gopin['sha256'],'domain_Digest':'sha256:'+gopin['sha256'],'expected_comparison':'sha256:'+re.search(r'const typedRuntimeFixtureGoSHA256 = "([^"]+)"',h).group(1),'matches':gopin['sha256']==re.search(r'const typedRuntimeFixtureGoSHA256 = "([^"]+)"',h).group(1),'saved_and_postchecked_pins':'Domain Digest prefixed format retained consistently; Root expected pins remain bare.'},'OutputType_fix':{'presence_tracked_by_pointer':True,'optional_nonnull_string':True,'output_action_only_including_reject_empty_on_other_actions':True,'allowed_values':['','frame','error','error-continue'],'output_not_pass_authority':True},'prior_findings':{'Q2-DIGEST-FORMAT':'CLOSED_AT_SOURCE_LEVEL','Q2-OFFICIAL-OUTPUTTYPE':'CLOSED_AT_SOURCE_LEVEL','4396-CHILD-JSONL':'CLOSED_AT_SOURCE_LEVEL_ACTUAL_PENDING'},'Go_AST_compile_test_gofmt_native_SQL_provider_model_execution':False,'actual_pass_claim':False,'formal_acceptance':False,'authority':'NONE','Root_adoption_and_actual_decision_pending':True,'new_mechanical_failures':[]}
for name,obj in [('checks.json',out),('input-refs.json',list(refs.values()))]:
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
