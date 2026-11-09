import ast,hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
old=Q/'publish_six_modes.py';raw=old.read_bytes()
before=b'publication_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=32*1024*1024)'
after=b'publication_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=128*1024*1024)'
assert raw.count(before)==1
revised=raw.replace(before,after,1);ast.parse(revised)
assert revised.replace(after,before,1)==raw
new=Q/'publish_six_modes_revision.py'
with new.open('xb')as out:out.write(revised)
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
print(json.dumps({'base_ref':ref(old),'revision_ref':ref(new),'only_delta':'publication guard total cap 32MiB to 128MiB, per-file cap unchanged','inverse_bytes_equal':True},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
