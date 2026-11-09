import ast,hashlib,json,os
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path(r'D:/作品集/ResearchOS/research-os')
M=O.parent.parent/'public23_to24_main_merge_preparation_codex/prepare-20261010-01'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=sha(b),bytes=len(b))
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 assert p.read_bytes()==b
 return pin(p)
def doc(p,v):return save(p,(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
session=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
with session.open('rb') as f:
 header=f.readline();size=os.fstat(f.fileno()).st_size
 start=max(0,size-4*1024*1024);f.seek(start)
 if start:f.readline()
 entries=[]
 while f.tell()<size:
  offset=f.tell();raw=f.readline()
  if not raw:break
  try:v=json.loads(raw)
  except ValueError:continue
  entries.append((offset,raw,v))
def texts(p):
 v=p.get('output',[])
 return v if isinstance(v,str) else '\n'.join(x.get('text','') for x in v if isinstance(x,dict))
def binding(needle,stem,existing=False):
 found=[x for x in entries if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type')=='custom_tool_call_output' and needle in texts(x[2]['payload']) and (not needle.startswith('SyntaxError:') or texts(x[2]['payload']).startswith('Script failed'))]
 assert len(found)==1,(stem,len(found))
 result=found[0];callid=result[2]['payload']['call_id']
 calls=[x for x in entries if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type')=='custom_tool_call' and x[2]['payload'].get('call_id')==callid]
 assert len(calls)==1
 call=calls[0];p=O/('diagnostics/'+stem+'.actual-3lf.jsonl')
 if existing:assert p.read_bytes()==header+call[1]+result[1];rawref=pin(p)
 else:rawref=save(p,header+call[1]+result[1])
 return dict(call_id=callid,actual_call=call[2]['payload'],actual_result=result[2]['payload'],raw_capture_ref=rawref,source_session_path=str(session),source_snapshot_bytes=size,source_session_header_sha256=sha(header),source_call_range=dict(offset=call[0],bytes=len(call[1]),sha256=sha(call[1])),source_result_range=dict(offset=result[0],bytes=len(result[1]),sha256=sha(result[1])))
b=binding("SyntaxError: Unexpected identifier 'aede0678'",'js-compile-rejection',True)
b.update(schema='researchos.actual-js-tool-rejection.v1',original_ordinal=1256,toolname='functions.exec',actual_outer_exit=None,actual_Python_exit=None,actual_Native_exit=None,actual_SQL_exit=None,process_started=False,mutations_started=False)
doc(O/'diagnostics/original-1256.binding.json',b)
b=binding('"chunk_id":"5f6da1"','tool-5f6da1')
b.update(schema='researchos.actual-tool-diagnostic-binding.v1',original_ordinal=None,ordinal_assignment='PENDING_ROOT_ALLOCATION',chunk_id='5f6da1',actual_outer_exit=1,actual_Python_exit=1,actual_Native_exit=None,actual_SQL_exit=None,reason='Seal metadata prefix succeeded; duplicate actual_result keyword failed while constructing diagnostic1256 binding. Existing prefix artifacts preserved; delta seal writes only missing documents.')
doc(O/'diagnostics/tool-5f6da1.binding.json',b)
b=binding('"chunk_id":"80fd5e"','tool-80fd5e')
b.update(schema='researchos.actual-tool-diagnostic-binding.v1',original_ordinal=None,ordinal_assignment='PENDING_ROOT_ALLOCATION',chunk_id='80fd5e',actual_outer_exit=1,actual_Python_exit=1,actual_Native_exit=None,actual_SQL_exit=None,reason='Ambiguous substring matched actual JS rejection plus later traceback quoting it; uniqueness refused before any new writes. New continuation narrows actual returned text prefix.')
doc(O/'diagnostics/tool-80fd5e.binding.json',b)
helper=pin(O/'compose_main24.source.py')
controls=json.loads((O/'new-pure-controls.json').read_bytes())
assert controls['source_ref']==helper and controls['status']=='PASS'
merge=pin(M/'file-merge-map.json')
hdf=dict(schema='researchos.main24-composition-helper-handoff.v1',status='SOURCE_AUTHORED_PENDING_INDEPENDENT_REVIEW',author='codex:/root/attach_restore_independent_review',source_helper_ref=helper,merge_map_ref=merge,contract_ref=pin(O/'ROOT-EXECUTION-CONTRACT.md'),request_template_ref=pin(O/'request.template.json'),grant_template_ref=pin(O/'grant.template.json'),future_result_template_ref=pin(O/'future-result.template.json'),new_pure_controls_ref=pin(O/'new-pure-controls.json'),targets=40,existing_increment_targets=10,new_absent_only_targets=30,selected_native_revision='b1599aaf259c435db5a0a5313ab0ea65',prepare_executed=False,apply_executed=False,Main_Canon_writes=0,Go_SQL_Native_product_calls=0,prior_successful_Source_controls_replayed=0,execution_grant_ref=None,TargetProgram=None,build_result_ref=None,test_result_ref=None,formal_acceptance=False,diagnostic_refs=[pin(p) for p in sorted((O/'diagnostics').glob('*.json'))],diagnostic_limit='1253/1256 and actual failed chunks5f6da1/80fd5e raw originals captured; 1254/1255 exact observed tool arguments/results retained, original callids/3LF unavailable and not asserted.',manifest_exclusions=['MF.json','postseal-tool-io.json'],required_next='Root independent Source review; Root metadata preparation and explicit qualified grant before apply.')
h=doc(O/'HDF.json',hdf)
members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ('MF.json','postseal-tool-io.json')]
mf=doc(O/'MF.json',dict(schema='researchos.source-package-manifest.v1',status='SEALED_SOURCE_ONLY',HDF_ref=h,files=members,exclusions=['MF.json','postseal-tool-io.json'],self_hash_not_embedded=True))
print(json.dumps(dict(HDF_ref=h,MF_ref=mf,source_helper_ref=helper,new_pure_controls_ref=pin(O/'new-pure-controls.json'),contract_ref=pin(O/'ROOT-EXECUTION-CONTRACT.md'),diagnostics=hdf['diagnostic_refs'],status=hdf['status']),ensure_ascii=True))

