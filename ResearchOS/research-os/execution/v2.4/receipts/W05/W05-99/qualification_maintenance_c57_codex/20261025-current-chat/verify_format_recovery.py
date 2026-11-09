from pathlib import Path
import hashlib,json,subprocess,sys
wt=Path(sys.argv[1]); scope=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
restore_output=Path(sys.argv[3]).read_text(encoding='utf-8-sig')
restored=[line.split(':',1)[1].strip() for line in restore_output.splitlines() if line.startswith('restored exact HEAD bytes:')]
for p in restored:
    got=(wt/p).read_bytes(); expected=subprocess.check_output(['git','-C',str(wt),'show','HEAD:'+p])
    assert got==expected, p
    print('RESTORED_HEAD_MATCH',p,hashlib.sha256(got).hexdigest())
for entry in scope['inherited43_other_paths_must_remain_exact']:
    p=entry['path']; actual=wt/p
    if not actual.exists():
        print('PIN_MISSING_SPARSE',p); continue
    got=actual.read_bytes(); hash=hashlib.sha256(got).hexdigest()
    assert hash==entry['sha256'] and len(got)==entry['bytes'],p
    print('PIN43_MATCH',p,hash)
