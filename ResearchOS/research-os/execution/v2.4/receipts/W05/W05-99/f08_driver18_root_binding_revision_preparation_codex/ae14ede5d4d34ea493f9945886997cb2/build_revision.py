"""Pure IO/AST revision construction. Never imports or executes candidates."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99'
OLD=BASE/'f08_driver18_root_binding_preparation_codex/a03c54991b5b44f9bdb6743d8b78b0c9'
V3=BASE/'f08_driver18_execution_revision_preparation_codex/fb328e152ae54da6b4be24cbc3b94ece'
REVIEW=BASE/'f08_driver18_root_adapter_independent_source_review_codex/3a2dfa5a7b9545dbb85c82703e519be7/review.json'
INPUTS={}
CHANGES=[]

def pin(p,raw=None):
    raw=p.read_bytes() if raw is None else raw
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):
    raw=p.read_bytes();INPUTS[str(p)]=pin(p,raw);return raw
def write(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return pin(OUT/name,raw)
def save(name,obj):return write(name,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def change(text,old,new,label):
    if text.count(old)!=1:raise ValueError('Unique exact source anchor required: '+label)
    CHANGES.append({'label':label,'old':old,'new':new})
    return text.replace(old,new,1)
def finish(name,oldpath,oldraw,text,start):
    raw=text.encode('utf8');ast.parse(raw,filename=name)
    inverse=text
    edits=CHANGES[start:]
    for e in reversed(edits):
        if inverse.count(e['new'])!=1:raise ValueError('Inverse ambiguity '+e['label'])
        inverse=inverse.replace(e['new'],e['old'],1)
    if inverse.encode('utf8')!=oldraw:raise ValueError('Whole-byte inverse failed '+name)
    ref=write(name,raw)
    save(name+'.inverse.json',{'original_ref':pin(oldpath,oldraw),'candidate_ref':ref,
         'whole_byte_inverse_equal':True,'edits':edits,'candidate_executed':False})
    write(name+'.diff',''.join(difflib.unified_diff(oldraw.decode('utf8').splitlines(True),text.splitlines(True),fromfile=str(oldpath),tofile=name)).encode('utf8'))
    return ref

if pin(REVIEW,read(REVIEW))['sha256']!='da06bf17259ab69b4823dcba16f3ea27735ead3d7a44d76e617de6ab292d5a27':raise ValueError('Review pin')
cp=V3/'driver18_controller.v3.proposed.py';cb=read(cp);ct=cb.decode('utf8');start=len(CHANGES)
ct=change(ct,"            mappings=[('test_source_ref','fork/driver18_innocuous_test.go')",'''            # Re-inventory the actual pristine module AFTER all offline copies.
            pristine=work/'modcache/modernc.org/sqlite@v1.60.1'
            expected_pristine={str(rel(row['relative_path'])).casefold():row for row in old['files']}
            actual_pristine={}
            for p in u.files(pristine):
                rp=str(p.relative_to(pristine)).casefold()
                need(rp not in actual_pristine,'PRISTINE_POST_COPY_DUPLICATE')
                actual_pristine[rp]=pin(p)
            need(len(expected_pristine)==1899 and set(actual_pristine)==set(expected_pristine),'PRISTINE_POST_COPY_MEMBERSHIP')
            for rp,row in expected_pristine.items():
                actual=actual_pristine[rp]
                need(actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],'PRISTINE_POST_COPY_BYTES')
                verify(actual)
            mappings=[('test_source_ref','fork/driver18_innocuous_test.go')''','R01-post-offline-pristine-inventory')
CREF=finish('driver18_controller.v4.proposed.py',cp,cb,ct,start)

ap=OLD/'authority_adapter.proposed.py';ab=read(ap);t=ab.decode('utf8');start=len(CHANGES)
t=change(t,"'controller_ref':'eec4f8aaf4c6b9d3e55d6d990fb9684e25c278b2f30f6c3c7686ff1b144cb030'","'controller_ref':'"+CREF['sha256']+"'",'R01-new-controller-explicit-pin')
t=change(t,"def same_ref(a, b):",'''def path_key(p):
    # Windows physical comparison only; original path spelling stays in refs.
    return str(p).casefold()

def zero(value):
    return type(value) is int and value == 0

def exact_location(ref, root, name):
    refshape(ref)
    need(safe(ref['path']) == safe(root) / name, 'EXACT_EVIDENCE_LOCATION_' + name)

def tree_files(root):
    root=safe(root);out={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:safe(str(Path(directory)/name),root)
        for name in files:
            p=safe(str(Path(directory)/name),root);key=path_key(p)
            need(key not in out,'PHYSICAL_DUPLICATE_FILE');out[key]=p
    return out

def complete_manifest(r, ref, root, required):
    exact_location(ref,root,'manifest.json')
    member_manifest(r,ref,required)
    m=r.doc(ref);need(m['excluded_only_self'] is True,'FULL_OUTPUT_MANIFEST')
    rows=m['files'];expected=tree_files(root);expected.pop(path_key(safe(ref['path'])))
    need({path_key(safe(x['path'])) for x in rows}==set(expected),'OUTPUT_MANIFEST_MEMBERSHIP')
    for x in rows:safe(x['path'],safe(root))

def same_ref(a, b):''','R01-R02-physical-path-and-complete-manifest-helpers')
t=change(t,"key = str(safe(row['path']))","key = path_key(safe(row['path']))",'S01-manifest-member-casefold')
t=change(t,"key = str(safe(item['path']))","key = path_key(safe(item['path']))",'S01-manifest-required-casefold')
t=change(t,"r.verify(item); key=str(safe(item['path']))","r.verify(item); key=path_key(safe(item['path']))",'S01-resource-key-casefold')
t=change(t,"need(str(safe(item['path'])) in allowed and same_ref(allowed[str(safe(item['path']))],item), 'TOOL_NOT_CATALOGUED')","need(path_key(safe(item['path'])) in allowed and same_ref(allowed[path_key(safe(item['path']))],item), 'TOOL_NOT_CATALOGUED')",'S01-tool-key-casefold')
t=change(t,"need(p.parts[0]!='modernc.org' or len(p.parts)<2 or p.parts[1]!='sqlite@v1.60.1', 'PRISTINE_SOURCE_OVERWRITE')","need(p.parts[0].casefold()!='modernc.org' or len(p.parts)<2 or p.parts[1].casefold()!='sqlite@v1.60.1', 'PRISTINE_SOURCE_OVERWRITE')",'R01-pristine-subtree-casefold')
t=change(t,"ref=row['ref']; need(str(safe(ref['path'])) in allowed and same_ref(allowed[str(safe(ref['path']))],ref), 'OFFLINE_SOURCE_PIN')","ref=row['ref']; need(path_key(safe(ref['path'])) in allowed and same_ref(allowed[path_key(safe(ref['path']))],ref), 'OFFLINE_SOURCE_PIN')",'S01-offline-source-casefold')
t=change(t,"need(a['run_uuid'] in ns.name, 'ROOT_REGISTRATION_UUID')","""need(a['run_uuid'] in ns.name, 'ROOT_REGISTRATION_UUID')
    safe(a['registration_output_root'],ns)
    need(type(a['registration_timeout_seconds']) is int and a['registration_timeout_seconds']>0,
         'ROOT_EXPLICIT_METADATA_TIMEOUT')""",'R03-explicit-root-output-timeout')
t=change(t,"draft=r.doc(bundle['draft_ref']); audit=r.doc(bundle['audit_ref']); intent=r.doc(bundle['intent_ref'])","""ns=safe(a['registration_namespace']);regout=safe(a['registration_output_root'],ns)
    for key in ['draft_ref','draft_manifest_ref','audit_ref','intent_ref','invocation_ref','requested_ref',
                'wrapper_invocation_ref','verified_ref','stdout_ref','stderr_ref','manifest_ref']:
        safe(bundle[key]['path'],ns)
    for ref in bundle['registration_code_and_draft_refs'].values():safe(ref['path'],ns)
    draft=r.doc(bundle['draft_ref']); audit=r.doc(bundle['audit_ref']); intent=r.doc(bundle['intent_ref'])""",'R03-registration-namespace')
t=change(t,"need(draft['scope_ref']==sref and draft['before']==a['before'] and draft['after']==a['after'], 'DRAFT_SCOPE_TUPLE')","""need(draft['scope_ref']==sref and draft['before']==a['before'] and draft['after']==a['after'], 'DRAFT_SCOPE_TUPLE')
    need(draft['schema']=='researchos.driver18-root-registration-draft.v1' and
         draft['canonical_paths']==CANON and draft['registration_metadata_paths']==CANON[:2] and
         draft['actual_registration_executed'] is False and draft['source_acceptance'] is False and
         draft['current_root_lease']==lease(s,sref) and draft['invocation_contract']=={
             'cwd':str(ROOT),'env':s['public_environment'],'timeout':a['registration_timeout_seconds'],
             'output_root':str(regout),'registration_review_path':a['registration_review_path']},
         'CURRENT_DRAFT_LEASE_AND_INVOCATION')
    for ref in draft['original_refs']+draft['desired_refs']:safe(ref['path'],ns)""",'R03-current-draft-fields')
t=change(t,"for key in ['register','wrapper','prepared_refs','audit']:","""need(same_ref(reg['current_scope_ref'],sref) and
         same_ref(reg['registration_draft_ref'],bundle['draft_ref']) and
         same_ref(reg['registration_draft_manifest_ref'],bundle['draft_manifest_ref']) and
         reg['canonical_paths']==CANON and reg['original_refs']==draft['original_refs'] and
         reg['desired_refs']==draft['desired_refs'] and reg['current_root_lease']==lease(s,sref),
         'REGISTRATION_REVIEW_CURRENT_DRAFT')
    prepared_refs=r.doc(bundle['registration_code_and_draft_refs']['prepared_refs'])
    need(prepared_refs=={'schema':'researchos.driver18-registration-prepared-refs.v1',
         'current_scope_ref':sref,'registration_draft_ref':bundle['draft_ref'],'canonical_paths':CANON,
         'original_refs':draft['original_refs'],'desired_refs':draft['desired_refs'],
         'current_root_lease':lease(s,sref)},'REGISTRATION_PREPARED_REFS_CURRENT_DRAFT')
    preaudit=r.doc(bundle['registration_code_and_draft_refs']['audit'])
    need(preaudit['schema']=='researchos.driver18-registration-preexecution-audit.v1' and
         preaudit['actual_registration_executed'] is False and
         same_ref(preaudit['current_scope_ref'],sref) and same_ref(preaudit['registration_draft_ref'],bundle['draft_ref']) and
         preaudit['original_refs']==draft['original_refs'] and preaudit['desired_refs']==draft['desired_refs'],
         'PREEXECUTION_AUDIT_CURRENT_DRAFT')
    need(not same_ref(bundle['audit_ref'],bundle['registration_code_and_draft_refs']['audit']),
         'POSTAUDIT_CANNOT_REPLACE_PREAUDIT')
    member_manifest(r,bundle['draft_manifest_ref'],[sref,bundle['draft_ref'],
        *bundle['registration_code_and_draft_refs'].values(),*draft['original_refs'],*draft['desired_refs']])
    for key in ['register','wrapper','prepared_refs','audit']:""",'R03-review-preparedrefs-preaudit-no-cycle')
t=change(t,"resources=r.doc(s['resource_catalog_ref'])\n    need(len(inv['argv'])>=6 and safe(inv['argv'][0])==safe(resources['python']['path']) and\n         inv['argv'][1:5]==['-I','-S','-X','utf8'] and\n         safe(inv['argv'][5])==safe(bundle['registration_code_and_draft_refs']['register']['path']),\n         'ACTUAL_REGISTRATION_ARGV')","""resources=r.doc(s['resource_catalog_ref']);codes=bundle['registration_code_and_draft_refs']
    expected_argv=[resources['python']['path'],'-I','-S','-X','utf8',codes['register']['path'],
         '--registration-draft',bundle['draft_ref']['path'],'--draft-sha256',bundle['draft_ref']['sha256'],
         '--registration-review',regref['path'],'--review-sha256',regref['sha256'],
         '--output-root',str(regout)]
    request=r.doc(bundle['requested_ref'])
    need(request=={'schema':'researchos.driver18-registration-request.v1','actor':'codex:/root',
         'argv':expected_argv,'cwd':str(ROOT),'env':s['public_environment'],
         'timeout':a['registration_timeout_seconds'],'current_scope_ref':sref,
         'registration_draft_ref':bundle['draft_ref'],'review_ref':regref,
         'stdout_ref_path':bundle['stdout_ref']['path'],'stderr_ref_path':bundle['stderr_ref']['path'],
         'automatic_retry':False,'counter_reset':False},'FULL_REGISTRATION_REQUEST')
    need(inv['argv']==expected_argv and inv['cwd']==str(ROOT) and
         same_ref(inv['requested_ref'],bundle['requested_ref']) and
         same_ref(inv['registration_draft_ref'],bundle['draft_ref']) and same_ref(inv['current_scope_ref'],sref) and
         inv['env']==request['env'] and inv['timeout']==request['timeout'], 'ACTUAL_REGISTRATION_ARGV')
    wrapper=r.doc(bundle['wrapper_invocation_ref'])
    need(wrapper['actor']=='codex:/root' and wrapper['argv']==[
         resources['python']['path'],'-I','-S','-X','utf8',codes['wrapper']['path'],
         '--request',bundle['requested_ref']['path'],'--request-sha256',bundle['requested_ref']['sha256']] and
         wrapper['cwd']==str(ROOT) and wrapper['env']==s['public_environment'] and
         same_ref(wrapper['requested_ref'],bundle['requested_ref']) and
         same_ref(wrapper['inner_invocation_ref'],bundle['invocation_ref']) and
         wrapper['automatic_retry'] is False and wrapper['counter_reset'] is False,
         'ACTUAL_WRAPPER_FULL_REQUEST_PAIR')
    job(wrapper['result'])
    for obj in [intent,audit,verified]:
        need(same_ref(obj['current_scope_ref'],sref) and same_ref(obj['registration_draft_ref'],bundle['draft_ref']) and
             same_ref(obj['requested_ref'],bundle['requested_ref']), 'CAS_ENVELOPE_CURRENT_PAIR')
    need(same_ref(audit['wrapper_invocation_ref'],bundle['wrapper_invocation_ref']) and
         same_ref(audit['draft_manifest_ref'],bundle['draft_manifest_ref']), 'AUDIT_WRAPPER_AND_DRAFT')
    for key in ['stdout_ref','stderr_ref','invocation_ref','requested_ref','wrapper_invocation_ref',
                'audit_ref','intent_ref','verified_ref','manifest_ref']:
        safe(bundle[key]['path'],regout)""",'R03-full-child-wrapper-argv-and-cas-envelope')
t=change(t,"member_manifest(r,bundle['manifest_ref'],[bundle[k] for k in ['draft_ref','audit_ref','intent_ref','invocation_ref','verified_ref','stdout_ref','stderr_ref']]+draft['original_refs']+draft['desired_refs'])","member_manifest(r,bundle['manifest_ref'],[bundle[k] for k in ['draft_ref','draft_manifest_ref','audit_ref','intent_ref','invocation_ref','requested_ref','wrapper_invocation_ref','verified_ref','stdout_ref','stderr_ref']]+list(bundle['registration_code_and_draft_refs'].values())+[regref]+draft['original_refs']+draft['desired_refs']+[x['ref'] for x in copies])",'R03-final-manifest-whole-pair')
t=change(t,"def outer_completion(r, ref, s, sref, gref, phase):\n    d=r.doc(ref); raw=r.doc(d['tool_result_ref'])","""def outer_completion(r, ref, s, sref, gref, phase):
    d=r.doc(ref); raw=r.doc(d['tool_result_ref'])
    original=r.doc(d['outer_invocation_ref']);initial=r.doc(original['tool_initial_result_ref'])
    need(original['schema']=='researchos.driver18-root-outer-invocation.v1' and
         original['actor']=='codex:/root' and original['cwd']==str(ROOT) and
         original['argv']==d['argv'] and original['run_uuid']==s['actual_Root_registration']['run_uuid'] and
         same_ref(original['scope_ref'],sref) and same_ref(original['grant_ref'],gref) and
         original['launcher_output_root']==s[phase+'_launcher_output_root'] and
         original['inner_output_root']==s[phase+'_output_root'] and
         type(initial['session_id']) is int and initial['session_id']==original['session_id']==d['session_id'] and
         initial.get('exit_code') is None and d['tool_completion_session_id']==d['session_id'],
         'ORIGINAL_OUTER_INVOCATION_COMPLETION_PAIR')
    need(d['actual_native_launcher_exit'] is None,'UNSAMPLED_OUTER_NATIVE_REMAINS_NULL')""",'R02-original-outer-pair')
begin=t.index('    prepared=r.doc(s[\'prepared_ref\']);')
end=t.index('\ndef verify_authority(',begin)
old=t[begin:end]
new='''    prepared=r.doc(s['prepared_ref']);need(same_ref(proof['prepared_ref'],s['prepared_ref']),'EXACT_PREPARED_OUTPUT')
    work=safe(s['work_root']);inner=safe(ps['prepare_output_root']);outer=safe(ps['prepare_launcher_output_root'])
    locations={'prepared_ref':(inner,'prepared.json'),'inner_result_ref':(inner,'result.json'),
        'inner_manifest_ref':(inner,'manifest.json'),'launcher_invocation_ref':(outer,'inner.invocation.json'),
        'launcher_requested_ref':(outer,'requested.json'),'launcher_completed_ref':(outer,'completed.json'),
        'launcher_manifest_ref':(outer,'manifest.json'),'launcher_stdout_ref':(outer,'stdout.raw'),
        'launcher_stderr_ref':(outer,'stderr.raw')}
    for key,(root,name) in locations.items():exact_location(proof[key],root,name)
    need(prepared['work_root']==s['work_root'] and prepared['fixed_inputs_ref']==s['fixed_inputs_ref'] and
         prepared['resource_catalog_ref']==s['resource_catalog_ref'] and zero(prepared['actual_Go_calls']) and
         prepared['I17']=='FATAL_OPEN' and prepared['all18']=='NOT_RUN' and
         same_ref(prepared['root_preparation_grant_ref'],pgref), 'PREPARED_RESULT')
    fixed=r.doc(s['fixed_inputs_ref']);resources=r.doc(s['resource_catalog_ref']);expected={}
    def add(relative,source):
        p=safe(str(work/relative),work);key=path_key(p)
        need(key not in expected,'PREPARED_DESTINATION_COLLISION');r.verify(source)
        expected[key]={'path':str(p),'sha256':source['sha256'],'bytes':source['bytes']}
    for key,base in [('fork_lock_ref',Path('fork')),('original_lock_ref',Path('modcache/modernc.org/sqlite@v1.60.1'))]:
        rows=r.doc(fixed[key])['files'];need(len(rows)==1899,'EXPECTED_COMPLETE_MODULES')
        for row in rows:add(base/row['relative_path'],{k:row[k] for k in ['path','sha256','bytes']})
    for row in resources['offline_modcache_copies']:add(Path('modcache')/row['relative_path'],row['ref'])
    mappings=[('test_source_ref','fork/driver18_innocuous_test.go'),('surface_ref','consumer/surface.go'),
              ('producer_ref','consumer/cmd/i16fixture/main.go'),('probe_ref','old-probe/main.go'),
              ('consumer_mod_ref','consumer/go.mod'),('sum_ref','consumer/go.sum'),
              ('old_mod_ref','old-probe/go.mod'),('sum_ref','old-probe/go.sum')]
    need(prepared['source_overlays']==[list(x) for x in mappings],'EXACT_PREPARED_OVERLAYS')
    for key,destination in mappings:add(Path(destination),fixed[key])
    rows=prepared['files'];need(isinstance(rows,list) and rows and len(rows)==len(expected),'NONEMPTY_FULL_PREPARED_FILES')
    seen=set()
    for ref in rows:
        p=safe(ref['path'],work);key=path_key(p)
        need(key not in seen and key in expected and same_ref(ref,expected[key]),'PREPARED_EXACT_MEMBER');seen.add(key);r.verify(ref)
    need(seen==set(expected)==set(tree_files(work)),'ACTUAL_PREPARED_COMPLETE_MEMBERSHIP')
    result=r.doc(proof['inner_result_ref'])
    need(result['phase']=='prepare' and result['first_cause'] is None and result['secondary']==[] and
         zero(result['native_calls']) and result['all18_pass'] is False and result['source_acceptance'] is False and
         result['counter_reset'] is False and result['roster']==[
             {'id':f'I{i:02d}','status':'NOT_STARTED','actual_exit':None,'qualified':False} for i in range(1,19)],
         'EXACT_PREPARE_18_ROSTER_NOT_PASS')
    inv=r.doc(proof['launcher_invocation_ref']);job(inv['result']);need(zero(inv['actual_native_exit']),'ACTUAL_PREPARE_NATIVE')
    req=r.doc(proof['launcher_requested_ref']);res=r.doc(ps['resource_catalog_ref'])
    need(req=={'argv':[res['python']['path'],'-I','-S','-X','utf8',ps['controller_ref']['path'],
         'prepare',psref['path'],psref['sha256'],pgref['path'],pgref['sha256']],
         'cwd':str(ROOT),'timeout':3600,'automatic_retry':False,'env':ps['public_environment']},
         'ORIGINAL_PREPARE_CHILD_REQUEST')
    for key in ['launcher_stdout_ref','launcher_stderr_ref']:r.verify(proof[key])
    done=r.doc(proof['launcher_completed_ref']);need(zero(done['reported_exit']) and done['error'] is None and
         done['secondary']==[] and done['source_acceptance'] is False,'PREPARE_COMPLETION')
    pair=r.doc(proof['launcher_pairing_ref'])
    need(pair=={'schema':'researchos.driver18-root-sealed-launcher-pair.v1','actor':'codex:/root',
         'scope_ref':psref,'grant_ref':pgref,'launcher_ref':ps['launcher_ref'],
         'controller_ref':ps['controller_ref'],'launcher_output_root':str(outer),'inner_output_root':str(inner),
         'requested_ref':proof['launcher_requested_ref'],'invocation_ref':proof['launcher_invocation_ref'],
         'stdout_ref':proof['launcher_stdout_ref'],'stderr_ref':proof['launcher_stderr_ref'],
         'completed_ref':proof['launcher_completed_ref'],'outer_completion_ref':proof['outer_completion_ref'],
         'launcher_manifest_ref':proof['launcher_manifest_ref'],'inner_manifest_ref':proof['inner_manifest_ref'],
         'prepared_ref':s['prepared_ref'],'inner_result_ref':proof['inner_result_ref'],
         'actual_child_pid':inv['result']['owned_child_pid'],'creation_time_100ns':inv['result']['creation_time_100ns'],
         'actual_native_exit':inv['actual_native_exit'],'automatic_retry':False,'counter_reset':False},
         'ROOT_ORIGINAL_LAUNCHER_PAIR')
    outer_completion(r,proof['outer_completion_ref'],ps,psref,pgref,'prepare')
    complete_manifest(r,proof['inner_manifest_ref'],inner,[s['prepared_ref'],proof['inner_result_ref']])
    complete_manifest(r,proof['launcher_manifest_ref'],outer,[proof[k] for k in
        ['launcher_invocation_ref','launcher_completed_ref','launcher_requested_ref','launcher_stdout_ref','launcher_stderr_ref']])
'''
t=change(t,old,new,'R02-complete-prepared-and-original-raw-chain')
t=change(t,"desired=registration(r,s,sref,r.doc(g['registration_evidence_ref']))","safe(g['registration_evidence_ref']['path'],safe(a['registration_namespace']))\n    desired=registration(r,s,sref,r.doc(g['registration_evidence_ref']))",'R03-sealed-bundle-namespace')
AREF=finish('authority_adapter.v2.proposed.py',ap,ab,t,start)

bp=OLD/'binding_adapter.proposed.py';bb=read(bp);bt=bb.decode('utf8');start=len(CHANGES)
bt=change(bt,"with_name('authority_adapter.proposed.py')","with_name('authority_adapter.v2.proposed.py')",'pin-new-authority-path')
bt=change(bt,"GATE_SHA='3ad5428a0e424ae0da1a1ee5efc7d0e18f5db4ecc5290c5466074c747a56e4a5'","GATE_SHA='"+AREF['sha256']+"'",'pin-new-authority-bytes')
bt=change(bt,"s=r.doc(TEMPLATE_REF)\n    keys=","s=r.doc(TEMPLATE_REF)\n    s['controller_ref']="+repr(CREF)+"\n    keys=",'R01-builder-fixed-new-controller')
bt=change(bt,"'canonical_paths':g.CANON,'original_refs':original,'desired_refs':desired,'origin_cut_ref':s['actual_origin_cut'],","""'canonical_paths':g.CANON,'original_refs':original,'desired_refs':desired,'origin_cut_ref':s['actual_origin_cut'],
         'current_root_lease':g.lease(s,sref),'invocation_contract':{
             'cwd':str(ROOT),'env':s['public_environment'],'timeout':a['registration_timeout_seconds'],
             'output_root':str(g.safe(a['registration_output_root'])),
             'registration_review_path':a['registration_review_path']},""",'R03-draft-reviewed-invocation-contract')
bt=change(bt,"s=g.scope(r,sref);a=s['actual_Root_registration'];phase=a['phase'];prefix='f08_driver18_'+phase","s=g.scope(r,sref);a=s['actual_Root_registration'];phase=a['phase'];prefix='f08_driver18_'+phase\n    g.safe(str(out),g.safe(a['registration_namespace']))",'R03-draft-output-namespace')
BREF=finish('binding_adapter.v2.proposed.py',bp,bb,bt,start)
save('candidate-refs.json',{'controller_ref':CREF,'authority_validator_ref':AREF,'binding_adapter_ref':BREF})
save('inputs.before.json',{'files':list(INPUTS.values()),'target_executions':0})
save('construction-static.json',{'Python_AST_files':3,'whole_byte_inverse_files':3,'candidate_imports':0,
     'target_executions':0,'native_product_calls':0,'checks_passed':True,'self_acceptance':False})
print(json.dumps({'output':str(OUT),'candidate_refs':{'controller':CREF,'authority':AREF,'binding':BREF}},ensure_ascii=False))
