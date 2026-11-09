import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
COL=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-c495292dee2d4e4fba7bb11a06979907'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
source=json.loads((COL/'source-before.json').read_text(encoding='utf-8'))
raw=(COL/'go-list.stdout').read_text(encoding='utf-8');offset=0;decoder=json.JSONDecoder();packages=[]
while offset<len(raw):
    if raw[offset].isspace():offset+=1;continue
    package,offset=decoder.raw_decode(raw,offset)
    if package.get('ImportPath','').startswith('researchos.local/research-os/'):
        directory=Path(package['Dir']).resolve()
        assert directory.is_relative_to(ROOT)
        relative=directory.relative_to(ROOT)
        assert relative.as_posix()==package['ImportPath'].removeprefix('researchos.local/research-os/')
        current=[ref(p) for p in sorted(directory.glob('*.go')) if p.is_file()]
        missing=[row for row in current if row['path'] not in source]
        packages.append({'import_path':package['ImportPath'],'path':relative.as_posix(),'current_go_files':current,'missing':missing})
gap=[entry for package in packages for entry in package['missing']]
result={'mode':'READ_ONLY_CURRENT_MAIN_PACKAGE_INVENTORY','formal_acceptance':False,'network_calls':0,'historical_proof':ref(COL/'proof.json'),'historical_source_before':ref(COL/'source-before.json'),'go_inventory':ref(COL/'go-list.stdout'),'reader':ref(ROOT/'execution/v2.4/formal_profile_w07.py'),'collector':ref(ROOT/'ops/ci/sources.py'),'source_count':len(source),'packages':packages,'missing_count':len(gap),'missing_files':gap,'finding':'Collector freezes only selected GoFiles/CgoFiles/EmbedFiles for transitive local packages; formal reader additionally requires every current *.go file (including unselected platform variants and tests) in each listed local package. Existing source-before cannot qualify and is retained unchanged.'}
(OUT/'gap_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit':ref(OUT/'gap_audit.json'),'source_count':len(source),'local_packages':len(packages),'missing_count':len(gap),'missing':[entry['path'] for entry in gap]},ensure_ascii=False))
