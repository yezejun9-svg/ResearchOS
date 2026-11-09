"""Receipt-only exact derivation. Does not import or run either controller."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT=Path('D:/作品集/ResearchOS/research-os')
OLD=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_integration_preparation_codex/a05d7d012d004f92b5e932e35038bf65'
N=Path(__file__).parent
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(name,d):
    with (N/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def tree(raw):
    result={}
    for line in raw.split(b'\0'):
        if line:
            h,p=line.split(b'\t',1);mode,kind,blob=h.decode('ascii').split()
            result[p.decode('utf-8')]={'mode':mode,'kind':kind,'blob':blob}
    return result

oldpath=OLD/'integrate_cli8.py';raw=oldpath.read_bytes()
if ref(oldpath)['sha256']!='1b43858e4a678f97d1afd409b835cb8e5eeef39065a98051e30dd5e03d750587':raise ValueError('Original controller pin')
if b'\r\n' in raw or raw.count(b'\n')!=414:raise ValueError('Original newline differs from actual09e71b')
old=raw.decode('utf-8')
before="""        attrs={ROOT/'.git/info/attributes',ROOT/'.gitattributes'}
        for item in exact:
            p=(ROOT/item['path']).parent
            while p!=ROOT:attrs.add(p/'.gitattributes');p=p.parent
        for p in attrs:
            if p.exists():require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()), 'Checkout attributes need scope')
"""
after="""        attribute_proof=document(scope['root_attributes_proof_ref'])
        require(set(attribute_proof)=={'schema','base_commit','cli_commit','base_tree_ref','cli_tree_ref','raw_ref','git_row'} and
                attribute_proof['schema']=='researchos.cli8-original-root-attributes-proof.v1' and
                attribute_proof['base_commit']==BASE and attribute_proof['cli_commit']==CLI,
                'Only the original root attribute proof is allowed')
        attribute_ref=attribute_proof['raw_ref']
        require(bounded(attribute_ref['path'])==ROOT/'.gitattributes' and
                attribute_ref['sha256']=='705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da' and
                attribute_ref['bytes']==8,'Exact root attribute identity')
        attribute_raw=verify(attribute_ref)
        require(attribute_raw==b'* -text\\n','Original root attribute bytes')
        attribute_row={'mode':'100644','kind':'blob','blob':'fa1385d99a319b43c06f5309d1aae9fdd3adea46'}
        require(attribute_proof['git_row']==attribute_row and
                tree(verify(attribute_proof['base_tree_ref']))['.gitattributes']==attribute_row and
                tree(verify(attribute_proof['cli_tree_ref']))['.gitattributes']==attribute_row and
                base_tree['.gitattributes']==old_tree['.gitattributes']==attribute_row and
                hashlib.sha1(b'blob '+str(len(attribute_raw)).encode()+b'\\0'+attribute_raw).hexdigest()==attribute_row['blob'],
                'Root attributes must retain the exact base/candidate Git blob')
        attribute_pins=[x for x in protected if path(x['path']).absolute()==ROOT/'.gitattributes']
        require(len(attribute_pins)==1 and attribute_pins[0]['sha256']==attribute_ref['sha256'] and
                attribute_pins[0]['bytes']==attribute_ref['bytes'],'Root attributes absent from immutable protected vector')
        attrs={ROOT/'.git/info/attributes',ROOT/'.gitattributes'}
        for item in exact:
            p=(ROOT/item['path']).parent
            while p!=ROOT:attrs.add(p/'.gitattributes');p=p.parent
        for p in attrs:
            if p.exists():
                if p==ROOT/'.gitattributes':
                    require(read(p)==verify(attribute_ref)==attribute_raw,'Original root attribute bytes changed')
                else:
                    require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()), 'Checkout attributes need scope')
