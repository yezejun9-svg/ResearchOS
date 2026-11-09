import pathlib,json,hashlib,datetime
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W13/W13-03/desktop_http_first_branch_revision_codex/a8e573ecbd20499c8bff9d4222dd9ffc'
O=R/'execution/v2.4/receipts/W13/W13-03/desktop_http_first_branch_revision_independent_review_codex/0311803e945b45ab9f8a60c9a7452c01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
manifest=read(P/'manifest.json'); audits=[]
for item in manifest['files']:
 p=P/item['path']; b=p.read_bytes(); audits.append({'expected':item,'actual':ref(p),'match':hashlib.sha256(b).hexdigest()==item['sha256'] and len(b)==item['bytes']})
save('manifest_audit.json',{'input':ref(P/'manifest.json'),'count':len(audits),'mismatch_count':sum(not x['match'] for x in audits),'entries':audits})
inputs=read(P/'inputs.current.json')['files']; before=[]
for item in inputs:
 p=pathlib.Path(item['path']);p=p if p.is_absolute() else R/p
 exists=p.is_file();a=ref(p) if exists else None
 good=exists==item.get('exists',True) and (not exists or (a['sha256']==item['sha256'] and a['bytes']==item['bytes']))
 before.append({'expected':item,'actual':a,'exists':exists,'match':good})
