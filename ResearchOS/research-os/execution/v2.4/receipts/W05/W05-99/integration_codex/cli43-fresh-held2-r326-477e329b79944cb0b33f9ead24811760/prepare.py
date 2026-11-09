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
    path=Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\cli43_root_binding_preparation_revision_codex\\9fd9cbeb1343442aa6e34e41f3f2deea\\metadata_pipeline.v7.proposed.py')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='095d4f4b86ad0432bd559d2df7221d7f26794eb484f07d313fcc67d3a54f3eed':
        raise RuntimeError('metadata module SHA mismatch')
    module=types.ModuleType('root_cli43_metadata')
    module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module.main('prepare')

if __name__=='__main__':
    try: code=entry()
    except BaseException as exc:
        sys.stderr.write(json.dumps({'phase':'PRE_METADATA_OWNED_LEAF','error':repr(exc),'actual_native_exit':None,
            'automatic_retry':False,'counter_reset':False},ensure_ascii=False)+'\n')
        code=1
    raise SystemExit(code)
