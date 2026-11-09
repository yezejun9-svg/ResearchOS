"""Read-only validation of seal inputs; reports static findings with exit zero."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("seal_selected_source.py")
source = target.read_text(encoding="utf-8")
marker = 'template_ref = emit("root-source-members.template.json", {'
if source.count(marker) != 1:
    print("PREFLIGHT_FINDING", "seal marker shape mismatch")
else:
    try:
        exec(compile(source.split(marker)[0], str(target), "exec"), {"__file__": str(target)})
        print("PREFLIGHT_PASS")
    except BaseException as exc:
        print("PREFLIGHT_FINDING", type(exc).__name__, str(exc))
