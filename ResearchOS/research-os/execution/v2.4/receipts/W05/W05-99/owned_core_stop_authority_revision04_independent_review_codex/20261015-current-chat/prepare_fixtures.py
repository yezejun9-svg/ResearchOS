import pathlib,hashlib,json,difflib
E=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_source_codex/20261015-current-chat'
W=R/'.local/worktrees/owned-core-stop-authority-r4-20261015'
T=R/'.local/owned-core-stop-r4-independent-review-20261015-tmp'
C=pathlib.Path('C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015')
C.mkdir(parents=True,exist_ok=False)
T.mkdir(parents=True,exist_ok=True)
(T/'gotmp').mkdir(exist_ok=True)
lineage=[]
def copy_transform(src,dst,transform):
    raw=src.read_bytes();before=raw.decode('utf-8');after=transform(before)
    dst.write_text(after,encoding='utf-8',newline='\n')
    diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(src),tofile=str(dst)))
    (E/(dst.name+'.patch')).write_text(diff,encoding='utf-8')
    lineage.append({'source':str(src),'source_sha256':hashlib.sha256(raw).hexdigest(),'copy':str(dst),'copy_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'diff':dst.name+'.patch'})
copy_transform(A/'fixture_parent_r4.go',E/'fixture_parent_r4.go',lambda x:x)
def harness(x):
    x=x.replace('owned-core-stop-authority-r4-20261015-tmp','owned-core-stop-r4-independent-review-20261015-tmp')
    x=x.replace('researchos-fixture-cache/owned-core-stop-authority-r4-20261015','researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015')
    x=x.replace('data=Path(r"C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015")/CASE.name/"data"', 'data=Path(r"'+str(T)+'")/CASE.name/"data"')
    x=x.replace('if MODE not in (','if MODE not in (',1)
    return x
copy_transform(A/'fixture_e2e_r4.py',E/'fixture_e2e_review.py',harness)
source=W/'ops/supervisor/owned_core_handle_windows_test.go'
dest=E/'owned_core_handle_review_windows_test.go'
def tests(x):
    x=x.replace('t.TempDir()', 'reviewFixtureDir(t)')
    return x+'\nfunc reviewFixtureDir(t *testing.T) string { t.Helper(); p,err:=os.MkdirTemp("'+str(C).replace('\\','/')+'", "native-"); if err!=nil {t.Fatal(err)}; return p }\n'
copy_transform(source,dest,tests)
(E/'overlay.json').write_text(json.dumps({'Replace':{str(source):str(dest)}},indent=2),encoding='utf-8')
(E/'fixture-lineage.json').write_text(json.dumps(lineage,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(lineage,ensure_ascii=False,indent=2))
