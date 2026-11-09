"""Correct the review-only packet count: 486 owned files plus four run files.
The immutable initial review and all actual consumer evidence remain preserved.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('closeout_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m

def main():
 old=read(N/'actual-decision.json');controls=read(N/'actual-checks.json');oldguard=read(N/'sourceguard.closed.json');oldh=read(N/'HDF.json');oldmf=read(N/'MF.json')
 assert len(controls['blocking_findings'])==1 and controls['blocking_findings'][0]['name']=='all486 native original and486 archive members held'
 original_refs=[{k:e[k] for k in ('path','sha256','bytes')} for e in oldguard['entries']]
 extra=[pin(N/name) for name in ('actual-decision.json','actual-checks.json','sourceguard.closed.json','HDF.json','MF.json','closeout.py')]
 extra.extend(oldmf['members'])
 request=read(old['root_request_ref']['path']);sh=read(request['source_hdf_ref']['path']);caller=mod(sh['caller_source_ref']['path'])
 rh=read(N.parent.parent/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4/HDF.json');registrar=mod(rh['registrar_ref']['path'])
 held,count=registrar.held_guard([*original_refs,*extra],False)
 try:
  handoff=read(request['native_handoff_ref']['path']);packet=read(handoff['native_packet_ref']['path'])
  inventory=caller.packet_inventory(packet)
  run=Path(packet['original_report_ref']['path']).parent
  pairs=packet['raw_copy_mapping'];runfiles=[x for x in pairs if Path(x['original_ref']['path']).parent==run]
  owned=[x for x in pairs if (run/'owned') in Path(x['original_ref']['path']).parents]
  actualguard=read(old['caller_closed_ref']['path'])['source_guard_cleanup']
  table={e['path'].casefold():{k:e[k] for k in ('path','sha256','bytes')} for e in actualguard['entries']}
  assert len(pairs)==490 and len(owned)==486 and len(runfiles)==4 and len(inventory)==980
  assert {Path(x['original_ref']['path']).name for x in runfiles}=={'go-test.stdout.jsonl','go-test.stderr.txt','native-tool-run.json','report.json'}
  assert all(table.get(r['path'].casefold())==r for r in inventory)
  for ref in [*original_refs,*extra]:assert pin(ref['path'])==ref
  for name in ('two-consumers','registration-review-seal','failure-a7cd3a'):
   binding=read(N/(name+'.actual-host.binding.json'));raw=Path(binding['actual_capture_ref']['path']).read_bytes().splitlines(keepends=True)
   with Path(binding['source_audit_path']).open('rb') as f:
    for i,(offset,size,expected) in enumerate(zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256'])):
     f.seek(offset);b=f.read(size);assert b==raw[i] and hashlib.sha256(b).hexdigest()==expected
  assert [pin(r['path']) for r in old['current_canonical_refs']]==old['current_canonical_refs']
 finally:
  cleanup=held.close();cleanup_ref=save('sourceguard.final.closed.json',cleanup)
 assert cleanup['closed'] is True and cleanup['retained_handles_count']==0 and cleanup['errors']==[]
 corrected=copy.deepcopy(controls)
 for check in corrected['checks']:
  if check['name']=='all486 native original and486 archive members held':
   check.update(name='all490 Native packet originals and490 archives held including486 owned and4 run files',passed=True,detail='Initial review expected 972 incorrectly; actual packet inventory is 980 and actual guard holds every entry. No consumer evidence changed.')
 corrected['blocking_findings']=[];corrected['correction_source_ref']=pin(N/'actual-checks.json');corrected['final_guard_ref_count']=count
 corrected['checks'].append(dict(name='final finite guard and raw audit ranges verified and released0',passed=True,detail=None));corrected['count']=len(corrected['checks'])
 cr=save('actual-checks.final.json',corrected)
 final=copy.deepcopy(old);final.update(decision='ACTUAL_MAIN_C19_TWO_CONSUMERS_COMPONENT_FIXTURE_VERIFIED',reviewed_at=datetime.now(timezone.utc).isoformat(),checks_ref=cr,source_guard_ref=cleanup_ref,actual_two_consumers_verified=True,blocking_findings=[],supersedes_review_ref=pin(N/'actual-decision.json'),review_correction='Native packet comprises486 owned files plus4 run-level files; all490 originals and490 archives were actually held. Initial expected count only was incorrect.',native_packet_original_count=490,native_packet_archive_count=490,owned_export_member_count=486)
 dr=save('actual-decision.final.json',final)
 mr=save('MF.final.json',dict(schema=oldmf['schema'],members=[pin(N/'closeout.py'),dr,cr,cleanup_ref,pin(N/'HDF.json'),pin(N/'MF.json'),*oldmf['members']],root_request_ref=old['root_request_ref'],current_canonical_refs=old['current_canonical_refs'],supersedes_manifest_ref=pin(N/'MF.json')))
 h=copy.deepcopy(oldh);h.update(decision=final['decision'],manifest_ref=mr,actual_decision_ref=dr,source_guard_ref=cleanup_ref,source_guard_ref_count=count,checks=corrected['count'],blocking_findings_count=0,supersedes_handoff_ref=pin(N/'HDF.json'),Root_next_original=1006)
 hr=save('HDF.final.json',h)
 for r in (hr,mr,dr):assert pin(r['path'])==r
 print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,checks=corrected['count'],guard_refs=count,blocking_findings=[]),ensure_ascii=False))

if __name__=='__main__':main()
