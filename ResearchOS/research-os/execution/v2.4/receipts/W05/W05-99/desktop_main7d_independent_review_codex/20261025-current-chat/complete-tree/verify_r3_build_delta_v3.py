# Retain ordinal 031: go-list also includes one generated cache source whose
# bytes are identical but whose fresh client-stage path moved with the fixture.
from pathlib import Path
v2=Path(__file__).with_name('verify_r3_build_delta_v2.py').read_text(encoding='utf-8')
oldblock="""assert len(new_paths)==len(old_paths)==1
new_fixture=next(iter(new_paths));old_fixture=next(iter(old_paths))
assert pathlib.Path(new_fixture).is_relative_to(W/'.local') and pathlib.Path(new_fixture).as_posix().endswith('/fixtures/negative-child.go')
assert (by[new_fixture]['sha256'],by[new_fixture]['bytes'])==(oldby[old_fixture]['sha256'],oldby[old_fixture]['bytes'])"""
newblock="""assert len(new_paths)==len(old_paths)==2
newstage=B.with_name(B.name+'-client-stage')
oldbundle=pathlib.Path(oldmanifest['bundle_root']);oldstage=oldbundle.with_name(oldbundle.name+'-client-stage')
newrel={pathlib.Path(p).relative_to(newstage).as_posix():by[p] for p in new_paths}
oldrel={pathlib.Path(p).relative_to(oldstage).as_posix():oldby[p] for p in old_paths}
assert newrel.keys()==oldrel.keys()=={'fixtures/negative-child.go','go-cache/be/bec631f14225ef8825cf3ddadc4d0c2f47fcce37005695bc5f76e2991ff3d91b-d'}
for relative,row in newrel.items():assert (row['sha256'],row['bytes'])==(oldrel[relative]['sha256'],oldrel[relative]['bytes'])
new_fixture=str(newstage/'fixtures/negative-child.go')"""
assert v2.count('exec(compile(')==1
v2=v2.replace('exec(compile(',"assert original.count(oldblock)==1\noriginal=original.replace(oldblock,newblock)\nexec(compile(")
exec(compile(v2,__file__,'exec'))
