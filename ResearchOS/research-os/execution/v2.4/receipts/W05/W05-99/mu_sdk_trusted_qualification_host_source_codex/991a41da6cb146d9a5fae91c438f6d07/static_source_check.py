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
print("STATIC_SOURCE_TEXT_CHECK=PASS; four Go files lexically balanced; three templates parse; forward diff exact; no Go compiler invoked")
