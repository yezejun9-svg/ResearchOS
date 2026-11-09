from pathlib import Path
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
old=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r337_readonly_review_codex/4bfbe59e6b504165a663076e88b53c16/seal.py'
s=old.read_text()
start=s.index('assert toolobs[');end=s.index('p=doc(N/"prepared_refs.json")',start)
s=s[:start]+'''assert toolobs['actual_prepare_outer_exit']==toolobs['actual_prepare_python_exit']==0
facts=[]
def walktools(x):
 if isinstance(x,dict):
  if 'chunk_id' in x and 'output' in x:facts.append(x)
  for v in x.values():walktools(v)
 elif isinstance(x,list):
  for v in x:walktools(v)
walktools(toolobs['observations'])
assert any(x['chunk_id']=='598eca' and x.get('session_id')==99811 for x in facts)
assert any(x['chunk_id']=='23e59d' and x.get('exit_code')==0 and 'ACTUAL_PYTHON_EXIT=0' in x['output'] for x in facts)
''' +s[end:]
changes=[
('desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5','desktop58-finite169-go3-r339-9eccde97a9fa4815941768cacaf590dc'),
('tool-observations.sixth-prepare.closed.original.json','tool-observations.seventh-final-binding-draft.closed.original.json'),
('1191049af62c6948f54f0ed9834c106e63624e40b71e3ace0f2b9a53f0dd9338','0d93b07797b48172b2605e9cdba6082c4709bba2bb9d421ba1b474945982d318'),('14635','23238'),
('0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1','c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859'),
('actual sourceReview bound 07d5','actual sourceReview bound 39cfe'),
('07d5b1e69beff42e2a99e987f240d09ca530ed3579cdb6c11428b6ff56084649','39cfe9d1690a271ace26478eb8dcd82a6c5acc07fbd7b7bfbdbc9810072fbcad'),
('617 exact failures not latepending','645 exact failures not latepending'),('[337,165,617]','[339,167,645]'),('[336,164,614]','[338,166,635]'),
('d8a016ddc71e440fb386a11957c098ea','fd6fec9e9d2a482d98203421ac21a82b'),
('Sixth scope admission','Seventh scope admission'),('Original 614 failure rows and three exact opaque new rows','Original 635 failure rows and ten exact opaque new rows'),('Old72ff closure metadata','Old b4d closure metadata')]
for a,b in changes:
 assert a in s,a
 s=s.replace(a,b)
with (O/'seal.py').open('xb') as f:f.write(s.encode())
print('Prepared new own sealer; actual original annex shape consumed, no candidate execution.')
