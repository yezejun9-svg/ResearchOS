from pathlib import Path
import re

root = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-normal-home-binding-20261105\adapters\runtime")
sections = {
    "codex_qualification_windows.go": [
        ("// The Host-supplied OS-account NormalHome", "func qualificationSHA(s string) bool {")
    ],
    "codex_qualification_windows_test.go": [
        ("func TestQualificationNormalHomeSpelling(t *testing.T) {", "func TestCodexNativeQualificationEnsureIsSingleUseAndBound(t *testing.T) {")
    ],
    "codex_qualification_capture_windows_test.go": [
        ("func TestQualificationNormalHomeIntentSpelling(t *testing.T) {", "func TestQualificationPrelaunchIntentProvenanceAndMutation(t *testing.T) {")
    ],
}
for name, spans in sections.items():
    path = root / name
    with path.open("r", encoding="utf-8", newline="") as stream:
        text = stream.read()
    for start, end in spans:
        if text.count(start) != 1 or text.count(end) != 1:
            raise RuntimeError(f"nonunique markers: {name}")
        i, j = text.index(start), text.index(end)
        before, block, after = text[:i], text[i:j], text[j:]
        block = re.sub(r"(?m)^(    )+", lambda m: "\t" * (len(m.group()) // 4), block)
        text = before + block + after
    if name == "codex_qualification_windows.go":
        text = text.replace("}\n// The Host-supplied", "}\n\n// The Host-supplied", 1)
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)
