"""Prepare a narrow trusted W05 branch without touching Main."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = ROOT / 'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e'
source = (ROOT / 'execution/v2.4/formal_case_index.py').read_text(encoding='utf-8')
replacements = [
    ('fixed trusted W05 loader',
     'def _registered_roots(reader, owner, task_id):',
     '''def _w05_profile(reader):
    from types import SimpleNamespace
    source = reader.path("execution/v2.4/formal_profile_w05.py")
    fixed_parent = reader.repo / "execution/v2.4"
    require(source.parent == fixed_parent and not source.is_symlink(),
            "PROFILE_SOURCE", str(source))
    raw_source = source.read_bytes()
    digest = hashlib.sha256(raw_source).hexdigest()
    require(source not in reader.read_hashes or reader.read_hashes[source] == digest,
            "INPUT_CHANGED_DURING_READ", str(source))
    reader.read_hashes[source] = digest
    namespace = {"__name__": "researchos_trusted_w05_profile", "__file__": str(source)}
    exec(compile(raw_source, str(source), "exec"), namespace)
    require(sha256(source) == digest, "INPUT_CHANGED_DURING_READ", str(source))
    return SimpleNamespace(**namespace)


def _registered_roots(reader, owner, task_id):'''),
    ('W05 registered roots',
     'require(task_id in {"W04", "W07"}, "UNSUPPORTED_PROTOCOL", task_id)',
     'require(task_id in {"W04", "W05", "W07"}, "UNSUPPORTED_PROTOCOL", task_id)'),
    ('W05 profile owner',
     'def _verify_owner(reader, owner, task_id, roots, plan_path):\n    if task_id == "W07":',
     'def _verify_owner(reader, owner, task_id, roots, plan_path):\n    if task_id == "W05":\n        return _w05_profile(reader).verify_owner(_profile_api(), reader, owner, roots, plan_path)\n    if task_id == "W07":'),
    ('W05 source dependency snapshot',
     '        _w07_profile(reader)  # Trusted module participates in every dependency/CAS snapshot.',
     '        _w07_profile(reader)  # Trusted module participates in every dependency/CAS snapshot.\n        _w05_profile(reader)  # Trusted W05 profile participates in every dependency/CAS snapshot.'),
    ('W05 fixed owner allow list',
     'require(task_id in {"W04", "W07"}, "UNSUPPORTED_PROTOCOL", "Evidence profile has not been independently implemented for " + task_id)',
     'require(task_id in {"W04", "W05", "W07"}, "UNSUPPORTED_PROTOCOL", "Evidence profile has not been independently implemented for " + task_id)'),
]


def preflight():
    return {name: source.count(old) for name, old, _ in replacements}


if __name__ == '__main__':
    counts = preflight()
    print(counts)
    if any(value != 1 for value in counts.values()):
        raise SystemExit(2)
    changed = source
    for _, old, new in replacements:
        changed = changed.replace(old, new, 1)
    ast.parse(changed)
    with (HERE / 'formal_case_index.w05.proposed.py').open('xb') as out:
        out.write(changed.encode('utf-8'))
    inverse = changed
    for _, old, new in reversed(replacements):
        assert inverse.count(new) == 1
        inverse = inverse.replace(new, old, 1)
    assert inverse == source
    print('AST_OK INVERSE_EXACT')
