import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'product-v1-native-preparation-wiring-author-20261105-final/MANIFEST.json':'03a65caafda8400991dcf5793538bb02171257d3d2c8d4f174b5c67fc86525b7','product-v1-native-preparation-wiring-final-review-20261105/review-report.json':'c5875e4b26d3041441bfbdecf14007581dd17651ae3625b8c829d1f8a0d5781c'}
for ref,digest in pins.items():assert sha(HERE/ref)==digest
dirs={Path(k).parts[0] for k in pins}|{'product-v1-native-preparation-wiring-prereview-20261105','product-v1-native-preparation-test01-correction-review-20261105','product-v1-native-preparation-wiring-author-20261105-rev1'};files=[p for d in dirs for p in (HERE/d).rglob('*') if p.is_file()]
files += [HERE/n for n in ['prepare_preparation_test01_overlay.py','derive_preparation_test01_rev2.py','prepare_preparation_overlay_directories.py','product-v1-native-preparation-overlay-directory-setup.json']];assert len(files)<150
p=HERE/'product-v1-preparation-final-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
