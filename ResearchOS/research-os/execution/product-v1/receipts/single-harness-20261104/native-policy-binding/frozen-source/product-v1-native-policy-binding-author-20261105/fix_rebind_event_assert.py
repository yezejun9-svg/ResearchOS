from pathlib import Path
import hashlib

p = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-policy-binding-20261105\internal\domain\runtime_harness_windows_test.go')
raw = p.read_bytes()
before = b'Arr(events["data"].(map[string]any), "items")'
after = b'Arr(events["data"].(map[string]any), "events")'
assert raw.count(before) == 1
p.write_bytes(raw.replace(before, after, 1))
print(hashlib.sha256(p.read_bytes()).hexdigest())
