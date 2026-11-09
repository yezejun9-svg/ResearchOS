import sys
sys.dont_write_bytecode=True
import ast,difflib,hashlib,json,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).resolve().parent
S=W/'w09_c19_caller_source_revision_codex/w09c19r2-1a11f08';V=W/'w09_evidence_v7_fragment_source_codex/fragv7-1a11f30'
GP=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
def verify(v):
 q=pin(v['path']);assert (q['sha256'],q['bytes'])==(v['sha256'].removeprefix('sha256:'),v['bytes']);return q
expected=[(S/'HDF.json','bfb479d0c441c0eeec03858ee41f1d12150e50c8b7b2cee563c16025525e58f2'),(S/'MF.json','455553ae51eb98c6ead665c7f9dfde0d9e6b5e765418d760f335d5f8845b0ab8'),(S/'prepare_w09_c19.actual_owned.py','bb3d5a0fc1bdabe32467dfaf5224053c26dac099a4975970c58266183e43bcd5'),(S/'run_w09_c19.actual_owned.py','edc33bd8d87466bbf465dfcbf91732034e55dffcb747e1bdb48064665e27d89b'),(V/'w09_evidence_closure.v7.proposed.py','1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777'),(V/'HDF.json','bb664f6f7c248b35836b95e36c079aa0bdb45d649a49898163f477cd627bfd39'),(V/'MF.json','a6b18e560edb37fb14c372f6d20e5760cf03b3d2ad11bd8d4e7ecbfed17dcda7'),(GP,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85')]
for p,sha in expected:assert pin(p)['sha256']==sha
refs=[pin(p) for p,_ in expected]+[pin(S/'source.integration.choice.json'),pin(S/'root-calling-contract.json'),pin(__file__),pin(sys.executable)]
for mf in (S/'MF.json',V/'MF.json'):
 members=json.loads(mf.read_bytes())['members'];members=members.values() if isinstance(members,dict) else members;refs += [verify(v) for v in members]
refs=list({v['path']:v for v in refs}.values())
gm=types.ModuleType('r3_source_guard');gm.__file__=str(GP);sys.modules[gm.__name__]=gm;exec(compile(GP.read_bytes(),str(GP),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
replacements=[('w09c19-1a11f08','w09c19v7-1a11f30'),('w09c19-isolation-1a11f08','w09c19v7-isolation-1a11f30'),('w09c19-producer-1a11f08','w09c19v7-producer-1a11f30'),('w09c19-isolation-env-1a11f08','w09c19v7-isolation-env-1a11f30'),('w09c19-producer-env-1a11f08','w09c19v7-producer-env-1a11f30')]
try:
 guard.acquire(refs)
 proofs=[]
 for filename in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py'):
  original=guard.get_buffer(str(S/filename));text=original.decode();applied=[]
  for old,new in replacements:
   count=text.count(old)
   if count:text=text.replace(old,new);applied.append(dict(old=old,new=new,count=count))
  inverse=text
  for item in reversed(applied):inverse=inverse.replace(item['new'],item['old'])
  assert inverse.encode()==original
  assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False)
  ast.parse(text)
  target=N/filename
  with target.open('xb') as f:f.write(text.encode())
  a=original.decode().splitlines(keepends=True);b=text.splitlines(keepends=True);ops=[]
  for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_start=i,old_end=j,new_start=k,new_end=l,old_lines=a[i:j],new_lines=b[k:l]))
  assert ''.join(x for v in ops for x in v['old_lines']).encode()==original and ''.join(x for v in ops for x in v['new_lines']).encode()==target.read_bytes()
  proofs.append(dict(original_ref=pin(S/filename),candidate_ref=pin(target),substitutions=applied,opcodes=ops,whole_byte_inverse=True,whole_AST_inverse=True))
 old_choice=json.loads(guard.get_buffer(str(S/'source.integration.choice.json')))
 paths={key:value for key,value in old_choice['fixed_paths'].items()}
 for key,path in paths.items():
  for old,new in replacements:path=path.replace(old,new)
  paths[key]=path;assert not Path(path).exists()
 save('caller-complete-inverse.json',dict(schema='researchos.w09-c19-v7-caller-five-path-inverse.v1',callers=proofs,allowed_path_replacements=replacements,all_other_caller_bytes_and_AST_unchanged=True,actual_jobs_not_run=True))
 save('source-input-pins.original.json',refs)
 save('fixed-future-paths.json',paths)
 for v in refs:assert pin(v['path'])==v
 print(json.dumps(dict(status='R3_CALLER_SOURCE_PATHS_ONLY_PREPARED',prepare_ref=pin(N/'prepare_w09_c19.actual_owned.py'),producer_ref=pin(N/'run_w09_c19.actual_owned.py'),all_five_future_paths_absent=True,input_count=len(refs))),flush=True)
finally:
 cleanup=guard.close();save('preparation-source-guard.cleanup.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
