from pathlib import Path
import json,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
old=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r337_readonly_review_codex/4bfbe59e6b504165a663076e88b53c16/audit.py'
raw=old.read_bytes();text=raw.decode();changes=[
('desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5','desktop58-finite169-go3-r339-9eccde97a9fa4815941768cacaf590dc'),
('79e1495bcbe3ac44baf03142bec2d260b117bec33bd0e7ce29c47d98423109b7', '087db26ecb643be25e21265fdaeb54c401d4a774fc9a425c9d51631cf2d3745d'),('5111307','5136740'),
('8fe10d258e33569fbcb081284d5a2da3148a2e0b587d47ec58c12de5253adab6','2f39332cfb1fc94e8bb823dd18ede8891902e51da00d8d778cc94c07c7f529b4'),
('edf1a088cb36f178333132d5cbad395a7b052329969a649f5da26aa14edffdd6','4f03d976da8196cae86273b5c1da2bc08822b81a655570db3ba5ba592b44a7f1'),('22067','22066'),
('0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1','c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859'),
('[336,164,614]','[338,166,635]'),('[337,165,617]','[339,167,645]'),
("'all614 original prefix+3exact'","'all635 original prefix+10exact'"),
("len(oldcp['failure_counters'])==614 and len(cut['origins'])==3","len(oldcp['failure_counters'])==635 and len(cut['origins'])==10"),
("prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882'","prior['run_uuid']=='b4d53db07f1e4ab8b9c0b37e291a6da5'"),
("cp['expected_previous_revision']==336","cp['expected_previous_revision']==338"),
("ck('24394verified',len(p['verified_refs'])==24394)","ck('24407verified',len(p['verified_refs'])==24407)")]
for a,b in changes:
    assert a in text,a
    text=text.replace(a,b)
with (O/'audit.py').open('xb') as f:f.write(text.encode())
with (O/'audit-derivation.json').open('xb') as f:f.write((json.dumps({'schema':'researchos.independent-audit-derivation.v1','old_algorithm_ref':{'path':str(old),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'changes':changes,'new_input_driven_review':True,'candidate_executed':False},ensure_ascii=False,indent=2)+'\n').encode())
print('Derived own read-only audit for actual r339 inputs; no candidate import/execution.')
