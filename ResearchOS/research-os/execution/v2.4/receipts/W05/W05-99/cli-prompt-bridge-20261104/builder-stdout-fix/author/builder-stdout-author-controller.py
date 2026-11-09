"""One-file fix plus tests against extracted actual AST; no native commands run."""
import ast
import datetime
import hashlib
import io
import json
import pathlib
import py_compile
import shutil
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock

ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-builder-stdout-20261104')
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
SOURCE=ROOT/'apps/desktop/build-validator.py'
SCOPE=MAIN/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/builder-stdout-fix'
OUT=SCOPE/'author'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')

lock=json.loads((MAIN/'execution/toolchains/locked.json').read_bytes())
python=lock['tools']['python']
if pathlib.Path(sys.executable).resolve()!=pathlib.Path(python['path']).resolve() or sha(pathlib.Path(python['path']))!=python['sha256']:raise SystemExit('locked Python mismatch')
scope=json.loads((SCOPE/'scope.json').read_bytes())
if scope['source_paths']!=['apps/desktop/build-validator.py']:raise SystemExit('unexpected scope')
OUT.mkdir(exist_ok=True)
before=SOURCE.read_bytes()
text=before.decode('utf-8')
replacements=[
    ('def run(name, argv, cwd=ROOT, timeout=120):','def run(name, argv, cwd=ROOT, timeout=120, *, decode_stdout=True):'),
    ("return stdout.decode('utf-8')","return stdout.decode('utf-8') if decode_stdout else stdout"),
    ("run('web-module-junction',['cmd','/c','mklink','/J',str(web/'node_modules'),str(pathlib.Path(args.web_modules).resolve())])", "run('web-module-junction',['cmd','/c','mklink','/J',str(web/'node_modules'),str(pathlib.Path(args.web_modules).resolve())],decode_stdout=False)"),
]
for old,new in replacements:
    if text.count(old)!=1:raise SystemExit('source anchor count mismatch: '+old)
    text=text.replace(old,new)
write_json(OUT/'inputs.json',{'base_head':scope['base_head'],'source_path':str(SOURCE),'source_before_sha256':hashlib.sha256(before).hexdigest(),'scope_sha256':sha(SCOPE/'scope.json'),'tool':python,'argv':sys.argv,'cwd':str(ROOT),'measurement_mode':'PURE_AST_MOCK','no_native_commands':True})
(OUT/'build-validator.before.py').write_bytes(before)
SOURCE.write_text(text,encoding='utf-8',newline='\n')
tree=ast.parse(SOURCE.read_text(encoding='utf-8'),filename=str(SOURCE))
main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
run_node=next(node for node in main.body if isinstance(node,ast.FunctionDef) and node.name=='run')
put_node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='put')
stream_node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='stream_json')
calls=[node for node in ast.walk(main) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run']
raw_calls=[node for node in calls if any(k.arg=='decode_stdout' and isinstance(k.value,ast.Constant) and k.value.value is False for k in node.keywords)]
if len(raw_calls)!=1 or not isinstance(raw_calls[0].args[0],ast.Constant) or raw_calls[0].args[0].value!='web-module-junction':raise SystemExit('raw stdout escaped junction call')
if [arg.arg for arg in run_node.args.kwonlyargs]!=['decode_stdout'] or run_node.args.kw_defaults[0].value is not True:raise SystemExit('strict default keyword signature changed')
compiled=compile(ast.fix_missing_locations(ast.Module(body=[put_node,stream_node,run_node],type_ignores=[])),str(SOURCE),'exec')
ENV={key:'fixture-only' for key in ['GOTOOLCHAIN','GOENV','GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','GOPROXY','GOSUMDB']}
OEM=b'\xc1\xb4\xbd\xd3 OEM stdout\r\n'
STDERR=b'raw fixture stderr\xff'

class ActualRunMockTests(unittest.TestCase):
    def bind(self,name,code=0,stdout=OEM,timeout=False):
        receipts=OUT/'mock-checks'/name;receipts.mkdir(parents=True,exist_ok=False)
        failure=subprocess.TimeoutExpired(['mock-command'],0.01,output=stdout,stderr=STDERR) if timeout else None
        mock=Mock(side_effect=failure) if timeout else Mock(return_value=types.SimpleNamespace(returncode=code,stdout=stdout,stderr=STDERR))
        namespace={'ROOT':ROOT,'datetime':datetime,'subprocess':types.SimpleNamespace(run=mock,TimeoutExpired=subprocess.TimeoutExpired),
                   'receipts':receipts,'env':ENV.copy(),'invocations':[],'json':json}
        exec(compiled,namespace)
        return namespace,receipts,mock
    def evidence(self,namespace,receipts,code,stdout):
        self.assertEqual((receipts/'fixture.stdout').read_bytes(),stdout)
        self.assertEqual((receipts/'fixture.stderr').read_bytes(),STDERR)
        row=json.loads((receipts/'fixture.invocation.json').read_bytes())
        self.assertEqual(row['exit'],code);self.assertEqual(row['actualargv'],['mock-command'])
        self.assertEqual(namespace['invocations'],[row])
        return row
    def test_oem_success_raw_false_preserves_bytes_and_row(self):
        namespace,receipts,mock=self.bind('oem-raw')
        result=namespace['run']('fixture',['mock-command'],decode_stdout=False)
        self.assertIsInstance(result,bytes);self.assertEqual(result,OEM)
        self.evidence(namespace,receipts,0,OEM);self.assertFalse((receipts/'stopped.json').exists())
        mock.assert_called_once_with(['mock-command'],cwd=ROOT,env=namespace['env'],capture_output=True,timeout=120)
    def test_oem_success_default_remains_strict_utf8(self):
        namespace,receipts,_=self.bind('oem-strict')
        with self.assertRaises(UnicodeDecodeError):namespace['run']('fixture',['mock-command'])
        self.evidence(namespace,receipts,0,OEM)
    def test_nonzero_raw_false_refuses_before_return(self):
        namespace,receipts,_=self.bind('nonzero-raw',code=7)
        with self.assertRaises(SystemExit) as error:namespace['run']('fixture',['mock-command'],decode_stdout=False)
        self.assertEqual(error.exception.code,7)
        row=self.evidence(namespace,receipts,7,OEM)
        self.assertEqual(json.loads((receipts/'stopped.json').read_bytes()),{'first_unexpected':row,'source_acceptance':False})
    def test_go_json_default_returns_text_and_parses(self):
        raw='{"ImportPath":"中文/module"}\n{"Name":"main"}\n'.encode('utf-8')
        namespace,receipts,_=self.bind('go-json',stdout=raw)
        result=namespace['run']('fixture',['mock-command'])
        self.assertIsInstance(result,str)
        self.assertEqual(list(namespace['stream_json'](result)),[{'ImportPath':'中文/module'},{'Name':'main'}])
        self.evidence(namespace,receipts,0,raw)
    def test_timeout_raw_false_records_124_then_refuses(self):
        namespace,receipts,_=self.bind('timeout-raw',timeout=True)
        with self.assertRaises(SystemExit) as error:namespace['run']('fixture',['mock-command'],decode_stdout=False)
        self.assertEqual(error.exception.code,124)
        row=self.evidence(namespace,receipts,124,OEM)
        self.assertEqual(json.loads((receipts/'stopped.json').read_bytes()),{'first_unexpected':row,'source_acceptance':False})

output=io.StringIO()
result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActualRunMockTests))
(OUT/'mock-tests.txt').write_text(output.getvalue(),encoding='utf-8',newline='\n')
compile_result={'passed':False}
try:
    pyc=OUT/'build-validator.pyc'
    py_compile.compile(str(SOURCE),cfile=str(pyc),doraise=True)
    compile_result={'passed':True,'pyc':str(pyc),'sha256':sha(pyc)}
