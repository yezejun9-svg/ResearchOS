"""Create a byte-verified B1 source archive without editing the worktree."""
import difflib
import hashlib
import json
import pathlib
import subprocess
import sys

WT = pathlib.Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-rpc-runtime-20261105")
BASE = "c3c7812347bb72930365fbb5db0efee8a965bc78"
FILES = (
    "codex.go", "codex_policy.go", "codex_driver_windows.go",
    "codex_rpc_windows.go", "codex_rpc_protocol.go", "codex_policy_test.go",
    "codex_rpc_windows_test.go", "codex_rpc_protocol_test.go",
)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    out = pathlib.Path(sys.argv[1])
    if out.exists():
        raise SystemExit("archive destination already exists")
    out.mkdir(parents=True)
    (out / "source").mkdir()
    (out / "inverse-baseline").mkdir()
    forward, inverse, manifest = [], [], {}
    for name in FILES:
        rel = "adapters/runtime/" + name
        source = (WT / rel).read_bytes()
        old = subprocess.run(["git", "show", BASE + ":" + rel], cwd=WT,
                             capture_output=True).stdout
        if name not in ("codex_rpc_windows.go","codex_rpc_protocol.go",
                        "codex_rpc_windows_test.go","codex_rpc_protocol_test.go") and not old:
            raise RuntimeError("missing tracked baseline " + rel)
        (out / "source" / name).write_bytes(source)
        if old:
            (out / "inverse-baseline" / name).write_bytes(old)
        manifest[rel] = {
            "baseline_sha256": sha(old) if old else "ABSENT_BEFORE",
            "source_sha256": sha(source),
            "baseline_bytes": len(old),
            "source_bytes": len(source),
        }
        before = old.decode("utf-8").splitlines(keepends=True)
        after = source.decode("utf-8").splitlines(keepends=True)
        forward.extend(difflib.unified_diff(before, after, fromfile="a/"+rel if old else "/dev/null",
                                            tofile="b/"+rel))
        inverse.extend(difflib.unified_diff(after, before, fromfile="a/"+rel,
                                            tofile="b/"+rel if old else "/dev/null"))
    (out / "forward.patch").write_text("".join(forward), encoding="utf-8", newline="")
    (out / "inverse.patch").write_text("".join(inverse), encoding="utf-8", newline="")
    manifest["base_head"] = BASE
    manifest["scope"] = "PRODUCT_V1_NATIVE_RPC_RUNTIME"
    (out / "SOURCE.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
