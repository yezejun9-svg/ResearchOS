from pathlib import Path
source=Path(__file__).with_name('read_Task69_basis_revision.py').read_text(encoding='utf-8')
old="assert nh['manifest_ref']==nmref"
new="assert Path(nh['manifest_ref']['path']).resolve(strict=True)==Path(nmref['path']).resolve(strict=True) and nh['manifest_ref']['sha256']==nmref['sha256'] and nh['manifest_ref']['bytes']==nmref['bytes']"
assert source.count(old)==1
exec(compile(source.replace(old,new),str(Path(__file__)),'exec'),dict(__name__='__main__',__file__=__file__))
