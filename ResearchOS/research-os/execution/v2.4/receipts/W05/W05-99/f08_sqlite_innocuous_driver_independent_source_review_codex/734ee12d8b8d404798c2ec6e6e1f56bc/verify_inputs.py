from pathlib import Path
import json,hashlib,difflib,re
src=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_preparation_codex/da3c883ec6684c4487dbe36ff45affe4')
out=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_independent_source_review_codex/734ee12d8b8d404798c2ec6e6e1f56bc')
def meta(p):
    b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
mf=meta(src/'manifest.json');hmeta=meta(src/'handoff.json')
assert (mf['sha256'],mf['bytes'])==('7c0d979f80472e3035a9d4c267fe9d42f933870e72e9ed26fd5553c8c41aec4d',9647)
assert (hmeta['sha256'],hmeta['bytes'])==('cf24eb27c506f0e4fb524ab39cf29459433452326bf1e625df86f275fd503f57',1754)
m=json.loads((src/'manifest.json').read_text(encoding='utf-8'))
assert len(m['members'])==31
refs=[]
for ref in m['members']:
    p=Path(ref['path']);a=meta(p)
    assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes'])
    dest=out/'inputs'/p.relative_to(src)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());refs.append(a)
(out/'inputs/manifest.json').write_bytes((src/'manifest.json').read_bytes())
h=json.loads((src/'handoff.json').read_text(encoding='utf-8'))
for key in ['candidate_ref','patch_ref','proof_ref','delivery_contract_ref']:
    ref=h[key];a=meta(Path(ref['path']));assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes'])
before=json.loads((src/'inputs.before.json').read_text(encoding='utf-8'))
assert isinstance(before,list) and len(before)==20
for row in before:
    snap=row['snapshot'];a=meta(Path(snap['path']))
    assert (a['sha256'],a['bytes'])==(snap['sha256'],snap['bytes'])==(row['original']['sha256'],row['original']['bytes'])
base=(src/'inputs/03-sqlite.go').read_bytes();cand=Path(h['candidate_ref']['path']).read_bytes()
patch=Path(h['patch_ref']['path']).read_bytes()
assert patch==(src/'inputs/15-modernc-sqlite-innocuous.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest()=='4d409061e130d8908849ded09a0bc2cd0035c75ddbfd092614756d75b4d90679' and len(patch)==847
b=base.decode('utf-8').splitlines(keepends=True);c=cand.decode('utf-8').splitlines(keepends=True)
delta=difflib.SequenceMatcher(a=b,b=c,autojunk=False)
ops=[x for x in delta.get_opcodes() if x[0]!='equal']
assert len(ops)==2 and all(x[0]=='insert' for x in ops)
inverse=c[:]
for tag,i1,i2,j1,j2 in reversed(ops):inverse[j1:j2]=b[i1:i2]
assert ''.join(inverse).encode('utf-8')==base
# Apply the sealed unified diff independently against exact old-line numbers,
# validating every context and removed line. This is text, not Go or SQL execution.
pl=patch.decode('utf-8').splitlines(keepends=True)
result=[];oldpos=0;hunk_count=0;i=2
while i<len(pl):
    match=re.fullmatch(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n',pl[i])
    assert match is not None
    oldstart,oldcount,newstart,newcount=map(int,match.groups())
    assert oldstart-1>=oldpos
    result.extend(b[oldpos:oldstart-1]);oldpos=oldstart-1
    i+=1;read_old=0;written_new=0
    while i<len(pl) and not pl[i].startswith('@@ '):
        line=pl[i];assert line[:1] in [' ','+','-']
        if line[0] in [' ','-']:assert b[oldpos]==line[1:];oldpos+=1;read_old+=1
        if line[0] in [' ','+']:result.append(line[1:]);written_new+=1
        i+=1
    assert (read_old,written_new)==(oldcount,newcount)
    hunk_count+=1
result.extend(b[oldpos:])
assert hunk_count==2 and ''.join(result).encode('utf-8')==cand
diff=''.join(difflib.unified_diff(b,c,fromfile='fixed-v1.60.1-snapshot',tofile='candidate',n=5))
(out/'actual-full-source-diff.txt').write_text(diff,encoding='utf-8')
record={'listed_members':31,'physical_with_manifest':32,'manifest':mf,'handoff':hmeta,'all_member_sha_bytes_verified':True,'member_refs':refs,'complete_original_source':meta(src/'inputs/03-sqlite.go'),'complete_candidate':h['candidate_ref'],'original_module_cache_or_Main_not_read':True,'origin_is_snapshot_and_metadata_not_module_zip_authentication':True,'source_full_bytes_loaded':True,'source_lines':len(c),'whole_inverse_byte_equal':True,'exact_sealed_two_hunk_application':True,'historical_patch_identical':True,'delta':[{'tag':tag,'old_start':i1+1,'old_end':i2,'new_start':j1+1,'new_end':j2} for tag,i1,i2,j1,j2 in ops],'Go_AST_compile_or_SQL_executed':False}
(out/'input-verification.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='member_refs'},ensure_ascii=True))
print('FULL_DIFF');print(diff)
for name,a,z in [('inputs/14-sqlite_g_0000000000060000.go',103560,103595),('inputs/01-go.mod',1,30),('inputs/06-go.mod',1,40),('inputs/08-LICENSE',1,60),('inputs/09-LICENSE-SQLITE',1,50),('inputs/10-LICENSE-SQLITE_VEC',1,60),('inputs/11-LICENSE-3RD-PARTY.md',1,90),('inputs/07-func_test.go',1,300)]:
    p=src/name;lines=p.read_text(encoding='utf-8').splitlines()
    print('FILE '+name)
    for n in range(a,min(z,len(lines))+1):print(str(n)+':'+lines[n-1])
for n,line in enumerate((src/'inputs/02-go.sum').read_text(encoding='utf-8').splitlines(),1):
    if line.startswith('modernc.org/sqlite v1.60.1'):print('GO_SUM '+str(n)+':'+line)

