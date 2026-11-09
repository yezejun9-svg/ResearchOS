import hashlib,json,os,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'product-v1-native-qualification-中文-root-01';SOURCE=ROOT/'S';HELPER=HERE/'product-v1-native-helper-build01/buildout/qualification-helper.exe';OUT=HERE/'product-v1-first-native-fixture-preparation.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ordinary(p):
 for q in [p,*p.parents]:
  st=q.lstat();assert not stat.S_ISLNK(st.st_mode) and not (st.st_file_attributes&0x400),str(q)
assert os.name=='nt' and ROOT.resolve().is_relative_to(HERE.resolve()) and not ROOT.exists() and not OUT.exists();ordinary(HERE);ordinary(HELPER)
assert sha(HELPER)=='4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef' and HELPER.stat().st_size==5335552
ROOT.mkdir();SOURCE.mkdir();dest=SOURCE/'qualification-helper.exe'
with HELPER.open('rb') as src,dest.open('xb') as dst:
 while raw:=src.read(65536):assert dst.write(raw)==len(raw)
 dst.flush();os.fsync(dst.fileno())
ordinary(ROOT);ordinary(SOURCE);ordinary(dest);assert sha(dest)==sha(HELPER) and {p.name for p in SOURCE.iterdir()}=={'qualification-helper.exe'}
r=dict(status='ROOT_SYNTHETIC_FIXTURE_PREPARED_NOT_EXECUTION_AUTHORIZATION',qualification_root=str(ROOT),synthetic_source=str(SOURCE),helper_source=str(HELPER),helper=str(dest),helper_sha256=sha(dest),helper_bytes=dest.stat().st_size,initial_source_files=['qualification-helper.exe'],canary_files_created=False,GUI_run_data_root='MUST_BE_SEPARATE_NEW_DIRECTORY_REGISTERED_LATER',ancestor_reparse_check=True,ACL_scope='Existing user workspace inheritance; no independent ACL/isolation qualification claimed. Product private capture directories remain separately verified.',helper_native_model_execution=False,task_submissions=0,formal_increment=0,product_increment=0)
OUT.write_bytes((json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode('utf8'));print(json.dumps(dict(receipt=str(OUT),sha256=sha(OUT),qualification_root=str(ROOT),helper_sha256=sha(dest),execution=False)))
