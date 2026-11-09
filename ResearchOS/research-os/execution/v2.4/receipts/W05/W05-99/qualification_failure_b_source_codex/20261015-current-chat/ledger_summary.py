import json
from pathlib import Path

p = Path(__file__).resolve().parent
for result in sorted(p.glob("b*.result.json")):
    d = json.loads(result.read_text(encoding="utf-8"))
    if d.get("native_exit") != 0:
        print(result.name, "native_exit", d.get("native_exit"))
for stem in ("b75-blocked-broker", "b76-blocked-timeout", "b77-blocked-broker", "b82-temp-clean"):
    d = json.loads((p / (stem + ".result.json")).read_text(encoding="utf-8"))
    print(stem, "exit", d.get("native_exit"), "stderr_bytes", d.get("stderr_bytes"))
