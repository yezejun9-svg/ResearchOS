import pathlib,json,hashlib,subprocess,datetime,re
O=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');H=R/'.local/worktrees/codex-w0599-host-configuration-handler'
P='execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/cli-product-scope-f31f46a2fa3d4432b52d02c4cd4b1921/'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p).replace('\\','/'),'sha256':sha(b),'bytes':len(b)}
def put(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return ref(p)
reads=[]
def snap(label,base,rel):
 p=base/rel;b=p.read_bytes();d=O/'inputs'/label/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b);reads.append({'label':label,'original':ref(p),'snapshot':ref(d)});return b
proposal=json.loads(snap('author_proposal',H,P+'proposal.json'));assert sha((H/P/'proposal.json').read_bytes())=='71024bfbd1f9115354fb61c4efb3742f07b47eaf15d77f2a7ee15fcb65d2fd87'
for n in ['manifest.json','handoff.json','input.before.json','input.after.json','public_sources.json','diagnostics.json']:snap('author_proposal',H,P+n)
source=[]
for row in proposal['source_scope']:
 path=row['path']; state={'path':path,'expected_exists':row['exists'],'main_exists':(R/path).is_file(),'author_exists':(H/path).is_file()}
 if row['exists']:
  mb=snap('main',R,path);hb=snap('author',H,path);state.update(main_sha256=sha(mb),author_sha256=sha(hb),matches_proposal=(sha(mb)==sha(hb)==row['source_before_sha256']))
  assert state['matches_proposal']
 else: assert not state['main_exists'] and not state['author_exists']
 source.append(state)
for path in ['apps/cli/cli_verbs.go','apps/cli/cli_doctor.go','apps/cli/cli_stream_test.go','tests/runtime/cli_contract/main.go','internal/api/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.schema.json']:
 snap('main_protected',R,path)
for path in ['internal/domain/client_protocol_configuration.go','internal/domain/client_protocol.go']:
 snap('handler_unfrozen_readonly',H,path)
frozen='execution/v2.4/receipts/W04/W04-99/executor_revalidation_codex/frozen_inputs/package/'
for path in ['22_CLIENT_INTERFACE_DETAILS.md','tasks/steps/W05-03.md','contracts/product.contract.json','contracts/tasks.json']:
 snap('frozen',R,frozen+path)
q=subprocess.run(['git','-C',str(R),'show','2cdb0d43d5a600eef13c8f1735946a9adf52d079:tests/runtime/cli_contract/v2verbs.go'],capture_output=True)
(O/'old_v2verbs.git.raw').write_bytes(q.stdout);(O/'old_v2verbs.git.stderr.raw').write_bytes(q.stderr);assert q.returncode==0 and q.stdout==(R/'tests/runtime/cli_contract/v2verbs.go').read_bytes()
put('git_original_fixture.json',{'argv':['git','-C',str(R),'show','2cdb0d43d5a600eef13c8f1735946a9adf52d079:tests/runtime/cli_contract/v2verbs.go'],'actual_exit_code':q.returncode,'stdout':ref(O/'old_v2verbs.git.raw'),'stderr':ref(O/'old_v2verbs.git.stderr.raw'),'matches_current_and_proposal':True})
schema=json.loads((R/'internal/api/contracts/client.protocol.schema.json').read_text(encoding='utf-8-sig')); defs=schema['$defs'];put('frozen_relevant_schema.json',{k:defs[k] for k in ['ConfigurePayload','ConfigureResult','ModelConfiguration','CommandResponse','ProtocolError','HostStatusResult']})
text=q.stdout.decode('utf-8');ids=re.findall(r'\b(?:ok|skip)\("([^"]+)"',text);put('original_fixture_check_ids.json',{'all_ids_in_original_order':ids,'all_count':len(ids),'configuration_related':[x for x in ids if any(k in x for k in ['MODEL','SWITCH','CONFIG','SETTLE','EPOCH'])],'protection':'No deletion, rename, skip or weaker predicate; only explicitly specified representation corrections and setup plus stronger causal observations.'})
checks=[]
for row in reads:
 a=ref(pathlib.Path(row['original']['path']));checks.append({'path':a['path'],'before':row['original']['sha256'],'after':a['sha256'],'unchanged':a['sha256']==row['original']['sha256']})
put('read_audit.json',{'inputs':reads,'input_count':len(reads),'after':checks,'all_observed_unchanged':all(x['unchanged'] for x in checks),'exact5_source_before':source,'case_execution':0,'sql':0,'node':0,'model':0,'http':0,'private_reads':0,'source_or_canonical_writes':0,'handler_candidate_not_frozen':True})
print(json.dumps({'inputs':len(reads),'source':source,'old_fixture_ids':len(ids),'drift':[x for x in checks if not x['unchanged']]},ensure_ascii=True))
