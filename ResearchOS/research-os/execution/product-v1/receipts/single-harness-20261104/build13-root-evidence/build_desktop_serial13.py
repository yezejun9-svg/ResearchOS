import argparse,hashlib,json,os,runpy,subprocess,sys
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
HEAD='998fc6330ba735056cd31f8ebf68dd50a8251c1b';BUILDER_SHA='8654e7955c12de11a80149d6cdfcb0e58d8ff4df69cadc5fc9d70cd97fe4f8e3';SOURCE_UNION_SHA='946cf0c40661cbd686387e4f1afa5426d0080dfd677607f8eef720d5eacb51e5'
WT=ROOT/'.local/worktrees/product-v1-build-13-20261105'
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/build13-scope'
QUAL=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-qualification-中文-root-01')
HELPER=HERE/'product-v1-native-helper-build01/buildout/qualification-helper.exe';HELPER_SHA='4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef'
def git(*a):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*a],cwd=ROOT).decode().strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=json.loads((ROOT/'execution/v2.4/checkpoint.json').read_bytes());assert cp['current_Main_HEAD']==HEAD and git('rev-parse','HEAD')==HEAD
state=json.loads((ROOT/'execution/product-v1/state.json').read_bytes())
assert all(any(x['scope_id']==i and x['status']=='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED' for x in state['active_scopes']) for i in ('PRODUCT_V1_QUALIFICATION_BUILD_BINDING','PRODUCT_V1_NATIVE_PRELAUNCH_INTENT'))
pins={}
for item in state['integrated_source']:
 for ref,digest in item['source_sha256'].items():pins[ref]=digest
assert hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()==SOURCE_UNION_SHA
if len(sys.argv)<2:raise SystemExit('missing pinned desktop build script')
build=Path(sys.argv[1]).resolve();assert build==WT/'apps/desktop/build-development.py' and sha(build)==BUILDER_SHA
p=argparse.ArgumentParser();p.add_argument('--go',required=True);p.add_argument('--node',required=True);p.add_argument('--electron-dist',required=True);p.add_argument('--module-cache',required=True);p.add_argument('--web-modules',required=True);p.add_argument('--mu-common',required=True);p.add_argument('--output',required=True);p.add_argument('--receipts',required=True);p.add_argument('--qualification-root',required=True);p.add_argument('--qualification-helper',required=True);p.add_argument('--qualification-helper-sha256',required=True);a=p.parse_args(sys.argv[2:])
web=Path(a.web_modules).resolve();allowed=ROOT/'.local/product-v1-build-inputs-20261104'
assert web.is_relative_to(allowed) and web.is_dir()
assert Path(a.go)==ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
assert Path(a.node)==Path('C:/nvm4w/nodejs/node.exe')
assert Path(a.electron_dist)==ROOT/'apps/desktop/node_modules/electron/dist'
assert Path(a.module_cache)==ROOT/'.local/tools/gopath/pkg/mod'
assert Path(a.mu_common)==ROOT and Path(a.output)==WT/'.local/desktop-v1-build-13'
assert Path(a.receipts)==OUT/'producer-13' and Path(a.qualification_root)==QUAL
assert Path(a.qualification_helper)==HELPER and a.qualification_helper_sha256==HELPER_SHA
assert sha(HELPER)==HELPER_SHA
os.environ['GOMAXPROCS']='1';sys.argv=[str(build),*sys.argv[2:]]
runpy.run_path(str(build),run_name='__main__')
