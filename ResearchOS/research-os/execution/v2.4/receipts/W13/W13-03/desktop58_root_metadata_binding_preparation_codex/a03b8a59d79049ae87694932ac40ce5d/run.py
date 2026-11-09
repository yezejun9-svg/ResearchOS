"""Future Root-only metadata wrapper; AST-prepared, NOT EXECUTED."""
import hashlib
import json
from pathlib import Path
import sys
import types

def entry():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode):
        raise RuntimeError('Python -I -S -X utf8 required')
    sys.dont_write_bytecode=True
    path=Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_root_metadata_binding_preparation_codex\\a03b8a59d79049ae87694932ac40ce5d\\metadata_pipeline.desktop58.proposed.py')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='15df7a4c54a58df2d11036ae7a1a1c8080ef6461264e75a3c89f52db1c795cff':
        raise RuntimeError('metadata module SHA mismatch')
    module=types.ModuleType('root_cli43_metadata')
    module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module.main('run')

if __name__=='__main__':
    try: code=entry()
    except BaseException as exc:
        sys.stderr.write(json.dumps({'phase':'PRE_METADATA_OWNED_LEAF','error':repr(exc),'actual_native_exit':None,
            'automatic_retry':False,'counter_reset':False},ensure_ascii=False)+'\n')
        code=1
    raise SystemExit(code)
