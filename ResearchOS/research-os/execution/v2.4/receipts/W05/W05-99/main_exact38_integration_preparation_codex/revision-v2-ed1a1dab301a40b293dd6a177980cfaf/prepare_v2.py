"""Receipt-only, no candidate import/execution. Narrow immutable v2 derivation."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT=Path('D:/作品集/ResearchOS/research-os')
OLD=ROOT/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/7b236231f51d42319f8c21c0db715b01'
N=Path(__file__).parent
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,d):
    with (N/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def row(raw,name):
    hits=[]
    for line in raw.split(b'\0'):
        if line:
            h,p=line.split(b'\t',1)
            if p.decode('utf-8')==name:
                mode,kind,blob=h.decode('ascii').split();hits.append({'mode':mode,'kind':kind,'blob':blob})
    if len(hits)!=1:raise ValueError('Missing/duplicate tree row '+name)
    return hits[0]
source=OLD/'integrate_exact38.py';original=source.read_bytes()
if ref(source)['sha256']!='7ca8b3dcdfdfc4135da349bacefba7eb41ba18c425db43abb3e51df0fc2e155c':raise ValueError('old controller drift')
s=original.decode('utf-8')
def replace(old,new):
    global s
    if s.count(old)!=1:raise ValueError('Expected unique exact replacement')
    s=s.replace(old,new,1)
replace("expected==[321,149,421],'Only explicitly proposed Root321/149/421; old319/320 refuses'",
        "expected==[321,149,422],'Only explicitly proposed Root321/149/422; old319/320 refuses'")
replace("'failures':[417,421]","'failures':[417,422]")
helper='''def unique_git_row(raw,relative_path):
    matches=[]
    for line in raw.split(b'\\0'):
        if line:
            header,name=line.split(b'\\t',1)
            if name.decode('utf-8',errors='strict')==relative_path:
                mode,kind,blob=header.decode('ascii').split()
                matches.append({'mode':mode,'kind':kind,'blob':blob})
    require(len(matches)==1,'Missing or duplicate pinned Git row')
    return matches[0]


'''.replace('\n','\r\n')
replace('def execute(args):',helper+'def execute(args):')
old="""    reviewed={x['relative_path']:x for x in document(independent['source38_final_hashes_ref'])}
    for item in exact:
        match=reviewed[item['path']]
        require(item['after_sha256']==match['sha256'] and item['after_bytes']==match['bytes'] and
                item['after_git']['blob']==match['git_blob'] and item['after_git']['mode']==match['mode'],
                'Final map differs from independently verified source38')
