from pathlib import Path
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';S=Path(__file__).resolve().parent
RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
review=V/'receipts/W09/W09-99/w09_br8_formal_actual_review_codex/prepare-20261010-01/actual-2ce2da363cda4c698c4927462b3fc3c8/independent-review.json'
context=RUN/'assemble-259182b5a7584e23bc58a273088e06cd/context.json'
def load(p,d):
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==d;return json.loads(b)
rv=load(review,'ddc2d04040a388d6bb189b4db7adb4b043ccdb31c650f4bedc70458064a8fda0')
ct=load(context,'70a5fc149e2fda2fbf6d9ce518ec7c34d11d07f2f1985cf8d68f32b20652562c')
assert rv['decision']=='ACCEPTED' and rv['missing']==rv['failed']==[] and len(rv['verdicts'])==8
gr=load(review.parent/'SourceGuard.closed.json','e644aba8f68ff7cc00fab6b971a2d87e396b6e72c305887b598a9f906b9ba529')
assert gr['closed'] and gr['retained_handles_count']==0 and gr['errors']==[]
au=load(S/'w09.w09-br8-actual-formal-review01.actual-audit.root.json','5e3bd2e84f730ba90c79dcc2dbd62e06640e33b78185ee9cca0355b2d04ab3a7')
assert au['binding_sha256']=='ddc2d04040a388d6bb189b4db7adb4b043ccdb31c650f4bedc70458064a8fda0'
assert not (V/'root_delivery_captures/W09/W09-99/index.json').exists()
extras=dict(context_ref=dict(path=context.relative_to(R).as_posix(),sha256='70a5fc149e2fda2fbf6d9ce518ec7c34d11d07f2f1985cf8d68f32b20652562c'),review_ref=dict(path=review.relative_to(R).as_posix(),sha256='ddc2d04040a388d6bb189b4db7adb4b043ccdb31c650f4bedc70458064a8fda0'),original_offsets=au['source_line_offsets'],previous_index_ref=None)
p=RUN/'capture.actual.extras.root.json';b=(json.dumps(extras,ensure_ascii=False,indent=2)+'\n').encode()
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(extras_path=str(p),verdict_count=8,formal_acceptance=False),ensure_ascii=False))
