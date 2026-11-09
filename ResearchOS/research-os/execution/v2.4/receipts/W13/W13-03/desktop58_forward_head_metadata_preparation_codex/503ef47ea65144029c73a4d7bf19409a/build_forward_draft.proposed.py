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
    p = Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_forward_head_metadata_preparation_codex\\503ef47ea65144029c73a4d7bf19409a\\forward_head_engine.proposed.py')
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != '6cbedde0cef3932bdd336da891a2cf52ef3629ae2c9fc48329d1ff3c30d7fa5b' or len(raw) != 44066:
        raise RuntimeError('fixed engine bytes')
    m = types.ModuleType('desktop58_forward_metadata_engine')
    m.__file__ = str(p)
    sys.modules[m.__name__] = m
    exec(compile(raw, str(p), 'exec'), m.__dict__)
    m.MODE = 'prepare'
    return m.main()

if __name__ == '__main__':
    raise SystemExit(main())
