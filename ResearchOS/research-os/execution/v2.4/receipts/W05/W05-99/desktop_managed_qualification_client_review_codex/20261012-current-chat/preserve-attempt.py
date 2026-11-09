from pathlib import Path
OUT=Path(__file__).resolve().parent
dest=OUT/'lifecycle-attempt1-nvm-shim';dest.mkdir(exist_ok=True)
for name in ['lifecycle-edges.mjs','lifecycle-edges.stdout','lifecycle-edges.stderr','lifecycle-edges.invocation.json']:
    (dest/name).write_bytes((OUT/name).read_bytes())
