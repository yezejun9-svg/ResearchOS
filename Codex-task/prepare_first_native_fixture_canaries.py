import ctypes, hashlib, json, os, stat
from ctypes import wintypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE / 'product-v1-first-native-fixture-preparation.json'
OUT = HERE / 'product-v1-first-native-fixture-canaries-preparation.json'
INTENT = HERE / 'product-v1-first-native-fixture-canaries-intent.json'
EXPECTED_OLD = 'e2c78d439d6b7dd69a224350d0f6cc560c98ed8594f163310dce0785c84ae7dc'
HELPER_SHA = '4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef'
FILES = {
    'README.md': b'ResearchOS synthetic qualification workspace. Files contain fixed test data only.\n',
    'probe.txt': b'RESEARCHOS_SYNTHETIC_READ_CANARY_20261105_01\n',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ordinary(path):
    for p in [path, *path.parents]:
        s = p.lstat()
        assert not stat.S_ISLNK(s.st_mode) and not (s.st_file_attributes & 0x400), str(p)

def exclusive_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    with path.open('xb') as f:
        assert f.write(raw) == len(raw)
        f.flush()
        os.fsync(f.fileno())
    assert path.read_bytes() == raw

def sddl(path):
    adv = ctypes.WinDLL('advapi32', use_last_error=True)
    adv.GetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    adv.GetFileSecurityW.restype = wintypes.BOOL
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(wintypes.DWORD)]
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = wintypes.BOOL
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    needed = wintypes.DWORD()
    adv.GetFileSecurityW(str(path), 7, None, 0, ctypes.byref(needed))
    assert needed.value > 0
    buf = ctypes.create_string_buffer(needed.value)
    assert adv.GetFileSecurityW(str(path), 7, buf, len(buf), ctypes.byref(needed)), ctypes.get_last_error()
    output = wintypes.LPWSTR()
    assert adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(buf, 1, 7, ctypes.byref(output), None), ctypes.get_last_error()
    try:
        return output.value
    finally:
        kernel.LocalFree(ctypes.cast(output, ctypes.c_void_p))

assert os.name == 'nt' and sha(OLD) == EXPECTED_OLD
old = json.loads(OLD.read_bytes())
root = Path(old['qualification_root'])
source = Path(old['synthetic_source'])
assert root == HERE / 'product-v1-native-qualification-中文-root-01'
assert source == root / 'S' and root.resolve().is_relative_to(HERE.resolve())
assert not OUT.exists() and not INTENT.exists()
ordinary(source)
assert {p.name for p in source.iterdir()} == {'qualification-helper.exe'}
helper = source / 'qualification-helper.exe'
ordinary(helper)
assert helper.is_file() and sha(helper) == HELPER_SHA and helper.stat().st_size == 5335552
expected = {name: {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)} for name, raw in FILES.items()}
exclusive_json(INTENT, dict(status='ROOT_FIXED_SYNTHETIC_CANARIES_INTENT_ONLY', prior_preparation_sha256=EXPECTED_OLD, qualification_root=str(root), synthetic_source=str(source), files=expected, no_execution=True))
for name, raw in FILES.items():
    path = source / name
    with path.open('xb') as f:
        assert f.write(raw) == len(raw)
        f.flush()
        os.fsync(f.fileno())
    ordinary(path)
    assert path.read_bytes() == raw
assert {p.name for p in source.iterdir()} == {'qualification-helper.exe', *FILES}
assert sha(helper) == HELPER_SHA and sha(OLD) == EXPECTED_OLD
inventory = {p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(source.iterdir())}
receipt = dict(status='ROOT_SYNTHETIC_FIXTURE_CANARIES_PREPARED_NOT_EXECUTION_AUTHORIZATION', prior_preparation_sha256=EXPECTED_OLD, intent_sha256=sha(INTENT), qualification_root=str(root), synthetic_source=str(source), exact_initial_inventory=inventory, source_security_sddl={str(p): sddl(p) for p in [root, source, helper, *(source/n for n in FILES)]}, ancestor_reparse_check=True, acl_claim='Observed existing inherited owner/group/DACL only; no independent sandbox/ACL qualification.', production_source_or_build_modified=False, helper_native_model_execution=False, task_submissions=0, formal_increment=0, product_increment=0)
exclusive_json(OUT, receipt)
print(json.dumps(dict(receipt=str(OUT), sha256=sha(OUT), files=inventory, execution=False), ensure_ascii=False))
