import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-429e1734d9da4efba276680e78e2510b'
I={};C=[]
def p(x):
 x=Path(x);return x if x.is_absolute() else R/x
def raw(x):
 x=p(x);b=x.read_bytes();I[str(x)]={'path':str(x),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def ref(x):raw(x);return I[str(p(x))]
def doc(x):return json.loads(raw(x))
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def pin(r):
 b=raw(r['path']);ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def save(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def anchors(text,needles):
 lines=text.splitlines();return [{'text':n,'line_numbers':[i+1 for i,l in enumerate(lines) if n in l]} for n in needles]
d=doc(N/'prepared_refs.json');b=doc(N/'binding.json');s=json.loads(pin(d['scope_ref']));a=doc(O/'audit.json')
gate_ref=s['authorization_verifier_ref'];gt=pin(gate_ref).decode('utf-8');ast.parse(gt)
module_ref=next(x for x in b['metadata_code_refs'] if x['sha256']=='c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755')
mt=pin(module_ref).decode('utf-8');ast.parse(mt)
scope_bytes=pin(d['scope_ref']);expected={'path':(N/'scope_registration.json').relative_to(R).as_posix(),'sha256':hashlib.sha256(scope_bytes).hexdigest(),'bytes':len(scope_bytes)}
desired=[json.loads(pin(r)) for r in d['desired_refs']]
actual=d['scope_ref'];wip=desired[0]['work_in_progress'];lease=desired[1]['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation']
ck('confirmed ABS serialized scope in prepared',Path(actual['path']).is_absolute())
ck('actual ABS ref is propagated unchanged to CP and OW',wip['desktop58_finite_validation_scope_ref']==lease['scope_ref']==actual)
ck('same physical scope/hash/bytes but not exact gate ref',p(actual['path'])==p(expected['path']) and actual['sha256']==expected['sha256'] and actual['bytes']==expected['bytes'] and actual!=expected)
status=doc(N/'prepare.status.invocation.json');args=['status','--porcelain=v1','--untracked-files=no']
ck('corrected status argv equals both actual producer and consumer',status['argv'][1:]==args and "['status','--porcelain=v1','--untracked-files=no']" in mt and "['status','--porcelain=v1','--untracked-files=no']" in gt)
ck('original two static predicates retained',len(a['failed'])==2 and {x['check'] for x in a['failed']}=={'scope exact ROOTrelative3key','read-only Git argv/env status'})
for live,original,copy in zip(d['canonical_before'],d['original_refs'],a['copied_canonical_before_refs']):
 ck('live/copy/original byte equality '+live['path'],pin(live)==pin(original)==pin(copy) and p(copy['path']).parent==O)
for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']:ck('still absent '+k,not p(s[k]).exists())
for name in ['invocation.json','canonical-write.intent.json','registration-audit.json']:ck('no actual registration '+name,not (N/name).exists())
ck('review and authority exact dictionary propagation',wip['desktop58_finite_validation_controller_review_ref']==b['controller_review_ref'] and wip['desktop58_finite_validation_current_source_authority_ref']==s['current_source_authority_ref'] and wip['desktop58_finite_validation_CLI2_qualification_ref']==s['current58_CLI2_qualification_ref'])
ck('metadata serialization ROOT-relative',all(not Path(x['path']).is_absolute() for x in b['metadata_code_refs']))
runtime=json.loads(pin(s['runtime_resources_ref']));runtime_rows={str(p(x['path'])):x for x in runtime['files']}
for x in b['metadata_code_refs']:
 y=runtime_rows.get(str(p(x['path'])));ck('metadata runtime ABS overlay '+x['path'],y is not None and Path(y['path']).is_absolute() and y['sha256']==x['sha256'] and y['bytes']==x['bytes'])
phases=next(ast.literal_eval(n.value) for n in ast.parse(mt).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OBSERVATION_PHASES' for t in n.targets))
ck('three canonicalABS observation destinations in exact producer order',s['expected_runtime_observation_paths']==[str(p(s['new_authorization_root'])/(x+'.json')) for x in phases])
ganchors=anchors(gt,["sr = reader.ref(scope_path)","wip['desktop58_finite_validation_scope_ref'] == scope_ref","lease['scope_ref'] == scope_ref","registration == registration_refs(reader, scope)","grant['scope_ref'] == scope_ref","grant['authority_review_refs'] == authority","prelaunch['runtime_resources_ref'] == scope['runtime_resources_ref']","str(path) == item['path'] == expected_path","path.parent == root","return scope"])
manchors=anchors(mt,["def pin(p):","'scope_ref':scope_ref","wip_values(b,scope_ref)","gate.load_scope(reader","gate.validate_authority(reader,scope,scope_ref","gate.validate_grant(str(safe(scope_ref['path']))","observed.append({'path':str(safe(copyref['path']))","--scope-ref"])
matrix=[
 {'interface':'scope prepare -> desiredCP/OW -> grant -> final gate','status':'BLOCKER','required_spelling':'ROOT-relative forward slashes; exact path/sha256/bytes dictionary','producer':'argref verifies then preserves caller dictionary; wip_values and desktop_lease preserve it; grant preserves it','consumer':'load_scope constructs reader.ref(ROOT scope), hence ROOT-relative; validate_authority and validate_grant use exact dictionary equality','actual':actual,'expected':expected,'consequence':'Grant internal final validate_grant fails before grant.completed; changing only grant argument to REL also fails earlier against already-ABS CP/OW.'},
 {'interface':'controller review and registration review refs','status':'NO_ADDITIONAL_MISMATCH_FOUND_STATIC','required_spelling':'Preserve each supplied sealed ref verbatim through WIP/invocation/audit/authority; review path identity is resolved separately','producer':'controller_review_ref copied binding->CP; review_ref copied run->invocation->audit','consumer':'controller review canonical path plus content hashes; audit.review_ref==inv.review_ref; grant authority exact values','restriction':'Do not globally rewrite ABS review refs merely to fix scope.'},
 {'interface':'current source authority / CLI2 qualification review manifest','status':'NO_ADDITIONAL_MISMATCH_FOUND_STATIC','required_spelling':'Original scope ref dictionaries unchanged','producer':'binding WIP projection, grant authority update from scope','consumer':'WIP authority==scope authority; WIP CLI2==scope CLI2; authority_review_refs exact returned dictionary'},
 {'interface':'registration_refs, manifest entries, audit links, intent, verified, done/raw/script refs','status':'NO_ADDITIONAL_MISMATCH_FOUND_STATIC','required_spelling':'ROOT-relative forward slashes for generated repo files; exact 3-key pins','producer':'pipeline pin/write/save emits relative refs; seal manifest emits pin for each actual file; grant uses gate.registration_refs','consumer':'Reader.ref generates same relative refs; registration dict/listed entries/audit links/verified intent compared exactly','restriction':'Future actual sealed registration refs still need actual metadata closure review; no absent output is invented.'},
 {'interface':'four canonical before/reviewer copies/grant copies','status':'NO_ADDITIONAL_MISMATCH_FOUND_STATIC','required_spelling':'canonical_path uses exact CANON relative order; copy ref may be resolved ABS or REL but must be under correct review/auth parent and pinned','producer':'review own bytecopies; grant copy_fact produces relative ref to exclusive auth leaf','consumer':'review4 copies same parent + byte equality; grant canonical_path order, parent and desired bytes; no whole-ref equality to live canonical path'},
 {'interface':'runtime catalogue, metadata8, observed modules and three observation references','status':'NO_ADDITIONAL_MISMATCH_FOUND_STATIC','required_spelling':'Metadata code refs serialized ROOT-relative; catalogue and actual observed module paths canonicalABS; final three observation refs canonicalABS in scope-declared order','producer':'verify metadata then safe ABS membership; copy_fact then explicit ABS projection into observed list','consumer':'runtime exact member SHA/bytes; prelaunch.runtime_resources_ref exactscope value; observation path string==expected canonicalABS and parent auth root','restriction':'Marker means pinned point-time observation; Python lifecycle remains false. Do not convert these ABS paths to REL.'},
 {'interface':'full scope binding and code/resources fixed refs','status':'NO_ADDITIONAL_MISMATCH_FOUND_STATIC','required_spelling':'grant.binding is complete scope object; code refs canonicalABS; same_ref canonicalizes only at explicitly coded sites','producer':'gate.binding(scope) returns scope unchanged','consumer':'grant.binding==binding(scope); CODE_KEYS absolute canonical path; resource union member exact dictionaries','restriction':'same_ref is not used for failing scope_ref fields and cannot remedy them.'}
]
finding={'id':'R335-SCOPE-REF-01','severity':'BLOCKER','summary':'Prepared ABS scope reference cannot satisfy Gate ROOT-relative exact-dictionary consumers.','actual_scope_ref':actual,'required_scope_ref':expected,'source_refs':[gate_ref,module_ref],'gate_source_anchors':ganchors,'producer_source_anchors':manchors,'minimum_fix':'Root must use a new immutable allocation/input cycle. Construct scope_ref from the actual scope bytes with ROOT-relative path before prepare; propagate the exact same three-key dictionary to prepare and grant. Validate desired CP WIP and OW lease dictionary equality against Gate Reader.ref semantics before CAS. Keep all old prepared/desired/scope/audits and fixed historical cuts unchanged. Do not weaken Gate or normalize unrelated ABS-required code/runtime references.'}
save('scope-ref-compatibility.json',{'schema':'researchos.root-registration-ref-compatibility-review.v1','reviewer':'codex:/root/w05_merge_review','finding':finding,'interface_matrix':matrix,'checks':C,'failed':[x for x in C if not x['passed']],'original_audit_ref':ref(O/'audit.json'),'predicate_correction':{'original_check':'read-only Git argv/env status','old_assumption':'-uno','actual_and_required':'--untracked-files=no','classification':'STATIC_AUDIT_PREDICATE_FALSE_POSITIVE','original_audit_unchanged':True,'original_tool_exit':0,'new_failure_origin':False},'input_refs':list(I.values()),'actual_registration_executed':False,'candidate_calls':0,'product_calls':0,'new_failure_origins':[]})
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'confirmed_blockers':1,'supplement_ref':ref(O/'scope-ref-compatibility.json'),'new_failure_count':0},ensure_ascii=False))
