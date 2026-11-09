from pathlib import Path
import hashlib

p = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-policy-binding-20261105\internal\domain\runtime_harness_windows.go')
old = p.read_bytes()
before = b'"workspace_read_scope": readiness.State, "cancellation": "UNVERIFIED"'
after = b'"workspace_read_scope": "UNVERIFIED", "cancellation": "UNVERIFIED"'
assert old.count(before) == 1
new = old.replace(before, after)
before2 = b'"enforcement_verified": ready}'
after2 = b'"enforcement_verified": false}'
assert new.count(before2) == 1
new = new.replace(before2, after2)
p.write_bytes(new)
print(hashlib.sha256(old).hexdigest(), hashlib.sha256(new).hexdigest())
