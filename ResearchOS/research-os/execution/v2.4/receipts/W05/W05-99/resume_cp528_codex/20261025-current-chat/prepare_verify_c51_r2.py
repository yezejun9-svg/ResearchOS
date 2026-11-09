import hashlib,json,subprocess,sys
from pathlib import Path
N=Path(__file__).parent
text=(N/'verify_c51_preseal.py').read_text(encoding='utf8')
old="assert hashlib.sha256(b''.join(lines[:86])).hexdigest()=='ee17964a2dec0902a1cbbefc3f227a2953054e5a175d6914a58c179bdecee939'"
replacement="""prefix_sha=hashlib.sha256(b''.join(lines[:86])).hexdigest()
assert prefix_sha!='ee17964a2dec0902a1cbbefc3f227a2953054e5a175d6914a58c179bdecee939'
reconstructed=B/'C51-DIAGNOSTIC-LEDGER-RECONSTRUCTED-86.jsonl'
verify(reconstructed,{'sha256':'ee17964a2dec0902a1cbbefc3f227a2953054e5a175d6914a58c179bdecee939','bytes':60297})
verify(B/'C51-LEDGER-REWRITE-INCIDENT.json',{'sha256':'7466aeb459790a67caf0e9eb2b4c99722b8ad3d65040980957bdb777ac939141'})
verify(B/'C51-DIAGNOSTIC-INCREMENT-053.jsonl',{'sha256':'8cb37c0c2001bfd4c407d4320cc9bd0a7aafcb0c2df0fd3754ea312609a761df'})
verify(B/'C51-EARLY-RAW-ADDENDUM.md')
assert hashlib.sha256(ledger).hexdigest()=='a203004e23dd3b26d4508a7680808a0e083bec924f93f6359f3e08698829c6e7'
assert len(lines)==89
"""
assert text.count(old)==1;text=text.replace(old,replacement)
text=text.replace('C51-root-patch-check.', 'C51-root-patch-check-r2.')
text=text.replace('C51-DIAGNOSTIC-LEDGER.root-snapshot.jsonl','C51-DIAGNOSTIC-LEDGER.root-snapshot-89.jsonl')
text=text.replace("'ledger_first86_hash_preserved':True","'ledger_first86_current_bytes_preserved':False,'original86_reconstruction_hash_matches_original_announced_hash':True,'reconstruction_is_not_original_file_continuity':True,'current89_prefix_sha256':prefix_sha")
text=text.replace('C51-root-preseal-verification.json','C51-root-preseal-verification-r2.json')
text=text.replace("'007 and009 broad formatting history requires additive author detail; current40pins exact'","'007 and009 formatting history now detailed in additive report; current40pins exact, original pre-restore full diff capture still missing'")
p=N/'verify_c51_preseal_r2.py'
with p.open('x',encoding='utf8')as f:f.write(text)
r=subprocess.run([sys.executable,'-B','-X','utf8',str(p)])
raise SystemExit(r.returncode)

