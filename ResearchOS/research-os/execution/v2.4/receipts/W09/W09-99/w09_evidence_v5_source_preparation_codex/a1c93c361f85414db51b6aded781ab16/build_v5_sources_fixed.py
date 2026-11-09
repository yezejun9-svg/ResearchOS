"""One-shot corrected pure source builder; original failed input remains sealed."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
source = (here / "build_v5_sources.py").read_text(encoding="utf-8")
old = '''            if event.get("method") != method or not event.get("path", "").endswith(suffix)
                    or event.get("status") != 201:
'''
new = '''            if (event.get("method") != method or not event.get("path", "").endswith(suffix)
                    or event.get("status") != 201):
'''
if source.count(old) != 1:
    raise SystemExit("original source anchor changed")
source = source.replace(old, new)
exec(compile(source, str(here / "build_v5_sources.py"), "exec"), globals())