except py_compile.PyCompileError as error:
    compile_result={'passed':False,'error':str(error)}
git=lock['tools']['git']
if sha(pathlib.Path(git['path']))!=git['sha256']:raise SystemExit('locked Git mismatch')
git_results={}
for name,args in [('diff-check',['diff','--check']),('status',['status','--short']),('diff',['diff','--','apps/desktop/build-validator.py']),('head',['rev-parse','HEAD'])]:
    argv=[git['path'],'-c','gc.auto=0','-c','maintenance.auto=false']+args
    process=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=30)
    (OUT/(name+'.stdout.txt')).write_bytes(process.stdout);(OUT/(name+'.stderr.txt')).write_bytes(process.stderr)
    git_results[name]={'argv':argv,'exit_code':process.returncode}
summary={'status':'SOURCE_FROZEN_MOCK_TESTS_PASSED' if result.wasSuccessful() and compile_result['passed'] and all(v['exit_code']==0 for v in git_results.values()) else 'AUTHOR_CHECK_FAILED',
   'base_head':scope['base_head'],'source_path':'apps/desktop/build-validator.py','source_sha256':sha(SOURCE),'source_bytes':SOURCE.stat().st_size,
   'mock_tests':{'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()},
   'ast_scope':{'default_decode_stdout':True,'keyword_only':True,'raw_stdout_call_names':['web-module-junction']},'py_compile':compile_result,'git':git_results,
   'scope':'Only build-validator.py changed; raw stdout/stderr and invocation rows are written before nonzero/timeout refusal; strict UTF8 default preserved.',
   'no_native_mklink_model_provider':True,'formal_increment':0,'independent_acceptance':'NOT_REQUESTED','committed':False,
   'first_build_failure':{'ref':scope['first_failure_ref'],'sha256':scope['first_failure_sha256'],'preserved':True},
   'failure_accounting':'Existing bundle failure origin/attempt count unchanged; this is mocked source validation, not a build retry.'}
write_json(OUT/'author-summary.json',summary)
shutil.copyfile(SOURCE,OUT/'build-validator.frozen.py')
shutil.copyfile(pathlib.Path(__file__),OUT/pathlib.Path(__file__).name)
write_json(OUT/'source-manifest.json',{'base_head':scope['base_head'],'file_count':1,'files':[{'path':'apps/desktop/build-validator.py','sha256':sha(SOURCE),'bytes':SOURCE.stat().st_size}],'frozen':True})
write_json(OUT/'diagnostics.json',{'construction_failures':[] if result.wasSuccessful() and compile_result['passed'] else [{'test_output':'mock-tests.txt','py_compile':compile_result}],
    'original_build_failure_preserved':scope['first_failure_ref'],'no_counter_reset':True,'all_subprocesses':'Only pinned Git read-only calls. subprocess.run inside the actual extracted function is a Mock; mklink/native were never executed.'})
evidence={str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
write_json(OUT/'evidence-manifest.json',{'source_sha256':sha(SOURCE),'evidence_sha256':evidence})
print(json.dumps({'status':summary['status'],'mock_tests':summary['mock_tests'],'source_sha256':summary['source_sha256'],'author_summary_sha256':sha(OUT/'author-summary.json'),'py_compile':compile_result['passed']},ensure_ascii=False),flush=True)
print(output.getvalue(),flush=True)
raise SystemExit(0 if summary['status']=='SOURCE_FROZEN_MOCK_TESTS_PASSED' else 1)
