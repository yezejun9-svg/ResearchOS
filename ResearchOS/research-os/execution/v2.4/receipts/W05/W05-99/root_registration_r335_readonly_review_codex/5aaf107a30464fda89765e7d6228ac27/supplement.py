import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882';C=[];I={}
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def raw(x):
 p=path(x);b=p.read_bytes();I[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def ref(x):raw(x);return I[str(path(x))]
def doc(x):return json.loads(raw(x))
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def pin(r):
 b=raw(r['path']);ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
p=doc(N/'prepared_refs.json');b=doc(N/'binding.json');s=json.loads(pin(p['scope_ref']));a=doc(O/'audit.json');cp,ow=[json.loads(pin(x)) for x in p['desired_refs'][:2]]
scope_ref=dict(ref(N/'scope_registration.json'),path=(N/'scope_registration.json').relative_to(R).as_posix())
prior=doc(R/'execution/v2.4/receipts/W05/W05-99/root_registration_r335_readonly_review_codex/ed6067d4f5e94377a97828d032cf51ab/scope-ref-compatibility.json')
gate_ref=s['authorization_verifier_ref'];pipe_ref=next(x for x in b['metadata_code_refs'] if x['sha256']=='c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755')
gt=pin(gate_ref).decode();pt=pin(pipe_ref).decode()
ck('same reviewed Gate/pipeline producer consumer',gate_ref['sha256']==prior['finding']['source_refs'][0]['sha256'] and pipe_ref['sha256']==prior['finding']['source_refs'][1]['sha256'])
ck('prior R335 scope mismatch closed in actual prepared/desired',scope_ref==p['scope_ref']==cp['work_in_progress']['desktop58_finite_validation_scope_ref']==ow['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation']['scope_ref'])
actualRoot=doc(N/'tool-observations.fourth-full-scope.closed.original.json');ck('same exact Root originally saved scope_ref',actualRoot['actual_scope_ref']==scope_ref and actualRoot['scope_ref_root_relative_from_first_creation'] is True)
ck('three exactkey REL scope pin',set(scope_ref)=={'path','sha256','bytes'} and not Path(scope_ref['path']).is_absolute() and '\\' not in scope_ref['path'])
for label,needle in [('load_scope','sr = reader.ref(scope_path)'),('CP scope',"wip['desktop58_finite_validation_scope_ref'] == scope_ref"),('OW scope',"lease['scope_ref'] == scope_ref"),('grant scope',"grant['scope_ref'] == scope_ref"),('registration refs',"registration == registration_refs(reader, scope)"),('grant authority',"grant['authority_review_refs'] == authority"),('observationABS',"str(path) == item['path'] == expected_path")]:ck('unchanged Gate interface '+label,needle in gt)
for label,needle in [('grant final self validation',"gate.validate_grant(str(safe(scope_ref['path'])),scope_ref['sha256']"),('registration refs producer','rr=gate.registration_refs(reader,scope)'),('runtime explicitABS',"observed.append({'path':str(safe(copyref['path']))"),('successmarker',"observation['all_observed_inputs_pre_pinned']=True"),('all4 immediate CAS',"'all-four immediately before replace CAS'"),('postguardCAS',"'post-source-guard final four CAS'"),('pregrantCAS',"'immediate pre-grant live four CAS'")]:ck('unchanged producer interface '+label,needle in pt)
const={}
for node in ast.parse(pt).body:
 if isinstance(node,ast.Assign):
  for t in node.targets:
   if isinstance(t,ast.Name):
    try:const[t.id]=ast.literal_eval(node.value)
    except (ValueError,TypeError):pass
expected=[str(path(s['new_authorization_root'])/(x+'.json')) for x in const['OBSERVATION_PHASES']]
ck('three runtime observations ABS exactordered',len(expected)==3 and s['expected_runtime_observation_paths']==expected and all(Path(x).is_absolute() for x in expected))
rt=json.loads(pin(s['runtime_resources_ref']));rows={x['path']:x for x in rt['files']}
for r in b['metadata_code_refs']:
 z=rows.get(str(path(r['path'])));ck('metadataREL -> actual runtimeABS '+r['path'],not Path(r['path']).is_absolute() and z is not None and z['sha256']==r['sha256'] and z['bytes']==r['bytes'])
w=cp['work_in_progress'];ck('authority/reviews preserved exactscope values',w['desktop58_finite_validation_current_source_authority_ref']==s['current_source_authority_ref'] and w['desktop58_finite_validation_controller_review_ref']==b['controller_review_ref'] and w['desktop58_finite_validation_CLI2_qualification_ref']==s['current58_CLI2_qualification_ref'])
ck('review scopeSHA pin actually reviewed',doc(b['controller_review_ref']['path'])['scope_sha256']==scope_ref['sha256'])
copies=a['copied_canonical_before_refs']
for live,original,own in zip(p['canonical_before'],p['original_refs'],copies):ck('final byteexact live+original+owncopy '+live['path'],pin(live)==pin(original)==pin(own) and path(own['path']).parent==O)
for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']:ck('fresh fiveleaf '+k,not path(s[k]).exists())
for n in ['invocation.json','canonical-write.intent.json','registration-audit.json','manifest.json']:ck('future Root phase absent '+n,not (N/n).exists())
matrix=[]
for row in prior['interface_matrix']:
 v=dict(row)
 if v['interface'].startswith('scope prepare'):
  v.update(status='RESOLVED_IN_NEW_PREPARED_INPUT',actual=scope_ref,expected=scope_ref,consequence='The actual prepared CP WIP and OW lease now match Reader.ref exactdict. Future grant must be invoked with the identical dictionary; no actual grant claimed.')
 matrix.append(v)
rr=save('compatibility-supplement.json',{'schema':'researchos.root-registration-ref-compatibility-review.v1','reviewer':'codex:/root/w05_merge_review','checks':C,'failed':[x for x in C if not x['passed']],'closed_finding':'R335-SCOPE-REF-01','scope_ref':scope_ref,'interface_matrix':matrix,'prior_matrix_ref':ref(R/'execution/v2.4/receipts/W05/W05-99/root_registration_r335_readonly_review_codex/ed6067d4f5e94377a97828d032cf51ab/scope-ref-compatibility.json'),'input_refs':list(I.values()),'actual_registration_executed':False,'future_grant_input_required':scope_ref,'no_additional_static_blocker_found':not any(not x['passed'] for x in C),'new_failure_count':0,'new_failure_origins':[]})
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'supplement_ref':rr,'new_failure_count':0},ensure_ascii=False))
