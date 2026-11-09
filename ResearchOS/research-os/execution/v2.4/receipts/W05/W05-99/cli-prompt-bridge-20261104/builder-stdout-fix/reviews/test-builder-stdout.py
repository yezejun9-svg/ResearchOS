"""Independent AST-extracted run helper checks. subprocess.run is always mocked."""
import ast,datetime,hashlib,json,pathlib,subprocess,tempfile,types,unittest
SOURCE=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-builder-stdout-20261104/apps/desktop/build-validator.py')
RAW=SOURCE.read_bytes(); TREE=ast.parse(RAW); assert hashlib.sha256(RAW).hexdigest()=='b15147a1671d2d619bb8d1deeedf41953609ceddd838e15abfa9e20afb4640fc'
RUN=next(n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name=='run')
PUT=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='put')
ENV={k:'fixture' for k in ['GOTOOLCHAIN','GOENV','GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','GOPROXY','GOSUMDB']}
class Tests(unittest.TestCase):
    def helper(self,completed=None,error=None):
        tmp=tempfile.TemporaryDirectory(prefix='researchos-builder-stdout-review-'); self.addCleanup(tmp.cleanup)
        root=pathlib.Path(tmp.name); invocations=[]; calls=[]
        def fake(*args,**kw):
            calls.append((args,kw))
            if error is not None: raise error
            return completed
        space={'ROOT':root,'receipts':root,'env':ENV,'invocations':invocations,'datetime':datetime,'json':json,'subprocess':types.SimpleNamespace(run=fake,TimeoutExpired=subprocess.TimeoutExpired)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[PUT,RUN],type_ignores=[])),str(SOURCE),'exec'),space)
        return space['run'],root,invocations,calls
    def test_default_strict_utf8_and_original_receipts(self):
        raw='{"v":"中文"}\n'.encode(); err=b'raw-stderr'
        run,root,rows,calls=self.helper(types.SimpleNamespace(returncode=0,stdout=raw,stderr=err))
        self.assertEqual(run('go-json',['inert']),raw.decode('utf-8'))
        self.assertEqual((root/'go-json.stdout').read_bytes(),raw); self.assertEqual((root/'go-json.stderr').read_bytes(),err)
        self.assertEqual(rows[0]['exit'],0); self.assertEqual(len(calls),1)
    def test_raw_oem_success_is_not_decoded(self):
        raw=b'\xce\xaa D:\\'+bytes([0xd7,0xf7,0xc6,0xb7])+b'\r\n'
        run,root,rows,calls=self.helper(types.SimpleNamespace(returncode=0,stdout=raw,stderr=b''))
        self.assertEqual(run('mklink-fixture',['inert'],decode_stdout=False),raw)
        self.assertEqual((root/'mklink-fixture.stdout').read_bytes(),raw); self.assertFalse((root/'stopped.json').exists())
        self.assertEqual(rows[0]['exit'],0)
    def test_default_oem_still_fails_after_raw_persisted(self):
        raw=bytes([0xd7]); run,root,rows,calls=self.helper(types.SimpleNamespace(returncode=0,stdout=raw,stderr=b''))
        with self.assertRaises(UnicodeDecodeError): run('strict-json-fixture',['inert'])
        self.assertEqual((root/'strict-json-fixture.stdout').read_bytes(),raw)
        self.assertTrue((root/'strict-json-fixture.invocation.json').is_file()); self.assertEqual(rows[0]['exit'],0)
    def test_raw_nonzero_remains_failure(self):
        raw=bytes([0xd7]); run,root,rows,calls=self.helper(types.SimpleNamespace(returncode=7,stdout=raw,stderr=b'failed'))
        with self.assertRaises(SystemExit) as caught: run('nonzero',['inert'],decode_stdout=False)
        self.assertEqual(caught.exception.code,7); self.assertEqual((root/'nonzero.stdout').read_bytes(),raw)
        self.assertEqual(json.loads((root/'stopped.json').read_bytes())['first_unexpected']['exit'],7)
    def test_raw_timeout_remains_failure(self):
        raw=bytes([0xd7]); run,root,rows,calls=self.helper(error=subprocess.TimeoutExpired(['inert'],1,output=raw,stderr=b'timedout'))
        with self.assertRaises(SystemExit) as caught: run('timeout',['inert'],decode_stdout=False)
        self.assertEqual(caught.exception.code,124); self.assertEqual((root/'timeout.stdout').read_bytes(),raw)
        self.assertEqual(json.loads((root/'stopped.json').read_bytes())['first_unexpected']['exit'],124)
    def test_only_mklink_call_can_disable_strict_decode(self):
        self.assertEqual([x.arg for x in RUN.args.kwonlyargs],['decode_stdout']); self.assertIsInstance(RUN.args.kw_defaults[0],ast.Constant)
        self.assertIs(RUN.args.kw_defaults[0].value,True)
        overrides=[]
        for n in ast.walk(TREE):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run':
                for kw in n.keywords:
                    if kw.arg=='decode_stdout':
                        self.assertIsInstance(kw.value,ast.Constant); self.assertIs(kw.value.value,False)
                        overrides.append(ast.literal_eval(n.args[0]))
        self.assertEqual(overrides,['web-module-junction']); compile(RAW,str(SOURCE),'exec')
if __name__=='__main__': unittest.main(verbosity=2)