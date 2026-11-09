"""Append all observed originals through985; keep prior resumes byte immutable."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
W=N.parent.parent
def pin(p):
    p=p.resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(v):
    assert set(v)=={'path','sha256','bytes'};b=Path(v['path']).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'];return b
def save(name,obj):
    with (N/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
old=json.loads((N/'RESUME.cp369-native-qualified.live981.root.json').read_bytes())
for v in old['canonical_refs']:read(v)
p=json.loads(read(old['pending_diagnostics_ref']))
for ordinal in range(981,985):
    r=pin(N/('failure'+str(ordinal)+'.original-tool-io.root.json'));v=json.loads(read(r))
    p['pending'].append(dict(ordinal=ordinal,origin_ref=r,origin_selector='original-tool-io',actual_outer_exit=v['actual_outer_exit'],actual_python_exit=v['actual_python_exit'],actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,description=v.get('diagnostic','Original Root readonly archive invocation; exact original IO retained.')))
fp=W/'w09_formal_profile_v4_source_codex/profv4-01a12c10'
r=dict(path=str((fp/'original-tool-failures-v4.md').resolve(strict=True)),sha256='ac768e225929311609008ee71f303e455a0f95610293461e498462179a64cd3f',bytes=1484);read(r)
p['pending'].append(dict(ordinal=985,origin_ref=r,origin_selector='52dcb1',actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,description='Source v4 sealer compared different proposal paths as equal refs; first invocation failed before seal. Byte/SHA comparison with separate original path verification subsequently passed.'))
assert [v['ordinal'] for v in p['pending']]==list(range(966,986))
p['next_original_failure_ordinal']=986
pr=save('pending-diagnostics.live986.root.json',p)
old.update(created_utc=datetime.now(timezone.utc).isoformat(),next_original_failure_ordinal_live=986,pending_diagnostics_ref=pr,W09_formal_profile_source_status='V4_SOURCE_SEALED_PENDING_INDEPENDENT_REVIEW',W09_formal_profile_source_handoff_ref=pin(fp/'HDF.json'),W09_formal_profile_source_manifest_ref=pin(fp/'MF.json'),C19_dispatcher_caller_source_status='IMPLEMENTING_SOURCE_ONLY_NO_ACTUAL_DISPATCH')
assert old['W09_formal_profile_source_handoff_ref']['sha256']=='e27b1ec5b48f19f23271ea7604d0f3bec04dcfe443191af2891f49dac2ba908a'
resume=save('RESUME.cp369-native-qualified.live986.root.json',old)
for v in old['canonical_refs']:read(v)
print(json.dumps(dict(resume_ref=resume,pending_diagnostics_ref=pr,live_next=986,canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