""".replace('\n','\r\n')
new="""    map_ref=independent['source38_final_hashes_ref']
    require(map_ref['sha256']=='b586bfe27bd9be3aaa02ae1b684dabc4d89a266a37fe35703595fac7cf37a295' and
            scope['exact38_ref']['sha256']=='9953d625ed7b4c31fd9a2379e8df5cda8237ab822e21df15e1ac850d7e737495',
            'Frozen source maps differ')
    reviewed_rows=document(map_ref)
    require(len(reviewed_rows)==38 and len({x['relative_path'] for x in reviewed_rows})==38,'Reviewed38 uniqueness')
    reviewed={x['relative_path']:x for x in reviewed_rows}
    supplement=document(scope['mode_supplement_ref'])
    require(set(supplement)=={'schema','source_map_ref','exact38_ref','target_tree_ref','target_commit','relative_path','git_row'} and
            supplement['schema']=='researchos.exact38-single-mode-supplement.v1' and
            supplement['source_map_ref']==map_ref and supplement['exact38_ref']==scope['exact38_ref'] and
            supplement['target_commit']==CHAIN[-1] and supplement['relative_path']=='apps/control/main.go',
            'Only the exact independently reviewed single-row mode supplement is allowed')
    actual_row=unique_git_row(verify(supplement['target_tree_ref']),'apps/control/main.go')
    require(actual_row==supplement['git_row'] and actual_row['kind']=='blob','Supplement is not derived from raw Git tree')
    for item in exact:
        match=reviewed[item['path']]
        if item['path']=='apps/control/main.go':
            require(set(match)=={'relative_path','git_blob','path','sha256','bytes','API_replay_compiled_input'} and
                    match['API_replay_compiled_input'] is False and actual_row==item['after_git'] and
                    actual_row['blob']==match['git_blob'],'Unique supplemental row binding')
            mode=actual_row['mode']
        else:
            require(set(match)=={'relative_path','git_blob','mode','path','sha256','bytes'},'Other37 require original exact mode fields')
            mode=match['mode']
        require(item['after_sha256']==match['sha256'] and item['after_bytes']==match['bytes'] and
                item['after_git']['blob']==match['git_blob'] and item['after_git']['mode']==mode,
                'Final map differs from independently verified source38')
    attributes=document(scope['root_attributes_supplement_ref'])
    require(set(attributes)=={'schema','root_path','raw_ref','base_tree_ref','target_tree_ref','base_commit','target_commit','git_row','original_protected_ref'} and
            attributes['schema']=='researchos.exact38-root-attributes-supplement.v1' and
            attributes['root_path']=='.gitattributes' and attributes['base_commit']==CHAIN[0] and
            attributes['target_commit']==CHAIN[-1] and bounded(attributes['raw_ref']['path'])==ROOT/'.gitattributes',
            'Only exact root attributes may be approved')
    attribute_raw=verify(attributes['raw_ref'])
    require(attribute_raw==b'* -text\\n','Exact original root attribute bytes required')
    attr_row=unique_git_row(verify(attributes['base_tree_ref']),'.gitattributes')
    require(attr_row==unique_git_row(verify(attributes['target_tree_ref']),'.gitattributes')==attributes['git_row'] and
            attr_row['kind']=='blob' and attr_row['blob']==hashlib.sha1(b'blob '+str(len(attribute_raw)).encode()+b'\\0'+attribute_raw).hexdigest(),
            'Root attributes must be the identical base/target Git blob')
    require(attributes['original_protected_ref']['sha256']=='c1b5c28c810a9c50b9439a2e80687af489e2987cdf87676bbcd7af8b934c6277',
            'Original protected vector pin')
    original_protected=document(attributes['original_protected_ref'])
    require(len(original_protected)==5172 and protected==original_protected+[attributes['raw_ref']],
            'Protected vector must preserve original5172 prefix and append only root attributes')
""".replace('\n','\r\n')
replace(old,new)
old="""        for p in attribute_paths:
            if p.exists():
                require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()),
                        'Nonempty checkout attributes need separate scope')
""".replace('\n','\r\n')
new="""        for p in attribute_paths:
            if p.exists():
                if p==ROOT/'.gitattributes':
                    require(read(p)==verify(attributes['raw_ref'])==attribute_raw,'Exact root attribute bytes changed')
                else:
                    require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()),
                            'Nonempty checkout attributes need separate scope')
