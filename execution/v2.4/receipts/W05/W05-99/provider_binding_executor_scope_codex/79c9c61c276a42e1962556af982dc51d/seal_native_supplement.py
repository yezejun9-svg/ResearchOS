import pathlib,json,hashlib,datetime,decimal,sys
sys.stdout.reconfigure(encoding='utf-8')
R=pathlib.Path('D:/作品集/ResearchOS/research-os');H=pathlib.Path(__file__).resolve().parent
N=R/'execution/v2.4/receipts/W05/W05-99/provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-native-read'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def save(n,v):
 p=H/n
 if p.exists():raise RuntimeError('immutable output already exists '+str(p))
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
items=[]
for name in ['invocation.json','headers.raw','response.html','visible-text.txt','observations.json']:
 source=N/name;b=source.read_bytes();dest=H/'snapshots/native-official-context'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 if source.read_bytes()!=b:raise RuntimeError('native evidence drift')
 items.append({'source':ref(source),'snapshot':ref(dest),'actual_read':'Path.read_bytes','exit':0,'before_after_equal':True})
if sha((N/'response.html').read_bytes())!='210f102275ccf1a6542f08a3bc9e4b4c7c83278cb74b35217bffa112df6363b2':raise RuntimeError('response hash mismatch')
if sha((N/'observations.json').read_bytes())!='72387e6e7bdcf0891751fb236c665c3a3ffe51be9cd7f74a54d089d9ff507048':raise RuntimeError('observation hash mismatch')
d=decimal.Decimal;bound=d(1048576)*d('0.30')/d(1000000)+d(8192)*d('1.20')/d(1000000)
save('native-context-supplement.json',{'schema':'researchos.provider-scope-native-source-supplement.v1','issued_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal_ref':ref(H/'proposal.json'),'source_evidence':items,'effect':'Adds independently reviewable actual native HTTP200 official context evidence; no proposal field, source scope, canonical state or old evidence rewritten. Replaces no previous failed web result.','decimal_formula_result_USD':str(bound),'proposed_reserve_per_MODEL_USD':'0.50','maximum_calls':6,'maximum_reserve_USD':'3.00','gateway_same_context_mapping':'Explicit inference requiring independent scope review; authenticated Go model ID did not report context.','actual_cost':None,'implementation_or_live_authorization':False})
save('handoff.final.json',{'schema':'researchos.provider-executor-final-scope-handoff.v1','status':'READY_FOR_INDEPENDENT_SCOPE_REVIEW_ONLY','actor':'codex:/root/command_queue_impl','proposal':ref(H/'proposal.json'),'prior_handoff':ref(H/'handoff.json'),'native_context_supplement':ref(H/'native-context-supplement.json'),'source_before':ref(H/'inputs.before.json'),'source_after':ref(H/'inputs.final.json'),'actual_source_drift':0,'L04_candidate_clean':'fef0ee2d56351e74ceed11b0b37d3f87e9c83494','eight_plus_ninth_decision':'8 exact proposed paths; ninth runtime_model_stream.go separately required after T08 freeze for full END/backup/no-observation original effect proof. No edits authorized by proposal.','budget':'Same original ordinary Task/Run max_calls4 (expected2 MODEL separated by TOOL), plus qualification max2. Proposed0.50 USD/call,total3.00, pending independently accepted context/price bound and reservation. actual_cost staysunknown.','reads':'57 frozen/main inputs rechecked0drift; official publicdocs read only; no model/privateDB/credential requests.','manifest':'manifest.final.json covers all evidence including previous immutable manifest, excluding itself.'})
files=[ref(p) for p in sorted(H.rglob('*')) if p.is_file() and p.name!='manifest.final.json']
save('manifest.final.json',{'schema':'researchos.receipt-manifest.v1','files':files,'file_count':len(files),'self_excluded':'manifest.final.json'})
for item in files:
 if sha((R/item['path']).read_bytes())!=item['sha256']:raise RuntimeError('manifest drift')
print(json.dumps({'proposal':ref(H/'proposal.json'),'native_supplement':ref(H/'native-context-supplement.json'),'handoff':ref(H/'handoff.final.json'),'manifest':ref(H/'manifest.final.json'),'files':len(files),'decimal_bound':str(bound)},indent=2,ensure_ascii=False))
