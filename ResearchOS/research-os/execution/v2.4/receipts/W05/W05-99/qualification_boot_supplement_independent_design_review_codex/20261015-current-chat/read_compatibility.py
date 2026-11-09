import pathlib,json,hashlib
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
base=repo/'execution/v2.4/receipts/W05/W05-99'
p=base/'qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat/G04-B75-full-source.raw'
raw=p.read_bytes(); assert hashlib.sha256(raw).hexdigest()=='2947423a120efeffa64cf382884f19d01335bb014b3bec36c1410ee55c08f0a2'
text=raw.decode('utf-8-sig'); i=text.find('func (s *Service) validatedQualificationFailureTx')
print('B75_RAW_MATCH',i)
print(text[i:i+12500])
p=base/'resume_cp398_codex/20261015-current-chat/continuation-cp511/C-design-adopted-constraints.json'
raw=p.read_bytes(); assert hashlib.sha256(raw).hexdigest()=='66df2cc54b7e9ef89db1976043171299f72fd02a6a25971c78b1a23d57dfcf6c'
print('C_CONSTRAINTS',raw.decode('utf-8-sig'))
