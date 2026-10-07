"""One integrity check: missing, outside, empty and altered evidence fail closed."""
import importlib.util
from pathlib import Path
import tempfile

spec = importlib.util.spec_from_file_location('acceptance_audit', Path(__file__).resolve().parents[2] / 'ops/ci/acceptance_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
with tempfile.TemporaryDirectory(prefix='researchos-audit-check-') as directory:
    root = Path(directory)
    sample = root / 'raw.json'
    sample.write_bytes(b'{"actual":true}')
    frozen = {'raw.json': audit.digest(sample)}
    audit.check_hashes(root, frozen)
    sample.write_bytes(b'{"actual":false}')
    for inventory in (frozen, {}, {'missing': frozen['raw.json']}, {str(root.parent / 'outside'): frozen['raw.json']}):
        try:
            audit.check_hashes(root, inventory)
        except ValueError:
            continue
        raise AssertionError('invalid evidence accepted')
print('PASS: original bytes accepted; changed, empty, missing and outside evidence rejected')
