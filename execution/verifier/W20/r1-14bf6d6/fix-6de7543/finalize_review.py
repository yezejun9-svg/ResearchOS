from pathlib import Path
import hashlib,json,subprocess,zipfile
OUT=Path(__file__).resolve().parent; PRIOR=OUT.parent; ROOT=PRIOR.parents[3]
REV='6de7543da751ace1d2d603a751f520e5fed71caa'; AUTHOR='c21e723'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
old=json.loads((PRIOR/'index.json').read_text());assert sha(PRIOR/'index.json')=='fad9e6f1ac1fa49ef06d7eb59b753eb7356fefcb53438b426e8948f5f4780ae6'
for r in old['files']:assert sha(PRIOR/r['path'])==r['sha256']
prefix='execution/receipts/W20/release-package/r1-fix/'
names=git('ls-tree','-r','--name-only',AUTHOR,'--',prefix).decode().splitlines();assert len(names)==12
target=OUT/'author-evidence';target.mkdir(exist_ok=True);auth=[]
for name in names:
 raw=git('show',AUTHOR+':'+name);p=target/Path(name).name;p.write_bytes(raw);auth.append({'source_path':name,'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':len(raw)})
summary=json.loads((target/'summary.json').read_text());assert summary['source_commit']==REV
assert sha(target/summary['archive'])==summary['archive_sha256']==sha(OUT/'build-first.zip')==sha(OUT/'build-second.zip')
packagecheck=json.loads((target/summary['package_check']).read_text());put(OUT/'author-evidence-audit.json',{'revision':git('rev-parse',AUTHOR).decode().strip(),'files':auth,'summary':summary,'package_check':packagecheck})
source_rows=[]
with zipfile.ZipFile(OUT/'build-first.zip') as archive:
 for name in archive.namelist():
  if name=='release-manifest.json' or name.startswith(('bin/','web/dist/','licenses/')):continue
  source='ops/release/'+name.split('/')[-1] if name.startswith('scripts/') else name
  raw=git('show',REV+':'+source);actual=archive.read(name)
  assert actual==raw,(name,source)
  source_rows.append({'archive_path':name,'git_path':source,'sha256':hashlib.sha256(raw).hexdigest()})
put(OUT/'packaged-source-audit.json',{'source_revision':REV,'files':source_rows,'matched':len(source_rows),'normalization':'None: exact Git blob bytes'})
preserved=[]
for probe in ['fixture-probe','fixture-probe-v2']:
 for label in ['a','b']:
  base=OUT/probe/('data-'+label);assert (base/'researchos.sqlite').is_file()
  for p in sorted(base.rglob('*')):
   if p.is_file():
    preserved.append({'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
    if p.suffix=='.log':
     destination=OUT/probe/'preserved-native-logs'/label/p.relative_to(base);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(p.read_bytes())
put(OUT/'data-before-cleanup.json',{'note':'All four disposable databases survived valid stop; only independent verifier working data is removed after hashing. Native logs copied outside cleanup targets.','files':preserved})
args=['powershell.exe','-NoProfile','-File',str(OUT/'cleanup_owned.ps1')]
with (OUT/'cleanup.stdout.log').open('wb') as stdout,(OUT/'cleanup.stderr.log').open('wb') as stderr:r=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=60)
put(OUT/'cleanup-command.json',{'argv':args,'exit_code':r.returncode});assert r.returncode==0
build=json.loads((OUT/'build-assertions.json').read_text());fixture=json.loads((OUT/'fixture-probe-v2/assertions.json').read_text());first=json.loads((OUT/'fixture-probe/assertions.json').read_text())
assert len(build)==11 and len(fixture)==34 and all(r['status']=='PASS' for r in build+fixture)
assert len(first)==16 and sum(r['status']=='FAIL' for r in first)==1
handle=PRIOR/'fix-0916a5e';external=[{'path':p.relative_to(PRIOR).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(handle.iterdir()) if p.is_file()]
review={'verdict':'PASS_R1_FIXTURE_PACKAGE_SLICE','source_revision':REV,'author_evidence_revision':git('rev-parse',AUTHOR).decode().strip(),'archive_sha256':sha(OUT/'build-first.zip'),'scope':'Independent fixture package slice only; no W20, A15, clean-Windows, final-schema migration or LIVE qualification.','resolved_findings':['R1-SOURCE-001: frozen Git input guard rejects modified docs, registry and untracked source; actual two clean builds match author artifact and leave checkout clean.','R1-IDENTITY-001: held process handle plus OS creation time, launch instance and data/release bindings refuse five mismatches and stale identity, retain records, preserve unrelated host and data.'],'independent_checks':{'build_pass':len(build),'final_fixture_pass':len(fixture),'packaged_sources_match_frozen_git':len(source_rows)},'first_fixture_attempt':{'pass':15,'fail':1,'failure':'wrong-creation-both-alive','cause':'Not established. The original urllib two-second health helper discarded exception detail. Wrong creation identity was refused and later valid cleanup of both original processes succeeded.','disposition':'Original failure retained verbatim. Improved observation only: direct loopback HTTP with response/error/duration plus native identity check after every negative. Same product/package under fresh owned instances passed all 34 checks.'},'limitations':['Author 25-case package suite and seven input negatives are archived and hash checked, not all independently replayed.','27 dependency license gaps remain disclosed.','Clean Windows and schema13-to-final upgrade not run/implemented; normal LIVE stays closed.'],'prior_review_sha256':sha(PRIOR/'review.json'),'prior_index_sha256':sha(PRIOR/'index.json'),'prior_index_files_unchanged':len(old['files']),'held_handle_prefinal_evidence':external,'cleanup':'Only own temporary checkout, extracted fixture and four disposable fixture data directories removed; commands and native logs retained.'}
put(OUT/'review.json',review)
(OUT/'review.md').write_text('# R1 fixture package independent review\n\nPASS_R1_FIXTURE_PACKAGE_SLICE at '+REV+'.\n\nThe two P1 findings are resolved for this slice. Two independent offline builds match the author archive SHA-256 '+sha(OUT/'build-first.zip')+'. All 385 manifest entries were checked; all '+str(len(source_rows))+' bundled source/script entries match the frozen Git version with exact Git blob bytes. Three modified/untracked-input attempts are rejected. Eleven build assertions and 34 final fixture assertions pass.\n\nWrong PID, creation time, copied identity/data binding, launch GUID and release root each refuse stopping, retain the identity record and leave both owned hosts alive. Valid stop kills only the intended held process and preserves its database. A stale stopped identity also refuses.\n\nThe first fixture attempt remains 15 PASS / 1 FAIL: its health-only assertion failed after correctly refusing the wrong creation time. The original helper did not retain the HTTP exception, so the cause is undiagnosed. A fresh run of the same product using recorded direct HTTP observations and independent OS process identity checks passes; no product patch occurred between these runs.\n\nThis approves only the R1 fixture-package slice. It does not qualify W20, A15, clean Windows, final-schema upgrades or LIVE. The manifest still discloses 27 license gaps. Author-only tests are identified separately in review.json.\n',encoding='utf-8')
for row in old['files']:assert sha(PRIOR/row['path'])==row['sha256']
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='index.json']
put(OUT/'index.json',{'source_revision':REV,'verdict':review['verdict'],'external_evidence':external,'files':files})
print(json.dumps({'verdict':review['verdict'],'review_sha256':sha(OUT/'review.json'),'index_sha256':sha(OUT/'index.json'),'files':len(files),'source_files':len(source_rows)}))
