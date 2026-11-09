"""Append-only independent v3 re-review; all fixtures stay in review scope."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
OUT = Path(__file__).resolve().parent
REPO = next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
SOURCE=REPO/'execution/v2.4/receipts/W09/W09-99/resume_cp398_formal_audit_codex/20261012-current-chat'
CAND=REPO/'.local/candidates/w09-header-recovery-20261012-v3'
def ref(p):
    raw=p.read_bytes()
    return {'path':p.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
manifest_path=SOURCE/'candidate-v3-manifest.json'
assert ref(manifest_path)['sha256']=='733040391f84840d7738e5a33348b9a952bfcbaf59eb42cbaba5504fb0716e30'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
for item in manifest['files']:
    assert ref(REPO/item['frozen_ref']['path'])==item['frozen_ref']
    assert ref(Path(item['candidate_path']))['sha256']==item['sha256']
cert_ref=ref(REPO/manifest['certificate_ref']['path'])
assert cert_ref==manifest['certificate_ref']
cert=json.loads((REPO/cert_ref['path']).read_text(encoding='utf-8'))
prior=json.loads((SOURCE/'header-correction.candidate-v2.json').read_text(encoding='utf-8'))
assert {k for k in cert if cert[k]!=prior[k]}=={'created_at','new_profile_ref'}
for version in ('v2','v3'):
    assert ref(SOURCE/f'candidate-{version}-source/w09_header_correction.py')['sha256']==cert['verifier_module_ref']['sha256']
assert ref(REPO/cert['old_profile_ref']['path'])['sha256']==cert['old_profile_ref']['sha256']
assert ref(REPO/cert['index_ref']['path'])['sha256']==cert['index_ref']['sha256']
assert not (REPO/'execution/v2.4/w09_header_correction.py').exists()
def methods(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(path.read_text(encoding='utf-8')))
            if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
old_methods=methods(SOURCE/'candidate-v2-source/test_header_correction.py')
new_methods=methods(CAND/'tests/test_header_correction.py')
assert len(old_methods)==22 and len(new_methods)==26
assert all(new_methods[k]==v for k,v in old_methods.items())
path=CAND/'tests/test_header_correction.py'
text=path.read_text(encoding='utf-8').replace('scratch = CANDIDATE / "tests" /','scratch = REVIEW_OUT /').replace('repo = CANDIDATE / "tests" /','repo = REVIEW_OUT /')
ns={'__file__':str(path),'__name__':'independent_v3_suite','REVIEW_OUT':OUT}
exec(compile(text,str(path),'exec'),ns)
log=io.StringIO()
result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['CorrectionControls']))
(OUT/'v3-candidate26-tests.txt').write_text(log.getvalue(),encoding='utf-8')
assert result.wasSuccessful() and result.testsRun==26
base=ns['CorrectionControls'];base.setUpClass()
api,helper,profile=base.api,base.m,base.profile
outcomes=[]
def reject(name,fn):
    try: fn()
    except api.InvalidEvidence as exc:
        outcomes.append({'name':name,'status':'PASS','rejection':exc.code})
    else: raise AssertionError(name+' was accepted')
# The full original independent v2 exploit was already frozen; author new tests
# exercise the same fixed-path/empty-review exploit with the real v2 and v3 sources.

context=json.loads(base.roots['context'].read_text(encoding='utf-8'))
changed=copy.deepcopy(context)
next(r for r in changed['version_vector']['source_files'] if r['path'].startswith('internal/domain/'))['sha256']='0'*64
reader=api.Reader(REPO);reader.w09_header_correction={'certificate':cert}
reject('unchanged_business_source_gate',lambda:profile['_vector'](api,reader,changed))

# Select an ACTUAL current-chat rejection delivery from this reviewer. It cannot
# be upgraded to v3 approval by forging only a review claim. No capture is written.
messages=[]
with Path(helper['CURRENT_LOG']).open('rb') as f:
    header=f.readline();previous=(0,header)
    while True:
        offset=f.tell();line=f.readline()
        if not line: break
        try: event=json.loads(line)
        except json.JSONDecodeError: previous=(offset,line);continue
        payload=event.get('payload',{})
        if event.get('type')=='response_item' and payload.get('type')=='agent_message' and payload.get('author')=='/root/w09_header_gate_review':
            if json.loads(previous[1]).get('type')=='inter_agent_communication_metadata':
                messages.append((previous,(offset,line),payload.get('id')))
        previous=(offset,line)
assert messages
meta,message,message_id=messages[-1]
lines=[header,meta[1],message[1]];raw=b''.join(lines)
class MemoryPath:
    def __init__(self,raw):self.raw=raw
    def stat(self):return SimpleNamespace(st_size=len(self.raw))
    def read_bytes(self):return self.raw
capture={'schema':'researchos.w09.correction-review-delivery.v1','source_audit_path':helper['CURRENT_LOG'],
 'thread_id':helper['CURRENT_THREAD'],'original_capture_ref':{'path':helper['PREFIX']+'memory-only-original',
 'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'source_line_offsets':[0,meta[0],message[0]],
 'original_line_sha256':[hashlib.sha256(x).hexdigest() for x in lines]}
capture_bytes=json.dumps(capture).encode()
capture_ref={'path':helper['PREFIX']+'memory-only-descriptor','sha256':hashlib.sha256(capture_bytes).hexdigest(),'bytes':len(capture_bytes)}
class MemoryReader:
    def ref(self,ref,prefix=None):return MemoryPath(capture_bytes if ref['path']==capture_ref['path'] else raw)
    def read(self,path):return json.loads(path.read_bytes())
    w09_audit_ranges=[]
review={'reviewer_id':'/root/w09_header_gate_review','issued_at':cert['created_at']}
reject('actual_current_rejection_cannot_be_forged_into_approval',lambda:helper['_review_delivery'](api,MemoryReader(),cert_ref,{'sha256':'0'*64},review,capture_ref))
review['reviewer_id']='/root/forged_reviewer'
reject('actual_current_delivery_cannot_impersonate_other_reviewer',lambda:helper['_review_delivery'](api,MemoryReader(),cert_ref,{'sha256':'0'*64},review,capture_ref))
capture['thread_id']=helper['OLD_THREAD']
capture_bytes=json.dumps(capture).encode();capture_ref['bytes']=len(capture_bytes)
reject('old_thread_current_delivery_claim_refused',lambda:helper['_review_delivery'](api,MemoryReader(),cert_ref,{'sha256':'0'*64},review,capture_ref))
summary={'schema':'researchos.independent-source-controls.v1','reviewer_id':'/root/w09_header_gate_review',
 'candidate26_passed':True,'original22_ast_unchanged':True,'helper_bytes_unchanged':True,
 'certificate_semantic_changes':['created_at','new_profile_ref'],'actual_header_ranges_checked':18,
 'additional_controls':outcomes,'actual_negative_delivery_id':message_id,
 'manifest_ref':ref(manifest_path),'certificate_ref':cert_ref,
 'native_or_consumer_calls':False,'main_or_canon_writes':False,'generated_capture_or_approval':False}
(OUT/'v3-controls-result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
