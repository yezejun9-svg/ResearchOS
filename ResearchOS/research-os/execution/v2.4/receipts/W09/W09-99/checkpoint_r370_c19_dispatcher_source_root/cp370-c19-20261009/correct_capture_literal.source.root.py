"""Create fresh Root publication payloads, retaining every Source proposal byte."""
from pathlib import Path
import copy,hashlib,json,os,sys
R=Path(r'D:\作品集\ResearchOS\research-os')
MAIN=R/'execution/v2.4/formal_profile_w09.py'
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def checked(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes()
 assert hashlib.sha256(b).hexdigest()==ref['sha256'] and ('bytes' not in ref or len(b)==ref['bytes'])
 return b
def save(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def correct(proposal,capture,index,issuance,literal):
 old=copy.deepcopy(capture);capture=copy.deepcopy(capture)
 assert capture['source_audit_path']==str(Path(literal)) and capture['source_audit_path']!=literal
 capture['source_audit_path']=literal
 inverse=copy.deepcopy(capture);inverse['source_audit_path']=old['source_audit_path'];assert inverse==old
 assert Path(literal).is_absolute() and Path(literal).is_file()
 return capture
def main():
 assert len(sys.argv)==5
 ref=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]));out=Path(sys.argv[4])
 assert out.is_absolute() and out.resolve().is_relative_to(R/'execution/v2.4/receipts/W09/W09-99') and not out.exists()
 main_raw=MAIN.read_bytes();assert hashlib.sha256(main_raw).hexdigest()=='1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087'
 import ast
 tree=ast.parse(main_raw)
 values=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROOT_SOURCE_AUDIT_LOG' for t in n.targets)]
 assert len(values)==1;literal=values[0]
 proposal=json.loads(checked(ref));assert proposal['schema']=='researchos.w09-capture-publication-proposal.v1'
 capture=json.loads(checked(proposal['capture_payload_ref']));index=json.loads(checked(proposal['payload_ref']));issuance=json.loads(checked(proposal['issuance_ref']))
 corrected=correct(proposal,capture,index,issuance,literal)
 event=capture['message_id'];entries=[x for x in index['entries'] if x['event_id']==event];assert len(entries)==1
 oldentry=copy.deepcopy(entries[0]);assert oldentry['capture_ref']==issuance['delivery_ref'] and oldentry['origin_ref']==issuance['origin_event_ref']
 original=checked(proposal['origin_payload_ref']);lines=original.splitlines(keepends=True);assert len(lines)==3
 assert [hashlib.sha256(x).hexdigest() for x in lines]==capture['original_line_sha256']
 events=[json.loads(x) for x in lines];assert events[1]['timestamp']==events[2]['timestamp'] and events[2]['ordinal']==events[1]['ordinal']+1
 assert events[2]['payload']['id']==event and events[2]['payload']['author']==issuance['issuer_id']=='/root/backup_regression_resources' and events[2]['metadata']['client_authored'] is False
 with Path(literal).open('rb') as f:
  for off,line in zip(capture['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
 out.mkdir();cp=save(out/'capture.proposed.json',encoded(corrected));fixed=dict(cp,path=proposal['capture_fixed_path'])
 newindex=copy.deepcopy(index);next(x for x in newindex['entries'] if x['event_id']==event)['capture_ref']=fixed
 inverse=copy.deepcopy(newindex);next(x for x in inverse['entries'] if x['event_id']==event)['capture_ref']=oldentry['capture_ref'];assert inverse==index
 newissuance=copy.deepcopy(issuance);newissuance['delivery_ref']=fixed;inverse=copy.deepcopy(newissuance);inverse['delivery_ref']=issuance['delivery_ref'];assert inverse==issuance
 ip=save(out/'index.proposed.json',encoded(newindex));issue=save(out/'issuance.json',encoded(newissuance))
 newproposal=copy.deepcopy(proposal);newproposal.update(capture_payload_ref=cp,payload_ref=ip,issuance_ref=issue)
 result=save(out/'result.json',encoded(newproposal))
 closure=save(out/'repair.closed.json',encoded(dict(schema='researchos.w09-root-publication-literal-correction.v1',original_proposal_ref=ref,result_ref=result,Main_ref=dict(path=str(MAIN),sha256=hashlib.sha256(main_raw).hexdigest(),bytes=len(main_raw)),changed_capture_field='source_audit_path',from_value=capture['source_audit_path'],to_value=literal,complete_structural_inverse=True,original_3LF_unchanged=True,prior_index_entries_unchanged=True,Canon_written=False,Native_replayed=False,formal_review_replayed=False)))
 assert MAIN.read_bytes()==main_raw
 print(json.dumps(dict(result_ref=result,repair_ref=closure,formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
