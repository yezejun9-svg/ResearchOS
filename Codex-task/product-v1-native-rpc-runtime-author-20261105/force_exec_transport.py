from pathlib import Path
import hashlib

p = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-rpc-runtime-20261105\adapters\runtime\codex_driver_windows.go')
raw = p.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '343e36f77f226d1f2c9db72663c5b019376b2ed75143eefc06469c804dc772b9'
before = b'\treturn &codexCLI{options: options}, nil\n'
after = b'\toptions.Descriptor.NativeTransport = CodexExecTransport\n\treturn &codexCLI{options: options}, nil\n'
assert raw.count(before) == 1
p.write_bytes(raw.replace(before, after, 1))
print(hashlib.sha256(p.read_bytes()).hexdigest())
