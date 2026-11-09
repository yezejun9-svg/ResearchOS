import pathlib,json,hashlib,re,struct
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
A=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat'
arch=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat'
review=R/'execution/v2.4/receipts/W05/W05-99/qualification_boot_supplement_independent_design_review_codex/20261015-current-chat'
paths=[arch/'BOOT-C-ARCHITECTURE.md',arch/'actual-deployment-plan-reviewable.md',arch/'C-boot-test-cuts.json',arch/'FINAL-manifest.json',review/'design-review.md',review/'design-review.json',review/'FINAL-manifest.json',R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp521/boot-proposal-adopted-limits.json',W/'internal/recoveryboundary/contract.go',W/'internal/recoveryboundary/boot_windows.go']
paths+=sorted(A.glob('v7-binary-0[12]*'))
D=B/'BINARY-contract-snapshot';D.mkdir(exist_ok=False)
refs=[]
for i,p in enumerate(paths):
 raw=p.read_bytes();dest=D/(str(i).zfill(2)+'-'+p.name);dest.write_bytes(raw)
 refs.append({'source':str(p),'snapshot':str(dest.relative_to(B)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mutable_source':str(p).startswith(str(W))})
for x in refs:assert hashlib.sha256(pathlib.Path(x['source']).read_bytes()).hexdigest()==x['sha256']
(D/'manifest.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf-8')
raw=(A/'v7-binary-02.stdout').read_text()
bm=re.search(r'NtQuery before raw=([0-9a-f]+)',raw);am=re.search(r'NtQuery after  raw=([0-9a-f]+)',raw)
assert bm and am
before=bytes.fromhex(bm.group(1));after=bytes.fromhex(am.group(1))
def parse(v):
 rev,sbz,ctrl,owner,group,sacl,dacl=struct.unpack_from('<BBHIIII',v)
 aclrev,aclsbz,aclbytes,count,sbz2=struct.unpack_from('<BBHHH',v,dacl)
 entries=[];off=dacl+8
 for i in range(count):
  typ,flags,size=struct.unpack_from('<BBH',v,off)
  mask=struct.unpack_from('<I',v,off+4)[0]
  entries.append({'index':i,'offset':off,'type':typ,'flags':flags,'size':size,'mask':hex(mask),'bytes_hex':v[off:off+size].hex(),'body_without_flags_hex':(v[off:off+1]+v[off+2:off+size]).hex()})
  off+=size
 assert off==dacl+aclbytes
 return {'revision':rev,'reserved':sbz,'control':hex(ctrl),'offsets':[owner,group,sacl,dacl],'acl_revision':aclrev,'acl_reserved':[aclsbz,sbz2],'acl_size':aclbytes,'ace_count':count,'aces':entries}
bp,ap=parse(before),parse(after)
diff=[{'offset':i,'before':before[i],'after':after[i]} for i in range(len(before)) if before[i]!=after[i]]
assert len(before)==len(after)==172
assert [x['offset'] for x in diff]==[85,109,129,149]
assert all(x['before']==0 and x['after']==16 for x in diff)
assert bp['offsets']==ap['offsets'] and bp['control']==ap['control']
assert all(x['body_without_flags_hex']==y['body_without_flags_hex'] for x,y in zip(bp['aces'],ap['aces']))
out={'class':'INDEPENDENT_READ_ONLY_PARSE_OF_AUTHOR_RAW_NOT_TEST_RUN','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'before':bp,'after':ap,'different_bytes':diff,'interpretation':'four ACE Header.AceFlags changed 0x00 to INHERITED_ACE 0x10; not layout or padding'}
(B/'BINARY-native-ace-diff.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'references':refs,'analysis':out},ensure_ascii=False,indent=2))
print('DEPLOYMENT')
for i,l in enumerate((arch/'actual-deployment-plan-reviewable.md').read_text().splitlines(),1):print(f'{i}: {l}')
print('CUTS_MATCHES')
for i,l in enumerate((arch/'C-boot-test-cuts.json').read_text().splitlines(),1):
 if re.search('restore|descriptor|binary|byte|SDDL',l,re.I):print(f'{i}: {l}')
print('CONTRACT_SCHEMA')
for i,l in enumerate((D/'08-contract.go').read_text().splitlines(),1):
 if i<55:print(f'{i}: {l}')
print('SOURCE_SD_FLOW')
for i,l in enumerate((D/'09-boot_windows.go').read_text().splitlines(),1):
 if re.search(r'SecurityDescriptorFromString|SecurityDescriptor:|GetSecurityInfo|func setTargetDescriptor|desiredSD|NtSetSecurityObject',l):print(f'{i}: {l}')

