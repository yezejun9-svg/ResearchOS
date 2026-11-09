"""Root-only future pure-IO draft builder. Never imports the owned Windows helper."""
import sys
sys.dont_write_bytecode = True
import hashlib
from pathlib import Path
import types

def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize):
        raise RuntimeError('Python -I -S -X utf8 required')
    if len(sys.argv) != 3:
        raise RuntimeError('builder request-path request-sha')
    p = Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_forward_head_metadata_preparation_revision_codex\\756f86f1976e4f80b6d006b5549c2370\\forward_head_engine.v2.proposed.py')
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != 'da7589b15de7c81d02642a14f02a33d827cc165b2920d8a413cb5ba0d56f8b1c' or len(raw) != 44702:
        raise RuntimeError('fixed engine bytes')
    m = types.ModuleType('desktop58_forward_metadata_engine')
    m.__file__ = str(p)
    sys.modules[m.__name__] = m
    exec(compile(raw, str(p), 'exec'), m.__dict__)
    m.MODE = 'prepare'
    return m.main()

if __name__ == '__main__':
    raise SystemExit(main())
