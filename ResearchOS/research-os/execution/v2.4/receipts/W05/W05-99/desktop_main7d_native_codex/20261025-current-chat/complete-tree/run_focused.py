"""Execute a prewritten focused-check batch with raw process outputs."""
import json
import os
from pathlib import Path
import subprocess
import sys


here = Path(__file__).resolve().parent
recipe = json.loads((here / sys.argv[1]).read_bytes())
env = os.environ.copy()
env.update(recipe["environment"])
for item in recipe["commands"]:
    base = here / f"{Path(sys.argv[1]).stem}-{item['name']}"
    with Path(str(base) + ".stdout.raw").open("xb") as stdout, Path(str(base) + ".stderr.raw").open("xb") as stderr:
        proc = subprocess.Popen(item["argv"], cwd=recipe["cwd"], env=env,
                                stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL)
        code = proc.wait()
    Path(str(base) + ".native-exit.txt").write_text(f"{code}\n", encoding="ascii", newline="\n")
    print(f"{item['name']} native_exit={code}")
    if code:
        sys.exit(code)
