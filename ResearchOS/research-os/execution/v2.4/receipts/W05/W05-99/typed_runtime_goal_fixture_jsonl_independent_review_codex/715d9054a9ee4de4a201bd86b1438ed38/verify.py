from pathlib import Path
import json,hashlib,re,ast
from collections import Counter
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9'
Q1=B/'typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931'
V=B/'typed_runtime_goal_fixture_jsonl_independent_review_codex/715d9054a9ee4de4a201bd86b1438ed38'
V.mkdir(parents=True,exist_ok=False)
oldreview=B/'typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd'
toolreview=B/'official_test2json_resource_independent_review_codex/fd737b147f004cb4be2e57a0f85d9c4e'
def pin(p):
 raw=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
refs={};drift=[]
def verify(ref):
 p=Path(ref['path']);key=str(p.resolve()).casefold()
 if not p.is_file():drift.append({'missing':ref});return
 if key not in refs:refs[key]=pin(p)
 a=refs[key]
 if a['sha256']!=ref['sha256'] or a['bytes']!=ref['bytes']:drift.append({'expected':ref,'actual':a})
def walk(obj):
 if isinstance(obj,dict):
  if all(k in obj for k in ['path','sha256','bytes']):verify(obj)
  else:
   for v in obj.values():walk(v)
 elif isinstance(obj,list):
  for v in obj:walk(v)
verify({'path':str(Q/'HDF.json'),'sha256':'9d0e393bedf1e647008cf9022081664ab7511ab6d341edeaa4831482bcd29340','bytes':10797})
verify({'path':str(Q/'MF.json'),'sha256':'65cd84d5c0b440f0c70acbb808c1960102bf03107e10aca1a83f0081f7035ca4','bytes':5997})
for p in Q.rglob('*'):
 if p.is_file():
  verify(pin(p))
  if p.suffix=='.json':walk(json.loads(p.read_text(encoding='utf-8')))
for name in ['HDF.json','MF.json','checks.json','report.md']:
 p=toolreview/name;verify(pin(p))
 if name=='MF.json':walk(json.loads(p.read_text(encoding='utf-8')))
ctx={'re':re,'Counter':Counter}
for filename,names in [('corrected-check.py',{'tokens','analysis'}),('supplement-check.py',{'broad'})]:
 p=oldreview/filename;verify(pin(p));tree=ast.parse(p.read_text(encoding='utf-8'))
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'independent-lexical-functions-only','exec'),ctx)
ctx['ctx']=ctx
checks=[]
for ref in json.loads((Q1/'base-refs.json').read_text(encoding='utf-8'))['refs']:
 verify(ref);p=Path(ref['path']);n=Q/'candidate-root/internal/domain'/p.name;old=Q1/'candidate-root/internal/domain'/p.name
 original=p.read_text(encoding='utf-8');new=n.read_text(encoding='utf-8')
 bc,bi,bn=ctx['analysis'](original);nc,ni,nn=ctx['analysis'](new);bo=ctx['broad'](original);no=ctx['broad'](new)
 checks.append({'file':p.name,'byte_equal_Q1':n.read_bytes()==old.read_bytes(),'calls':len(bc),'calls_preserved':not(Counter(bc)-Counter(nc)),'top_test_names':len(bn),'top_test_names_preserved':bn==nn,'strict_if':len(bi),'lexical_if':len(bo),'strict_if_preserved':not(Counter(bi)-Counter(ni)),'lexical_if_preserved':not(Counter(bo)-Counter(no))})
helper=Q/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go';old=Q1/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go'
h=helper.read_text(encoding='utf-8');h1=old.read_text(encoding='utf-8');ctx['analysis'](h)
marker='func typedMuBrokerFixtureProgram('
tail_equal=helper.read_bytes().split(marker.encode('utf-8'),1)[1]==old.read_bytes().split(marker.encode('utf-8'),1)[1]
base=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain'
contract=base/'contracts.go';official=R/'.local/tools/go1.27.1/go/src/cmd/internal/test2json/test2json.go';main=official.parent.parent.parent/'test2json/main.go'
for p in [contract,official,main]:verify(pin(p))
go=R/'.local/tools/go1.27.1/go/bin/go.exe';actualGo=pin(go);verify(actualGo)
gohex=actualGo['sha256']
new_funcs=set(re.findall(r'^func (typedRuntimeFixture\w+)\(',h,re.M));duplicates=[]
for p in base.glob('*.go'):
 for name in new_funcs:
  if re.search(r'^func '+re.escape(name)+r'\(',p.read_text(encoding='utf-8'),re.M):duplicates.append({'file':p.as_posix(),'name':name})
decoder=h.split('func typedRuntimeFixtureDecodeEvent(',1)[1].split('func typedRuntimeFixtureVerifyJSONL(',1)[0]
out={'scope':'SOURCE_COMPONENT_ONLY','verdict':'REQUEST_CHANGES','input_ref_count':len(refs),'hash_mismatches':drift,'candidate_files':[p.relative_to(Q/'candidate-root').as_posix() for p in (Q/'candidate-root').rglob('*') if p.is_file()],'four_files':checks,'totals':{'calls':sum(x['calls'] for x in checks),'names':sum(x['top_test_names'] for x in checks),'lexical_if':sum(x['lexical_if'] for x in checks),'strict_if':sum(x['strict_if'] for x in checks)},'TLS_configure_profile_provider_attach_tail_byte_equal_Q1':tail_equal,'helper_delimiters_balanced':True,'duplicate_new_helper_functions':duplicates,'digest_mismatch_static_counterexample':{'actual_go_bare_sha256':gohex,'domain_Digest_result_from_definition':'sha256:'+gohex,'expected_const':re.search(r'const typedRuntimeFixtureGoSHA256 = "([^"]+)"',h).group(1),'comparison_can_succeed':False,'definition':pin(contract)},'decoder_allowed_fields':re.findall(r'case "([^"]+)":',decoder),'official_OutputType_field_absent_from_decoder':'case "OutputType":' not in decoder,'official_schema_ref':pin(official),'official_main_ref':pin(main),'findings':['Resource pins compare domain sha256:-prefixed Digest against bare 64hex and reject first Go input.','Pinned Go1.27.1 emits OutputType=frame for normal framing; strict decoder rejects it as unknown.'],'prior_child_JSONL_direction':'Text-substring logic removed and strict event state machine added, but mandatory official happy path remains blocked.','actual_Go_compile_test_native_SQL_model_executed':False,'new_mechanical_errors':[],'formal_acceptance':False}
for name,obj in [('checks.json',out),('input-refs.json',list(refs.values()))]:
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
