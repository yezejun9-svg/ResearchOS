"""Only unchanged Root stdout decoder conditions; no actual capture/qualification."""
import json,types,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
S=D.parent.parent/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
G=D.parent.parent/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
def load(p,n):
 m=types.ModuleType(n);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
 g=load(G,'stdout_Source_guard');guard=g.SourceReadGuard();refs=[pin(__file__),pin(S/'main23_root.source.py'),pin(G)]
 try:
  guard.acquire(refs);m=load(S/'main23_root.source.py','stdout_Source_decoder_inert')
  fixture=dict(schema=m.CAPTURE_RESULT_SCHEMA,issued_by='SOURCE_ONLY_NO_ROOT_AUTHORITY',observed_refs=['SOURCE_ONLY_NOT_A_REF'])
  single=json.dumps(fixture)+'\nROOT_SOURCE_PYTHON_EXIT=0\n'
  multi=json.dumps(fixture,indent=2)+'\nROOT_SOURCE_PYTHON_EXIT=0\n'
  decoded=[v for v in m.structured_documents(single) if type(v) is dict and v.get('schema')==m.CAPTURE_RESULT_SCHEMA]
  assert decoded==[fixture]
  assert not [v for v in m.structured_documents(multi) if type(v) is dict and v.get('schema')==m.CAPTURE_RESULT_SCHEMA]
  assert m.structured_documents(json.dumps(fixture))==[fixture]
 finally:closed=guard.close();cr=save('Root-stdout-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 rr=save('Root-tool-stdout-format.Source-interface.json',dict(schema='researchos.main23-Root-stdout-Source-interface-review.v1',status='PASS_SOURCE_ONLY',checks=3,single_JSON_line_with_PowerShell_marker_supported=True,multiline_JSON_with_marker_requires_new_actual_observation=True,whole_plain_JSON_supported=True,old_a49d1d_actual_capture_qualified=False,original1066_not_reset=True,fixture_authority='NONE',actual_qualification_created=False,Source_guard_ref=cr,execution_grant=False,formal_acceptance=False))
 print(json.dumps(dict(result_ref=rr,checks=3,guard_ref=cr,retained_handles_count=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