""".replace('\n','\r\n')
replace(old,new)
ast.parse(s)
oldhashes=re.findall(r"[0-9a-f]{64}",original.decode('utf-8'))
newhashes=re.findall(r"[0-9a-f]{64}",s)
if not all(newhashes.count(x)>=oldhashes.count(x) for x in set(oldhashes)):raise ValueError('Original64hex literals changed')
with (N/'integrate_exact38.v2.py').open('xb') as f:f.write(s.encode('utf-8'))
sc=load(OLD/'scope.final.proposed.json')
mapref=next(x for x in sc['evidence_refs'] if x['sha256']=='b586bfe27bd9be3aaa02ae1b684dabc4d89a266a37fe35703595fac7cf37a295')
tr=OLD/'tree-after.stdout.raw';br=OLD/'tree-before.stdout.raw'
save('single-mode-supplement.json',{'schema':'researchos.exact38-single-mode-supplement.v1','source_map_ref':mapref,
 'exact38_ref':sc['exact38_ref'],'target_tree_ref':ref(tr),'target_commit':sc['source_chain'][-1],
 'relative_path':'apps/control/main.go','git_row':row(tr.read_bytes(),'apps/control/main.go')})
attrs=ref(ROOT/'.gitattributes')
save('root-attributes-supplement.json',{'schema':'researchos.exact38-root-attributes-supplement.v1',
 'root_path':'.gitattributes','raw_ref':attrs,'base_tree_ref':ref(br),'target_tree_ref':ref(tr),
 'base_commit':sc['source_chain'][0],'target_commit':sc['source_chain'][-1],
 'git_row':row(tr.read_bytes(),'.gitattributes'),'original_protected_ref':sc['protected_ref']})
originalvector=load(Path(sc['protected_ref']['path']))
if any(Path(x['path'])==ROOT/'.gitattributes' for x in originalvector):raise ValueError('Root attrs unexpectedly already in vector')
save('protected.v2.json',originalvector+[attrs])
with (N/'controller.v1-v2.diff').open('xb') as f:
 f.write(''.join(difflib.unified_diff(original.decode('utf-8').splitlines(True),s.splitlines(True),fromfile='integrate_exact38.py',tofile='integrate_exact38.v2.py')).encode('utf-8'))
sc['controller_ref']=ref(N/'integrate_exact38.v2.py');sc['expected_registration']=[321,149,422]
sc['registration_namespace']='execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
sc['mode_supplement_ref']=ref(N/'single-mode-supplement.json');sc['root_attributes_supplement_ref']=ref(N/'root-attributes-supplement.json')
sc['protected_ref']=ref(N/'protected.v2.json')
sc['conditions']=[x.replace('321/149/421','321/149/422') for x in sc['conditions']]
sc['limitations']=[x.replace('vector:5172','vector:5173').replace('plus prior selected protection and formal snapshot.','plus prior selected protection, formal snapshot and exact root .gitattributes.') for x in sc['limitations']]
reviewdir=ROOT/'execution/v2.4/receipts/W05/W05-99/exact38_integration_controller_independent_review_codex/22c9358b53a4439d88c8230bab0cf477'
review=load(reviewdir/'review.json')
if ref(reviewdir/'review.json')['sha256']!='6857f4bbe96363996708b707943e89e3855a69e6cadcc58ad5fc2e92c6efc852':raise ValueError('Independent review drift')
if [x['id'] for x in review['requested_changes']]!=['I38-SR-01','I38-SR-02','I38-PRECONDITION-01']:raise ValueError('Unexpected review scope')
newrefs=[ref(reviewdir/x) for x in ['review.json','manifest.json','handoff.json','failure-origin.828f8b.json']]
sc['evidence_refs']+=newrefs
sc['pending_original_failures']+=[ref(reviewdir/'failure-origin.828f8b.json')]
sc['prelaunch_parent_rule']='Root future grant/prelaunch validates ancestor no alias/reparse and creates only fixed parent; UUID operation leaf remains absent for controller exclusive mkdir.'
sc['supplement_acceptance']='PREPARATION_ONLY. New independent scope/controller review must sign scope hash binding both supplements before any native call.'
save('scope.v2.proposed.json',sc)
save('static-derivation.json',{'original_ref':ref(source),'new_ref':ref(N/'integrate_exact38.v2.py'),'AST':'PARSED_ONLY_NOT_IMPORTED',
 'all_original_64hex_literals_unchanged':True,'original_vector_count':len(originalvector),'new_vector_count':len(originalvector)+1,
 'diff_ref':ref(N/'controller.v1-v2.diff'),'allowed_changes':['Only apps/control/main.go original no-mode row via exact pinned raw-tree supplement; other37 exactmode schema retained.',
 'Only literal original ROOT .gitattributes bytes and identical base/target Git blob; nested/info attributes remain rejected.',
 'Explicit321/149/422 registration and417->422 intent, original417 prefix retained.'],
 'controller_native_FF_import_execution':0,'new_failure_origins':[],'state':'PREPARATION_COMPLETE_STOPPED_PENDING_NONAUTHOR_REVIEW'})
rows=load(Path(mapref['path']))
keys37={'relative_path','git_blob','mode','path','sha256','bytes'}
if not all(set(x)==keys37 for x in rows if x['relative_path']!='apps/control/main.go'):raise ValueError('Unexpected other37 schema')
canon=[]
for name in ['checkpoint','path_ownership','step_state','commands']:
 p=ROOT/('execution/v2.4/'+name+'.json');raw=p.read_bytes();copy=N/('canonical.current.'+name+'.json')
 with copy.open('xb') as f:f.write(raw)
 canon.append({'canonical_path':str(p.relative_to(ROOT)),'current_ref':ref(p),'copy_ref':ref(copy)})
save('canonical.current.json',canon)
cp=load(N/'canonical.current.checkpoint.json');ow=load(N/'canonical.current.path_ownership.json')
save('input-binding-audit.json',{'current_tuple':[cp['revision'],ow['revision'],len(cp['failure_counters'])],
 'actual_Main_head_declared_by_checkpoint':cp['head'],'old_controller_ref':ref(source),'source_map_ref':mapref,
 'old_exact38_ref':sc['exact38_ref'],'raw_base_tree_ref':ref(br),'raw_target_tree_ref':ref(tr),
 'mode37_original_keysets_confirmed':True,'unique_supplemental_row':next(x for x in rows if x['relative_path']=='apps/control/main.go'),
 'root_attributes_current':attrs,'root_attributes_exact_bytes_hex':(ROOT/'.gitattributes').read_bytes().hex(),
 'root_attributes_base_target_same_git_row':row(br.read_bytes(),'.gitattributes')==row(tr.read_bytes(),'.gitattributes'),
 'review_refs':newrefs,'new_native_or_tool_failure_origins':[],'actual_Git_FF_tests_SQL_HTTP_models':0,
 'tool_trace_refs':[{'chunk_id':x,'actual_outer_exit':0} for x in ['d5392f','43b4fb','3bed38','5dc740']],
 'unchanged_limitations':['Same-user TOCTOU remains dependent on Root serial lease.','Python runtime is point-time, not complete lifecycle proof.',
 'Root must separately inspect prelaunch parent/noalias/exclusive leaf/finally failure recorder.','No actual authorization, native FF, source/formal acceptance.']})
save('handoff.json',{'status':'V2_PREPARATION_COMPLETE_STOPPED','controller_ref':ref(N/'integrate_exact38.v2.py'),
 'scope_ref':ref(N/'scope.v2.proposed.json'),'mode_supplement_ref':ref(N/'single-mode-supplement.json'),
 'attributes_supplement_ref':ref(N/'root-attributes-supplement.json'),'protected_v2_ref':ref(N/'protected.v2.json'),
 'static_derivation_ref':ref(N/'static-derivation.json'),'input_audit_ref':ref(N/'input-binding-audit.json'),
 'original_REQUEST_CHANGES_ref':newrefs[0],'old_review_manifest_ref':newrefs[1],
 'original_failed_auditor_ref':newrefs[-1],'current_tuple':[cp['revision'],ow['revision'],len(cp['failure_counters'])],
 'proposed_future_tuple':[321,149,422],'actual_controller_execution':False,'actual_product_execution':False,
 'new_failure_origins':[],'existing_pending_failures':5,'source_or_formal_acceptance':False,
 'next':'Root final v2 scope + independent controller/supplement/prelaunch review, actual new Root CAS and single grant required. No reuse of original v1 scope/grant.'})
members=[ref(p) for p in sorted(N.rglob('*')) if p.is_file()]
save('manifest.json',{'count':len(members),'entries':members,'excluded_only':str(N/'manifest.json')})
print(json.dumps({'namespace':str(N),'controller':ref(N/'integrate_exact38.v2.py'),'scope':ref(N/'scope.v2.proposed.json'),
 'handoff':ref(N/'handoff.json'),'manifest':ref(N/'manifest.json'),'member_count':len(members)},ensure_ascii=False))
