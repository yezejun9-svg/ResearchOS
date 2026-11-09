"""Text-only proposed-source checks; never compiles or runs the Go helper."""
from pathlib import Path
import difflib
import json
from pygments import lex
from pygments.lexers import GoLexer
from pygments.token import Error, Punctuation

root = Path(__file__).resolve().parent
files = sorted(root.glob("*.go"))
assert len(files) == 4, "expected exactly four proposed Go source files"
pairs = {"}": "{", ")": "(", "]": "["}
for source in files:
    text = source.read_text(encoding="utf-8")
    assert text.startswith("//go:build windows\n"), source.name
    stack = []
    for token, value in lex(text, GoLexer()):
        assert token not in Error, f"lexical error in {source.name}: {value!r}"
        if token in Punctuation and value in "{}()[]":
            if value in "{([":
                stack.append(value)
            else:
                assert stack and stack.pop() == pairs[value], source.name
    assert not stack, source.name
for template in root.glob("*.template.json"):
    json.loads(template.read_text(encoding="utf-8"))
assert len(list(root.glob("*.template.json"))) == 3, "expected three JSON templates"
members = ["execute.go", "go.authority.template.json", "hostapi.go", "main.go",
           "prepare.go", "profile.template.json", "seed.template.json"]
expected = "".join(line for name in members for line in difflib.unified_diff(
    [], (root / name).read_text(encoding="utf-8").splitlines(keepends=True),
    fromfile="/dev/null", tofile="b/" + name))
assert (root / "forward.proposed.diff").read_text(encoding="utf-8") == expected, "forward diff differs from proposed Source bytes"
assert "receipts/W05/W05-99/" in (root / "HANDOFF.md").read_text(encoding="utf-8")
assert "receipts/W05/W05-99" in (root / "SOURCE-MAP.md").read_text(encoding="utf-8")
previous = root.parent.parent / "mu_sdk_trusted_qualification_host_source_codex" / "991a41da6cb146d9a5fae91c438f6d07"
changed = ["main.go", "prepare.go", "execute.go", "profile.template.json"]
for filename, before, after in [
    ("revision.old-to-new.diff", previous, root),
    ("revision.new-to-old.diff", root, previous),
]:
    delta = "".join(line for name in changed for line in difflib.unified_diff(
        (before / name).read_text(encoding="utf-8").splitlines(keepends=True),
        (after / name).read_text(encoding="utf-8").splitlines(keepends=True),
        fromfile=("a/" if before == previous else "b/") + name,
        tofile=("b/" if after == root else "a/") + name))
    assert (root / filename).read_text(encoding="utf-8") == delta, filename
profile = json.loads((root / "profile.template.json").read_text(encoding="utf-8"))
policy = profile["tool_policy"]
assert profile["model_config"]["max_calls"] == 2
assert (policy["max_calls"], policy["read_paths"], policy["write_paths"],
        policy["max_read_bytes"], policy["max_write_bytes"]) == (1, ["evidence.txt"], [], 4096, 4096)
print("STATIC_SOURCE_TEXT_CHECK=PASS; four Go files lexically balanced; three templates parse; forward/revision/inverse diffs exact; no Go compiler invoked")
