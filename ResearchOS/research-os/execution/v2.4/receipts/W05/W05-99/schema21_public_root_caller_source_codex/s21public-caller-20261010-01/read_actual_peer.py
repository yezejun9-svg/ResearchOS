import hashlib,json
from pathlib import Path
p=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public21-source-review-v2.actual-audit.root.json')
try:
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='775d81746688b95de66cdb101c5caec0d22ebed3bdeffec194afcf31eac782dd' and len(raw)==1126
    binding=json.loads(raw);ref=binding['original_capture_ref'];data=Path(ref['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==ref['sha256'] and len(data)==ref['bytes']
    rows=[json.loads(x) for x in data.splitlines()];last=rows[-1];print(json.dumps(dict(author=last['payload']['author'],text=last['payload']['content'][0]['text']),ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1',flush=True);raise
else:print('ROOT_PYTHON_EXIT=0',flush=True)
