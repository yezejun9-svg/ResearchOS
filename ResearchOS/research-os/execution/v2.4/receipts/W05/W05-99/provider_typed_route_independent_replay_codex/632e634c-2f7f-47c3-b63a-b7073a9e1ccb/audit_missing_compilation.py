import pathlib,json,hashlib,subprocess,os,re
H=pathlib.Path(__file__).resolve().parent;M=pathlib.Path('D:/作品集/ResearchOS/research-os');A=M/'.local/worktrees/codex-w0599-provider-binding';R=M/'.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c';C='6fb5263681c17f0e50920c354dc07ed440a23714';P=A/'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1/compiled-inputs.before.json'
def ref(p):b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_NO_REPLACE_OBJECTS']='1';src=json.loads(P.read_text(encoding='utf-8'));missing=[];checked=[]
for name,item in src['files'].items():
 p=pathlib.Path(name)
 if not p.is_relative_to(A):continue
 rel=p.relative_to(A).as_posix()
 if rel.startswith('.local/') or rel.startswith('execution/'):continue
 dest=R/rel
 if dest.is_file():checked.append({'relative':rel,'sha256':ref(dest)['sha256'],'author_sha256':item['sha256']});continue
 args=['git','-C',str(A),'show',C+':'+rel];raw=subprocess.check_output(args,env=env);blob=subprocess.check_output(['git','-C',str(A),'rev-parse',C+':'+rel],env=env).decode().strip();digest=hashlib.sha256(raw).hexdigest();assert digest==item['sha256'];text=raw.decode('utf-8');missing.append({'path':rel,'git_blob':blob,'sha256':digest,'bytes':len(raw),'author_compiled_entry':item,'has_init':bool(re.search(r'func\s+init\s*\(',text)),'has_embed':'go:embed' in text,'imports':re.findall(r'"(researchos\.local/research-os/[^"\n]+)"',text),'source_only_not_execute':True,'git_read_argv':args,'git_read_exit':0})
assert all(x['sha256']==x['author_sha256'] for x in checked)
report={'candidate':C,'author_frozen_graph':ref(P),'checked_existing_candidate_compilation_inputs':len(checked),'existing_mismatches':[],'missing':missing,'missing_count':len(missing),'destination':str(R),'scope_requested':'Only listed immutable public production compile inputs. No tests/cmd/evidence/holdout data or function execution. No restoration occurred.','go_list_result':ref(H/'go-list.result.json'),'go_list_stderr':ref(H/'go-list.stderr.raw'),'next_no_blind_iteration':'This compares every local candidate entry of sealed author compiled graph, not just first reported import; current independent go-list must still establish fresh actual graph after precise authorization.'}
with (H/'all-missing-compiled-public-resources.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'request':ref(H/'all-missing-compiled-public-resources.json'),'existing':len(checked),'missing':missing},ensure_ascii=False,indent=2))