"""
if old.count(before)!=1:raise ValueError('Exact LF attribute span must occur once')
new=old.replace(before,after,1)
ast.parse(old);parsed=ast.parse(new)
original_hashes=re.findall(r'[0-9a-f]{64}',old);new_hashes=re.findall(r'[0-9a-f]{64}',new)
if not all(new_hashes.count(x)>=original_hashes.count(x) for x in set(original_hashes)):raise ValueError('Original64hex literals changed')
if new.replace(after,before,1)!=old:raise ValueError('Reverse exact derivation failed')
attrs=(ROOT/'.gitattributes').read_bytes()
if attrs!=b'* -text\n':raise ValueError('Current root attribute bytes changed')
bt=tree((OLD/'tree-a5.stdout.raw').read_bytes());ct=tree((OLD/'tree-cli.stdout.raw').read_bytes())
row={'mode':'100644','kind':'blob','blob':'fa1385d99a319b43c06f5309d1aae9fdd3adea46'}
if bt['.gitattributes']!=row or ct['.gitattributes']!=row:raise ValueError('Sealed tree proof differs')
paths=load(OLD/'protected-public-paths.planned.json')
if paths.count('.gitattributes')!=1:raise ValueError('Original planned protection must already contain root attributes exactly once')
with (N/'integrate_cli8.v2.py').open('xb') as f:f.write(new.encode('utf-8'))
with (N/'controller.v1-v2.diff').open('xb') as f:f.write(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='integrate_cli8.py',tofile='integrate_cli8.v2.py')).encode('utf-8'))
save('root-attributes-proof.json',{'schema':'researchos.cli8-original-root-attributes-proof.v1',
 'base_commit':'a5d6d16ffaf129de0361470c3a1570228bd259a2','cli_commit':'b98738ac093ea55bb8700cfa724ddd9e6b2a1251',
 'base_tree_ref':ref(OLD/'tree-a5.stdout.raw'),'cli_tree_ref':ref(OLD/'tree-cli.stdout.raw'),
 'raw_ref':ref(ROOT/'.gitattributes'),'git_row':row})
scope=load(OLD/'scope.proposed.json')
scope['controller_ref']=ref(N/'integrate_cli8.v2.py');scope['root_attributes_proof_ref']=ref(N/'root-attributes-proof.json')
scope['supersedes_preparation_only_ref']=ref(OLD/'scope.proposed.json')
scope['attributes_amendment']='Allow only pinned literal root * -text LF bytes with same a5/CLI Git mode/blob and mandatory protected-vector row. All other nested/info/global attributes and filter/include rules unchanged.'
save('scope.v2.proposed.json',scope)
canon=[]
for name in ['checkpoint','path_ownership','step_state','commands']:
    p=ROOT/('execution/v2.4/'+name+'.json');b=p.read_bytes();q=N/('canonical.current.'+name+'.json')
    with q.open('xb') as f:f.write(b)
    canon.append({'canonical_path':str(p.relative_to(ROOT)),'current_ref':ref(p),'copy_ref':ref(q)})
save('canonical.current.json',canon)
cp=load(N/'canonical.current.checkpoint.json');ow=load(N/'canonical.current.path_ownership.json')
failure=ROOT/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/revision-v2-ed1a1dab301a40b293dd6a177980cfaf/failure-origin.df6aba.json'
save('static-audit.json',{'AST':'PARSED_ONLY_NOT_IMPORTED','AST_nodes':sum(1 for _ in ast.walk(parsed)),
 'original_LF':414,'original_CRLF':0,'exact_single_span_replacement':True,'reverse_exact_derivation':True,
 'all_original64hex_literals_retained':True,'all_other_controller_bytes_unchanged':True,
 'original_scope_ref':ref(OLD/'scope.proposed.json'),'original_manifest_ref':ref(OLD/'manifest.json'),
 'original_controller_ref':ref(oldpath),'new_controller_ref':ref(N/'integrate_cli8.v2.py'),
 'actual_current_canonical_tuple':[cp['revision'],ow['revision'],len(cp['failure_counters'])],
 'future_registration_explicit_only':True,'future_expected_registration':None,
 'actual_new_Git_queries':0,'actual_candidate_import_or_execution':0,'actual_Go_SQL_HTTP_SDK_model':0,
 'existing_df6aba_origin_preserved_ref':ref(failure),'df6aba_is_not_new_again':True,'new_failure_origins':[],
 'read_tool_trace':[{'chunk':'09e71b','actual_outer_exit':0},{'chunk':'b51778','actual_outer_exit':0}],
 'semantics_unchanged':{'owned_paths':8,'shared_handler38':3,'additional_changed_paths':5,'new_file_absence_claims':0,'combined_unique_paths':43},
 'authority_still_missing':['Actual Main38 FF closed manifest/review and forward cp.head=a5','New explicit Root CLI registration/independent controller review/once grant','Fresh actual protected Main a5 public vector/status','Root owned outer launcher contract'],
 'acceptance':False})
save('handoff.json',{'state':'CLI8_V2_PREPARATION_COMPLETE_STOPPED','author':'codex:/root/command_queue_impl',
 'controller_ref':ref(N/'integrate_cli8.v2.py'),'scope_ref':ref(N/'scope.v2.proposed.json'),
 'attributes_proof_ref':ref(N/'root-attributes-proof.json'),'static_audit_ref':ref(N/'static-audit.json'),
 'diff_ref':ref(N/'controller.v1-v2.diff'),'original_handoff_ref':ref(OLD/'handoff.json'),'original_manifest_ref':ref(OLD/'manifest.json'),
 'existing_df6aba_origin_ref':ref(failure),'new_failure_origins':[],'candidate_executed':False,
 'source_canonical_index_writes':0,'source_or_product_acceptance':False,'formal_increment':0,
 'limits':'Exact same future one apply/index8/one source commit only. Fresh43 compiler/2held rows/Desktop/provider remain separate unauthorised scopes.',
 'next':'Root independently reviews concrete v2 controller/scope, freezes future explicit registration and actual Main38 closure; no execution under this preparation.'})
members=[ref(p) for p in sorted(N.rglob('*')) if p.is_file()]
save('manifest.json',{'count':len(members),'entries':members,'excluded_only':str(N/'manifest.json')})
print(json.dumps({'controller':ref(N/'integrate_cli8.v2.py'),'scope':ref(N/'scope.v2.proposed.json'),'handoff':ref(N/'handoff.json'),'manifest':ref(N/'manifest.json'),'manifest_count':len(members)},ensure_ascii=False))
