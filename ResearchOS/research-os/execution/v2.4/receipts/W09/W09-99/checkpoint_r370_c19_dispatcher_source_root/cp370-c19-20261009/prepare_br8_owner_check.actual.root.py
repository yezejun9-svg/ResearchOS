from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
def ref(p,base=R):
 b=p.read_bytes();return dict(path=p.relative_to(base).as_posix(),sha256=hashlib.sha256(b).hexdigest())
def save(p,d):
 b=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
pr=RUN/'capture-a7067db724ce4a34a71a01055c9e00c8/result.json';b=pr.read_bytes();assert hashlib.sha256(b).hexdigest()=='8a9e3a2915c12bd67df0768f13696e9a087704fbf72f1c5ba22cef68ff1c884f'
proposal=json.loads(b);issuance=R/proposal['issuance_ref']['path'];context=RUN/'assemble-259182b5a7584e23bc58a273088e06cd/context.json'
review=V/'receipts/W09/W09-99/w09_br8_formal_actual_review_codex/prepare-20261010-01/actual-2ce2da363cda4c698c4927462b3fc3c8/independent-review.json'
assert ref(context)['sha256']=='70a5fc149e2fda2fbf6d9ce518ec7c34d11d07f2f1985cf8d68f32b20652562c' and ref(review)['sha256']=='ddc2d04040a388d6bb189b4db7adb4b043ccdb31c650f4bedc70458064a8fda0'
assert ref(issuance)['sha256']==proposal['issuance_ref']['sha256']
now=datetime.now(timezone.utc).isoformat();isd=json.loads(issuance.read_bytes());assert now>=isd['observed_at']
owner=dict(id='W09-99',status='ACCEPTED',executor_id='codex:/root',verifier_id='/root/backup_regression_resources',accepted_at=now,evidence=[ref(p,V) for p in (context,review,issuance)],scope_note='Eight independent PASS verdicts, six actual consumers, C19 and A06 complete GLOBALs; current formal derivation still required.')
own=save(RUN/'prospective-owner.actual.root.json',owner)
plan=Path(r'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\contracts\execution.plan.json')
pb=plan.read_bytes();assert hashlib.sha256(pb).hexdigest()=='a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17'
extras=dict(prospective_owner_ref=own,context_ref=ref(context),review_ref=ref(review),issuance_ref=ref(issuance),plan_ref=dict(path=str(plan),sha256=hashlib.sha256(pb).hexdigest(),bytes=len(pb)))
er=save(RUN/'check.actual.extras.root.json',extras)
print(json.dumps(dict(prospective_owner_ref=own,extras_ref=er,Canonical_written=False,formal_derivation_pending=True),ensure_ascii=False))
