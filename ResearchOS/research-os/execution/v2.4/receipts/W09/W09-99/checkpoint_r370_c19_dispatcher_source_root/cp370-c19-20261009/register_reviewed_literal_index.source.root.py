"""Root index-slot CAS: historical slot is data; current index is a file pin."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys,types
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';S=Path(__file__).resolve().parent;RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
B=V/'receipts/W05/W05-99';W=V/'receipts/W09/W09-99'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,d):
 with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
 return pin(p)
def module(p,n,d):
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==d;m=types.ModuleType(n);m.__file__=str(p);sys.modules[n]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
def transform_value(cp,ow,old,new,core,now):
 assert cp['work_in_progress']['w09_root_delivery_capture_index_ref']==old
 after=copy.deepcopy(cp);ops=[]
 for path,value in [(['work_in_progress','w09_root_delivery_capture_index_ref'],new),(['revision'],cp['revision']+1),(['expected_previous_revision'],cp['revision']),(['updated_at'],now),(['updated_by'],'codex:/root')]:
  exists,before=core.value_at(after,path);ops.append(dict(path=path,before_exists=exists,before=copy.deepcopy(before),after=copy.deepcopy(value)));core.put(after,path,value)
 assert core.inverse_operations(after,ops)==cp
 return after,copy.deepcopy(ow),ops
def main():
 assert len(sys.argv)==2 and sys.argv[1]=='root-register-exact-reviewed-index'
 cp=pin(V/'checkpoint.json');ow=pin(V/'path_ownership.json');assert cp['sha256']=='f785c7face581a574e34d78699cc3540c5117be2a363a21b08e9c7bb7b3ec8a5' and ow['sha256']=='b949831cc4827ae2cadae77235188dfff0776a0c8074a57714c1445e16c32a86'
 index=V/'root_delivery_captures/W09/W09-99/index.json';current=pin(index);assert current['sha256']=='6bdb7a703934007dae8e50e368d0e41b00b4a132ba5998158255881c21ed520d' and current['bytes']==1340
 oldpath=RUN/'literal02-fixed-publication.root/index.before.raw.json';oldpin=pin(oldpath);assert oldpin['sha256']=='ce0424c83c54d08e82682382be3fbdd1c856fff8c2f697b8104a5a761962d9cb' and oldpin['bytes']==756
 before=json.loads(oldpath.read_bytes());after=json.loads(index.read_bytes());assert after['entries'][:-1]==before['entries'] and len(after['entries'])==len(before['entries'])+1
 old=dict(oldpin,path=index.relative_to(R).as_posix());new=dict(current,path=index.relative_to(R).as_posix())
 proposal=RUN/'capture-7d7d176970554ad3b9cdb72bc3b1ce8a/root-corrected-publication01/result.json';assert pin(proposal)['sha256']=='04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8'
 pub=W/'w09_capture_literal_actual_publication_independent_review_codex/review-20261010-01-full/review-decision.json';assert pin(pub)['sha256']=='1e71d800b2eec0599f9f38fff3d0297461f4b4adb39a06ba0f002d32d9389af1'
 audit=S/'w09.literal-publication-actual-review01.actual-audit.root.json';assert pin(audit)['sha256']=='1cc4e9076b85fb86555fbc629668759e80046c1ac51e0fbd2ff744840a9106be'
 runtime=module(W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py','root_literal_register_audit','1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08')
 proofs=runtime.actual_audit(pin(audit),'codex:/root/full_w09_source_review',pin(pub)['sha256'])
 snapshot=[pin(V/'step_state.json'),pin(V/'commands.json')];refs=[pin(TP),pin(G),pin(CORE),pin(index),pin(oldpath),pin(proposal),pin(pub),pin(audit),pin(Path(__file__)),*snapshot,*proofs]
 for entry in after['entries']:
  for key in ('capture_ref','origin_ref'):
   ref=entry[key];p=R/ref['path'];actual=pin(p);assert (actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes']);refs.append(actual)
 refs=list({str(Path(x['path'])):dict(x,path=str(Path(x['path']))) for x in refs}.values())
 out=S/'cp398-literal-index-reviewed-registration';assert not out.exists();out.mkdir();(out/'canonical-journal').mkdir()
 guard=module(G,'root_literal_register_guard','e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
 try:
  guard.acquire(refs);core=module(CORE,'root_literal_register_core','2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f');tp=module(TP,'root_literal_register_tp','094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9')
  def transform(c,o):
   result,unchanged,ops=transform_value(c,o,old,new,core,datetime.now(timezone.utc).isoformat())
   save(out/'complete-changes-and-inverse.root.json',dict(checkpoint_operations=ops,ownership_operations=[],complete_structural_inverse=True,historical_slot_ref=old,current_file_ref=new,Canon_counter_reset=False))
   return result,unchanged
  result=tp.update_pair([cp,ow],transform,str(out/'canonical-journal'),'activate');receipt=save(out/'committed.root.json',dict(result,registered_index_ref=new,old_index_archive_ref=oldpin,SS_written=False,formal_acceptance=False))
 finally:closed=guard.close();gr=save(out/'source-guard.closed.root.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors'] and snapshot==[pin(V/'step_state.json'),pin(V/'commands.json')]
 print(json.dumps(dict(receipt_ref=receipt,guard_ref=gr,current4=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
