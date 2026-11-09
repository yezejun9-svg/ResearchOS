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
    path=Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_root_metadata_scope_binding_revision_preparation_codex\\1c4ea6999d4d4437a0202c4e81ce581b\\metadata_pipeline.desktop58.bound.v2.proposed.py')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='ce57675388c87ced955106931425175adae974def5a10b214de01efdfb40836c':
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
