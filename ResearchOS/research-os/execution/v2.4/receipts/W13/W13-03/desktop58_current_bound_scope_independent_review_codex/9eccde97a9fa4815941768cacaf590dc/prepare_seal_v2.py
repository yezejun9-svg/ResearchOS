from pathlib import Path
import hashlib,json
O=Path(__file__).parent
old=(O/'seal.py').read_bytes()
needle=b"pre['failed'][0]['check']"
assert old.count(needle)==1
new=old.replace(needle,b"pre['failed'][0]['name']")
new=new.replace(b"'new_failure_origins':[]",b"'new_failure_origins':[ref(O/'failure-origin.17b9ae.json')]")
new=new.replace(b"'new_failure_count':0",b"'new_failure_count':1")
with (O/'seal.v2.py').open('xb') as f:f.write(new)
r=(O/'failure-origin.17b9ae.json').read_bytes()
print(json.dumps({'origin_ref':{'path':str(O/'failure-origin.17b9ae.json'),'sha256':hashlib.sha256(r).hexdigest(),'bytes':len(r)},'old_sealer_preserved':True,'predicate_only_correction':'literal-precheck row name key; unchanged all audits/resource inputs','failure_disclosure_updated':True},ensure_ascii=False))
