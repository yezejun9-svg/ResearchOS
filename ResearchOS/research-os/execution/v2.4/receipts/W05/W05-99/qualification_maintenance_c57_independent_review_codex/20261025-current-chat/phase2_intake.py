import pathlib,json,hashlib,subprocess
B=pathlib.Path(__file__).parent;R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp547/C57-independent-phase2-exact57-amendment.json'
raw=A.read_bytes();assert hashlib.sha256(raw).hexdigest()=='15fc725cd3c61a165949718775c163d41bf9f9ddc7f8dfadf9f2467185d76bba'
a=json.loads(raw)
for key in ['source57_manifest_ref','author_finalizer_ref','Root_commit_verification_ref','source_scope_ref','preparation_scope_ref']:
 ref=a[key];p=R/ref['path'];data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==ref['sha256'],key
 obj=json.loads(data)
 print('REF',key,'KEYS',list(obj))
 if key in ['source57_manifest_ref','Root_commit_verification_ref','source_scope_ref']:
  for k,v in obj.items():
   if isinstance(v,list):print('LIST',k,'COUNT',len(v),'SAMPLE',json.dumps(v[:1],ensure_ascii=False)[:2000])
   elif isinstance(v,dict):print('DICT',k,'KEYS',list(v))
   else:print('VALUE',k,str(v)[:300])
 else:print(json.dumps(obj,ensure_ascii=False,indent=2))
p=subprocess.run(['git','ls-tree','-r','-l','--full-tree',a['candidate_commit']],cwd=R,capture_output=True);assert p.returncode==0
lines=p.stdout.decode().splitlines();sizes=[int(l.split()[3]) for l in lines if l.split()[1]=='blob']
print('TREE_BLOBS',len(sizes),'TOTAL_BYTES',sum(sizes))
print('ASCII_ROOT_EXISTS',pathlib.Path(a['owned_ascii_native_fixture_root']).exists(),'SNAPSHOT_EXISTS',pathlib.Path(a['isolated_snapshot']).exists())
