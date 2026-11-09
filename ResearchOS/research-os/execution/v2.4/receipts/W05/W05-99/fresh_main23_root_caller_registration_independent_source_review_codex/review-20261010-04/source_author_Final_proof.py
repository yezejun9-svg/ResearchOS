"""Real author delivery identity and four Source pins; not a review/grant."""
import hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent;W=D.parent.parent
S=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
R=W.parent.parent/'W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
G=W/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
def load(p,n):
 m=types.ModuleType(n);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
 raw=pin(R/'main23.v4.peer.source-author.raw.jsonl');binding=pin(R/'main23.v4.peer.source-author.binding.root.json')
 assert (raw['sha256'],raw['bytes'])==('17f853f1d58e3a26a7c568e115c0240891cf33455aa5093b814aeac45657a950',25008)
 assert (binding['sha256'],binding['bytes'])==('21b20c04e602605f837e9c9fb972fef3fa9bf9c8362584e6909b65d200c4a43a',1211)
 m=load(S/'main23_root.source.py','real_Source_author_inert');refs=[raw,binding,pin(__file__),pin(G),*[pin(S/n) for n in ('HDF.json','MF.json','main23_root.source.py','root-calling-contract.source.json')]]
 guard=m.guard_primitives().SourceReadGuard()
 try:
  guard.acquire(refs);b=m.doc(binding);meta,last=m.original_capture_rows(b,m.checked(raw),peer=True);p=last['payload']
  assert meta['type']=='inter_agent_communication_metadata' and type(meta['payload']['trigger_turn']) is bool
  assert last['ordinal']==meta['ordinal']+1==61496 and meta['timestamp']==last['timestamp']
  assert p['type']=='agent_message' and p['author']==m.CALLER_AUTHOR.removeprefix('codex:') and p['recipient']=='/root' and last['metadata']['client_authored'] is False
  assert b['peer_actor']==m.CALLER_AUTHOR and b['message_id']==p['id'] and b['received_at']==last['timestamp']
  text=p['content'][0]['text'];prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/backup_regression_resources\nPayload:\n'
  assert text.startswith(prefix) and text.count('```json\n')==1
  # Author presentation is a code fence. This parser is solely author identity
  # evidence and is never substituted for validate_peer_delivery strict JSON.
  body=text.split('```json\n',1)[1].split('\n```',1)[0];delivered=m.strict(body)
  expected={k:pin(S/n) for k,n in [('HDF_ref','HDF.json'),('MF_ref','MF.json'),('caller_ref','main23_root.source.py'),('contract_ref','root-calling-contract.source.json')]}
  assert set(delivered)==set(expected) and all(m.same_ref(delivered[k],expected[k]) for k in expected)
  assert m.doc(expected['HDF_ref'])['actual_Source_identity']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
 finally:closed=guard.close();cr=save('Source-author-FINAL-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 result=save('actual-Source-author-FINAL-proof.json',dict(schema='researchos.main23-M4-real-Source-author-final-proof.v1',status='PASS_SOURCE_IDENTITY_ONLY',checks=4,author=m.CALLER_AUTHOR,source_thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',Root_thread_id=m.ROOT_THREAD,actual_ordinal=61496,raw_ref=raw,binding_ref=binding,full_delivered_Source_refs=delivered,original_source_offsets_verified=True,actual_backend_identity_verified=True,author_format_is_not_peer_review_decoder_input=True,Source_guard_ref=cr,retained_handles_count=0,execution_grant=False,formal_acceptance=False))
 print(json.dumps(dict(result_ref=result,guard_ref=cr,checks=4,retained_handles_count=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
