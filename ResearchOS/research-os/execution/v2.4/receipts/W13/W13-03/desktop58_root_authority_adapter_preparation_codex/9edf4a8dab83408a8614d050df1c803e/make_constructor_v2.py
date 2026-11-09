import ast,json,hashlib
from pathlib import Path
out=Path(__file__).parent
old=(out/'prepare_source.py').read_bytes()
lines=old.splitlines(keepends=True)
matched=[i for i,x in enumerate(lines) if x.startswith(b'oldreturn=')]
assert len(matched)==1
i=matched[0]
assert lines[i].count(b'\\r\\n')==1
before=lines[i];lines[i]=lines[i].replace(b'\\r\\n',b'\\n',1)
new=b''.join(lines)
ast.parse(new)
assert new.replace(lines[i],before,1)==old
with (out/'prepare_source.v2.py').open('xb') as f:f.write(new)
with (out/'constructor-v2-delta.json').open('xb') as f:f.write((json.dumps({'old_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(new).hexdigest(),'line':i+1,'old':before.decode(),'new':lines[i].decode(),'inverse_exact':True,'source_CRLF':0,'source_LF':441,'candidate_execution':False},indent=2)+'\n').encode())