save('inputs.before.json',{'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(before),'mismatch_count':sum(not x['match'] for x in before),'rows':before,'atomic_snapshot':False})
protected=[]
for item in read(P/'protected_ranges.json'):
 p=R/item['path'];lines=p.read_bytes().splitlines(keepends=True);raw=b''.join(lines[item['first_line']-1:item['last_line']]);h=hashlib.sha256(raw).hexdigest()
 protected.append({'expected':item,'actual_sha256':h,'actual_bytes':len(raw),'match':h==item['sha256'] and len(raw)==item['bytes']})
save('protected_ranges_audit.json',{'count':len(protected),'mismatch_count':sum(not x['match'] for x in protected),'rows':protected})
roster=read(P/'finite_roster.expanded.json'); scope=read(P/'source_scope.final.json'); proposal=read(P/'proposal.final.json')
names=[x['name'] for x in roster['leaves']]; oldids={x.get('original_scenario') for x in roster['leaves'] if x.get('original_scenario')}
save('roster_audit.json',{'named_leaves':len(names),'unique_names':len(set(names)),'regression_units':len(roster['regressions']),'all_NOT_RUN':all(x['status']=='NOT_RUN' for x in roster['leaves']+roster['regressions']),'HTTP_leaf_cap_sum':sum(x['http_request_cap'] for x in roster['leaves']),'child_leaf_cap_sum':sum(x['pure_child_cap'] for x in roster['leaves']),'HTTP_regression_cap_sum':sum(x['http_cap'] for x in roster['regressions']),'original_scenario_references':sorted(oldids),'source_paths_count':len(scope['paths']),'source_paths_unique':len({x['path'] for x in scope['paths']}),'no_run':True})
selected=['handoff.json','proposal.final.json','source_scope.final.json','finite_roster.expanded.json','manifest.json','conditions_resolution.json','capacity_and_lifecycle.json','protocol_preflight_supplement.json','deployment_contract.json','numeric_resource_graph.json','fixture_amendments.json','implementation_order.final.json','protected_ranges.json','inputs.current.json','resources.before.json']
refs=[]
for name in selected:
 p=P/name;copy=O/('original-'+name);copy.write_bytes(p.read_bytes());refs.append({'original':ref(p),'copy':ref(copy)})
save('input_refs.json',refs)
conds=[
('D01-CAPACITY',['proposal.final.json#/capacity_layers','capacity_and_lifecycle.json','protocol_preflight_supplement.json'],'CLOSED_AT_SCOPE','8/16MiB raw limits,33554436base64+1024metadata=33555460 frame,64MiBoutput,depth/node/numeric/decodedstring/queuebuffers bounds explicit; publicHost1MiB remains unchanged and separate. Six-key final precedence resolves preliminary five-key note.'),
('D02-PURE-SCHEMA',['proposal.final.json#/validation_order','numeric_resource_graph.json','protocol_preflight_supplement.json'],'CLOSED_AT_SCOPE','Full raw syntax/UTF8/duplicate/EOF then UseNumber and frozen SchemaDoc input/response definitions, no wire domain.Decode/JCS/float64. REQUEST phase must complete/reap before identical captured request bytes can be POSTed. Resource limits precede big.Rat.'),
('D03-PREBUILDER',['source_scope.final.json#/paths/14','proposal.final.json#/prebuilder_revision'],'CLOSED_AT_SCOPE','Explicit15th v2.js comments/envelopeFor only; default configure four null and scoped CAS/project goal exceptions distinguishable. No table/classifier/schema/domain edits.'),
('D04-BINARY-DEPLOYMENT',['deployment_contract.json','source_scope.final.json#/paths/9','resources.before.json'],'CLOSED_FOR_DEVELOPMENT_SCOPE_ONLY','Fixedrealpath descriptor/exe/module/assets closure and new stopped development publication tree; actual resolver/child controls planned. Installedpackaging/asar caller remainsHOLD, no arbitrarypath override or beforeafterhash immutableimage claim.'),
('D05-CHILD-LIFECYCLE',['capacity_and_lifecycle.json','protocol_preflight_supplement.json','deployment_contract.json'],'CLOSED_AT_SCOPE_WITH_RUNTIME_PROOF_DUE','Held ChildProcess object,actual exit+pipeclose+childclose,5srun+5sreap,unreaped blocksqueue. No barePID kill. REQUEST/RESPONSE max2children; HTTP10s. Runtime support and outer process ownership must be evidenced, not inferred from nonce.'),
('D06-RESPONSE-IDENTITY',['proposal.final.json#/scope_and_identity','proposal.final.json#/HTTP_error_layer','finite_roster.expanded.json'],'CLOSED_AT_SCOPE','Original tuple and applicable nestedidentity; onlycreate newSID; readonlyforeignwriter allowed; no invented topclient/project; ACK pending doesnotadopt or unlock by laterGET; HostConfigRevision neverSessionCAS; statuserrors separate.'),
('D07-LOSSLESS-RENDERERS',['numeric_resource_graph.json','source_scope.final.json','finite_roster.expanded.json'],'CLOSED_AT_SCOPE_WITH_REAL_RENDERER_PROOF_DUE','ActualReactdist and legacyHTML+preload/IPC/Electronoffscreen planned; safe exactNumber/BigInt and retaineddecimal values, actual subsequentrequest literal checks. Legacy small primitives mirrored inownedscript avoidingnewCSP/fileESM assumption; VM/mock not substitute.'),
('D08-FIXTURE-CORRECTION',['fixture_amendments.json','protected_ranges.json'],'CLOSED_AT_SCOPE','FalsehoststatusSID/partialSnapshot/ACKthenGET positives corrected onlyownedspans. Originalcredential/401/nativebootstrap assertions protected. Synthetic samecommandCOMPLETED remainsfixture; actualHostcompletionHOLD.'),
('D09-FINITE-ROSTER',['finite_roster.expanded.json','implementation_order.final.json'],'CLOSED_AT_SCOPE','159 namednewleaves+7regressionunits;69statusgrammar versusactualHost capability distinguished;11channels/23methods maintained;162newHTTP+224regressionHTTP=386max;future0MODELSDKexternalpaid.'),
('D10-PROVENANCE-AND-STOP',['implementation_order.final.json','resources.before.json','inputs.current.json'],'CLOSED_AT_SCOPE_WITH_EXECUTION_CLOSURE_DUE','Fullactualcompiler/deps/embed/WORK/generated/importcfg/archive/newexe andElectron/Vite/assets/resources beforefirstcase required. Current106 publicinputs are not actualcompiledclosure. Firstunexpected stop/noautoretry/sourcecohortmix;noformalacceptance.')]
save('conditions_review.json',{'old_conditions_sha256':'da8a81322991a010aef325dbe4e78129c33e0be8242480370712e3947aea7b05','rows':[{'id':a,'refs':[ref(P/x.split('#')[0])|({'json_locator':x.split('#')[1]} if '#' in x else {}) for x in b],'verdict':c,'reason':d,'execution':'NOT_RUN'} for a,b,c,d in conds]})
limitations=[
'Final six-key REQUEST/RESPONSE protocol is authoritative over preliminary five-key capacity notes. SourceRoot grant must bind final proposal+supplement, not preliminary standalone notes.',
'Go future command list should use -compiled along with -deps -test -json so the promised complete compiled variants are captured; full -work/-x build/generated/archive closure remains mandatory. This is a verification command completion, not an additional product path.',
'Resource hashes currently establish availability, not runtime versions, successful compilation, deployedbinary or complete process dependency closure. Freeze actual Electron/Node/Go/Python/tool and imported assets before running.',
'Per-leaf caps are maxima, not expected emitted counts. In particular missingbinary/preflightfail must emit zeroHTTP even if its generic roster maximum is1; stage-specific noPOST assertions are mandatory.',
'ChildProcess object and correlationnonce alone do not establish OS creationTIME. Actual pinnedruntime ownership/exit/pipeclose controls must establish safe cleanup. If supported implementation needs code outside15, stop and requestexactscope rather than use barePID.',
'ActualHost>1MiB, actualattach/cancel/resume producercompletion, nativeframing, browserContinuity, installedpackaging, GUI/NVDA formal and liveprovider stayHOLD.',
'Offscreen renderer fixtures are not installedGUI/NVDA acceptance. Public95/159/7 counts must never be reported as actualpassed before native receipts. Original scenario count remains93; no new95 scenario claim is made.'
]
# Remove wording unrelated to the frozen scenario count; retain exact93/159/7 distinction.
limitations[-1]='Offscreen renderer fixtures are not installedGUI/NVDA acceptance. Original93 scenarios,159 futureleaves and7 regressionunits must not be reported as actualpassed before native receipts.'
save('implementation_conditions.json',{'conditions':limitations,'no_source_lease_granted_by_reviewer':True})
after=[]
for row in before:
 p=pathlib.Path(row['expected']['path']);p=p if p.is_absolute() else R/p
 a=ref(p) if p.is_file() else None;after.append({'path':str(p),'before':row['actual'],'after':a,'unchanged':a==row['actual']})
save('inputs.after.json',{'rows':after,'drift_count':sum(not x['unchanged'] for x in after),'atomic_snapshot':False})
issues=sum(not x['match'] for x in audits)+sum(not x['match'] for x in before)+sum(not x['match'] for x in protected)+sum(not x['unchanged'] for x in after)
save('tool_observations.json',{'read_success_tool_refs':['1c373f','013ae5','8058e9','599ee0','4f73e1','2d1fa9'],'actual_exits':0,'display_truncation':['599ee0','4f73e1'],'fullbytes_independently_hashed':True,'new_failures':[],'new_failure_count':0,'old_locator_chain':'STOPPED; prior3 originnonzero retained in earlierreview, notrecounted. Onlymanifest/exactrefs used.','target_execution':{'Go':0,'Node':0,'SQL':0,'HTTP':0,'GUI':0,'SDK':0,'MODEL':0,'helper_import':0},'receipt_sealing':'Python hashing/JSON only, no target execution.'})
save('review.json',{'schema':'researchos.desktop-http-revised-scope-independent-review.v1','reviewer':'codex:/root/command_queue_impl','source_author':'codex:/root/sources_parent_impl','decision':'SOURCE_SCOPE_READY_WITH_CONDITIONS' if issues==0 else 'REQUEST_CHANGES_INPUT_MISMATCH','authorship':'Reviewer did not implement Desktop15 product changes; scope review only, no acceptance of prior reviewer-authored products.','input_handoff_ref':ref(P/'handoff.json'),'conditions_review_ref':ref(O/'conditions_review.json'),'implementation_conditions_ref':ref(O/'implementation_conditions.json'),'manifest_audit_ref':ref(O/'manifest_audit.json'),'roster_audit_ref':ref(O/'roster_audit.json'),'protected_ranges_audit_ref':ref(O/'protected_ranges_audit.json'),'source_scope_ref':ref(P/'source_scope.final.json'),'proposal_ref':ref(P/'proposal.final.json'),'scope_paths':15,'input_mismatch_count':issues,'future_new_leaves':159,'future_regression_units':7,'future_total_HTTP_cap':386,'tests_actual_run':0,'product_source_ready':False,'implementation_lease_granted':False,'Main_integration_authorized':False,'formal_increment':0,'conclusion':'The prior10conditions are resolved at design/scope level for a development-resource DesktopHTTP slice, subject to the explicit implementation conditions and Root grant. This doesnot establish any runtime result or installedproduct qualification.'})
save('handoff.json',{'decision':read(O/'review.json')['decision'],'review_ref':ref(O/'review.json'),'conditions_ref':ref(O/'conditions_review.json'),'implementation_conditions_ref':ref(O/'implementation_conditions.json'),'source_scope_ref':ref(P/'source_scope.final.json'),'proposal_ref':ref(P/'proposal.final.json'),'original_manifest_entries':len(audits),'public_inputs':len(before),'input_mismatch_count':issues,'future_tests':'159new+7regression NOT_RUN','new_failures':0,'product_source_ready':False,'no_self_authorization':True})
allfiles=sorted(p for p in O.iterdir() if p.is_file() and p.name!='manifest.json');save('manifest.json',{'files':[ref(p) for p in allfiles],'listed_count':len(allfiles),'self_excluded':True})
print(json.dumps({'issues':issues,'manifest131':len(audits),'inputs':len(before),'protected':len(protected),'refs':{n:ref(O/n) for n in ['review.json','conditions_review.json','implementation_conditions.json','handoff.json','manifest.json']}},ensure_ascii=True))
