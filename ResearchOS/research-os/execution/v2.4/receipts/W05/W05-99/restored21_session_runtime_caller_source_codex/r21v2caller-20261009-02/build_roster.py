"""Source-only derivation of the exact 63-path union from reviewed inputs."""
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent
C = json.loads((N / 'contract.json').read_bytes())


def exact(ref):
    path = Path(ref['path']).resolve()
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ref['sha256']
    assert 'bytes' not in ref or len(raw) == ref['bytes']
    return json.loads(raw)


def safe(name):
    rel = PurePosixPath(name)
    assert name == rel.as_posix() and not rel.is_absolute()
    assert len(rel.parts) >= 2 and all(part not in ('', '.', '..') for part in rel.parts)
    assert '\\' not in name and ':' not in name and '\0' not in name


def main():
    assert len(sys.argv) == 1 and not (N / 'exact-source-roster.json').exists()
    old = exact(C['h20_source_overlay'])['sources']
    new = exact(C['a21_v2_overlay'])['files']
    assert len(old) == 61 and len(new) == 5
    composed = {**old, **new}
    assert len(composed) == 63
    for name, ref in composed.items():
        safe(name)
        path = Path(ref['path']).resolve()
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == ref['sha256'] and len(raw) == ref['bytes']
    payload = {'schema': 'researchos.restored21-v2-exact-composed-source-roster.v1',
               'accepted_h20_count': len(old), 'a21_overlay_count': len(new),
               'composed_count': len(composed), 'sources': {k: composed[k] for k in sorted(composed)}}
    path = N / 'exact-source-roster.json'
    with path.open('xb') as stream:
        stream.write((json.dumps(payload, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    raw = path.read_bytes()
    print(json.dumps({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
