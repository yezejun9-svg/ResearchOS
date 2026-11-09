import argparse,hashlib,json,stat
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(root,p):
 p=p.resolve();assert p.is_relative_to(root);return p.relative_to(root).as_posix()
def regular(p):
 s=p.lstat();return p.is_file() and not p.is_symlink() and not (s.st_file_attributes&0x400)
p=argparse.ArgumentParser();p.add_argument('--selection',required=True);p.add_argument('--sha',required=True);p.add_argument('--target',required=True);a=p.parse_args()
selection=Path(a.selection);assert sha(selection)==a.sha;spec=json.loads(selection.read_bytes())
if isinstance(spec,list):spec={'root':str(selection.parent),'files':spec}
source=Path(spec.get('root') or spec.get('base_directory')).resolve();assert source.is_relative_to(Path(__file__).resolve().parent)
target=ROOT/a.target;assert target.resolve().is_relative_to((ROOT/'execution/product-v1/receipts').resolve()) and not target.exists(),'Inspect prior archive; never blindly overwrite'
files={source/f for f in spec.get('root_files',[])}|{source/f for f in spec.get('selected_files',[])}|{selection}
for d in spec.get('include_directories',[]):
 tree=source/d;assert tree.is_dir() and tree.resolve().is_relative_to(source)
 for f in tree.rglob('*'):
  assert not f.is_symlink() and not f.is_junction()
  if f.is_file():files.add(f)
for entry in spec.get('files',[]):
 if isinstance(entry,str):f=source/entry
 else:
  f=source/entry.get('relative_path',entry.get('path',''));assert sha(f)==entry['sha256']
 files.add(f)
for f in files:
 r=rel(source,f);assert regular(f),r
 assert not {'node_modules','gocache','modcache','cache','tmp'}.intersection(Path(r).parts),r
 assert f.suffix.lower() not in {'.exe','.dll','.sqlite','.db'},r
assert sum(f.stat().st_size for f in files)<32*1024*1024
rows=[dict(path=rel(source,f),sha256=sha(f),bytes=f.stat().st_size) for f in sorted(files)]
target.mkdir(parents=True)
for row in rows:
 f=source/row['path'];assert sha(f)==row['sha256'];dest=target/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes());assert sha(dest)==row['sha256']
manifest=dict(schema='researchos.product-v1-root-evidence-archive/1',source=str(source),selection_sha256=a.sha,original_source_preserved=True,files=rows)
(target/'ROOT_ARCHIVE.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(target=str(target),files=len(rows),bytes=sum(r['bytes'] for r in rows),manifest_sha256=sha(target/'ROOT_ARCHIVE.json'))))
