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
    path=Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_cli2_fact_abi_revision_preparation_codex\\ddc11e9721a6490baf1f0032c6bf6d16\\metadata_pipeline.desktop58.bound.v4.proposed.py')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755':
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
