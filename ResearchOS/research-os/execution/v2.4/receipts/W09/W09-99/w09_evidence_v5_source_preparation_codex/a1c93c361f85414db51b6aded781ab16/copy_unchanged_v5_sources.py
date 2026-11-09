"""Exact-copy only the two unchanged v4 test support files into new packet."""
import hashlib
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
old = here.parents[1] / "w09_evidence_revision_source_preparation_codex/fdbee1676fd64d8b9a93ce81076c6c4c"
sources = [
    ("domain_test.proposed.go", "domain_test.v5.proposed.go",
     "83b0a57fcd3dd9a58f8c7493b2a164efe91aa04bbf87b1c11f7477b413093aac", 28018),
    ("w09_evidence_export_test.proposed.go", "w09_evidence_export_test.v5.proposed.go",
     "7862750e160532ee36d5fd3daa436e39e7a42cc1ea03884d129150ff7ce6ee2e", 12362),
]
raws = []
for old_name, new_name, wanted_sha, wanted_bytes in sources:
    raw = (old / old_name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != wanted_sha or len(raw) != wanted_bytes:
        raise SystemExit("reviewed source changed")
    raws.append((new_name, raw))
for new_name, raw in raws:
    with (here / new_name).open("xb") as stream:
        stream.write(raw)
print("EXACT_COPIES", len(raws))
