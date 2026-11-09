import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'product-v1-native-qualification-producer-author-20261105-rev4/MANIFEST.json':'522a562016d0b94ea4576d956106b08068bbf47449b6f9de01683d12b709b2b2','product-v1-native-qualification-b3-security-review-rev4-20261105/REVIEW.json':'81882201f62245cb3f51b13dc4b0c1af2151768b950730b0c46c1da4bd311ebc','product-v1-native-qualification-wrapper-rev4-review-20261105/review-report.json':'a3395a13a579ea0ab0556c879dfde766e3d978387e68a7965a30384c7fcbf403','product-v1-native-qualification-go01-audit-20261105/REVIEW.json':'03894695ad0f6575a2ab9f04096c8e12bc3a27e662dd1a4aa9553a6e907b8cb2'}
for ref,digest in pins.items():assert sha(HERE/ref)==digest
dirs={Path(k).parts[0] for k in pins}|{'product-v1-native-qualification-producer-author-20261105-rev3','product-v1-native-qualification-producer-test01-passed-20261105'};files=[p for d in dirs for p in (HERE/d).rglob('*') if p.is_file()];assert len(files)<160
p=HERE/'product-v1-qualification-final-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
