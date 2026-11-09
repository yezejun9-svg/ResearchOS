from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parent
old = root.parent / 'product-v1-workbench-author'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(old / 'FROZEN.json') == '0146759979ed06a19392881eaaf2f031bbeef951ed0cd1befa2f3b9a97e7195f'
assert sha(old / 'EVIDENCE_MANIFEST.json') == '395af27cf58170054bfce7d184a9233930d7ca8a0338608c03ef8c919272d30a'
frozen = json.loads((old / 'FROZEN.json').read_text(encoding='utf-8'))
manifest = json.loads((old / 'EVIDENCE_MANIFEST.json').read_text(encoding='utf-8'))
assert all(sha(old / item['path']) == item['sha256'] for item in manifest['files'])
pins = frozen['source_sha256'] | frozen['test_sha256']
wt = Path(frozen['worktree'])
assert not (root / 'baseline-review.json').exists()
for name, digest in pins.items():
    assert sha(wt / name) == digest == sha(old / 'source-snapshot' / name)
    for directory in ['baseline', 'candidate']:
        target = root / directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((wt / name).read_bytes())
for name in ['run_pure_checks.py', 'run_vite_build.py', 'run_git_checks.py']:
    shutil.copyfile(old / name, root / name)
qa = root.parent / 'product-v1-workbench-independent-qa-20261104'
inputs = [
    (qa / 'checks01/independent-ui.stdout.raw', 'independent-ui.freeze01.stdout.raw', '85a2418dcb3514db1214126afd9462d391e652586b02609b2af874cfb125cfea'),
    (qa / 'independent-ui.mjs', 'independent-ui.fixture.mjs', None),
    (old / 'FROZEN.json', 'author.freeze01.json', None),
    (old / 'EVIDENCE_MANIFEST.json', 'author.freeze01.manifest.json', None),
    (old / 'AUTHOR-DIAGNOSTICS.json', 'author.freeze01.diagnostics.json', None),
]
copied = []
for source, name, expected in inputs:
    if expected: assert sha(source) == expected
    target = root / 'prior-evidence' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    copied.append({'source': str(source), 'copy': target.relative_to(root).as_posix(), 'sha256': sha(target)})
report = {'old_freeze_sha256': sha(old / 'FROZEN.json'), 'old_manifest_sha256': sha(old / 'EVIDENCE_MANIFEST.json'),
          'old_manifest_pins_verified': len(manifest['files']), 'worktree': str(wt), 'baseline_sha256': pins,
          'qa_inputs': copied, 'all_live10_match': True, 'native_or_model_runs': 0}
(root / 'baseline-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'live_paths': len(pins), 'old_evidence_pins': len(manifest['files']), 'all_match': True}))
