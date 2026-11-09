import pathlib,json,hashlib,shutil
E=pathlib.Path(__file__).resolve().parent
T=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r4-independent-review-20261015-tmp')
records=[]
for case in sorted(E.glob('fixture-e2e-*')):
 if not case.is_dir():continue
 original=T/case.name
 dest=case/'observed-operation-copy';dest.mkdir(exist_ok=False)
 for p in sorted((original/'operation').iterdir()):
  if p.is_file():
   copy=dest/p.name;shutil.copyfile(p,copy)
   records.append({'original':str(p),'copy':str(copy),'sha256':hashlib.sha256(copy.read_bytes()).hexdigest(),'bytes':copy.stat().st_size})
 db=original/'data/researchos.sqlite'
 copy=case/'observed-fixture.sqlite';shutil.copyfile(db,copy)
 records.append({'original':str(db),'copy':str(copy),'sha256':hashlib.sha256(copy.read_bytes()).hexdigest(),'bytes':copy.stat().st_size})
obsolete=T/'supervisor-review.exe'
if obsolete.exists():
 obsolete.unlink()
(E/'fixture-output-archive.json').write_text(json.dumps({'records':records,'removed_unused_initial_test_build':str(obsolete),'retained_fixture_roots_for_review':[str(T),'C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015'],'reason':'Remaining native binaries, image ACL fixtures and exact data roots are retained as review/reproduction evidence. No author or previous policy-denied root is touched.'},ensure_ascii=False,indent=2),encoding='utf-8')
print('archived',len(records),'fixture artifacts; removed unused initial test build')
