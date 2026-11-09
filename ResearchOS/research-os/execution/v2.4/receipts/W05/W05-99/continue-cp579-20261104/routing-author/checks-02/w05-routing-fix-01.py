from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-routing-20261104')
p=root/'tests/runtime/check/w0501.go'
s=p.read_text(encoding='utf-8')
assert '\t"os/exec"\n' in s
p.write_text(s.replace('\t"os/exec"\n',''),encoding='utf-8',newline='\n')

p=root/'tests/runtime/check/routing_test.go'
s=p.read_text(encoding='utf-8')
s=s.replace('for _, row := range runtimeRouteRows() {', '''rows := []runtimeRouteRow{
        {"W05", "W05-01", "", runtimeServed, true},
        {"W05", "W05-02", "", runtimeServed, true},
        {"W05", "W05-G01", "", runtimeFixture, true},
        {"W12", "", "C11", runtimeFixture, true},
        {"W05", "W05-G02", "", runtimeV24Live, true},
        {"W05", "W05-H08", "", runtimeV24Live, true},
        {"W05", "W05-P01", "", runtimeV24Live, true},
        {"W05", "W05-U02", "", runtimeV24Live, true},
        {"W05", "", "A04", runtimeV24Live, true},
        {"W12", "W05-G01", "", "", false},
        {"W12", "W05-G02", "", "", false},
        {"W12", "", "A04", "", false},
        {"W05", "", "C11", "", false},
        {"W05", "W05-01", "A04", "", false},
        {"W05", "W05-G02", "A04", "", false},
        {"W12", "W05-G01", "C11", "", false},
        {"W05", "W99-DOES-NOT-EXIST", "", "", false},
        {"W12", "", "", "", false},
        {"W05", "", "", "", false},
        {"", "", "A04", "", false},
        {"", "W05-01", "", "", false},
        {"", "", "", "", false},
    }
    for _, row := range rows {''',1)
needle='\tif err := os.Remove(filepath.Join(lockDir, "locked.json")); err != nil {'
assert needle in s
s=s.replace(needle,'''    fixture, err := runtimePythonCommand(root, "ops/ci/runtime.py", "fixture")
    if err != nil || fixture.Path != tool || fixture.Args[3] != filepath.Join(root,"ops","ci","runtime.py") || fixture.Args[5] != "fixture" {t.Fatalf("incorrect fixture command: %#v err=%v",fixture,err)}
    if err := os.WriteFile(filepath.Join(lockDir,"locked.json"), []byte("{"),0600); err != nil {t.Fatal(err)}
    if _,err = lockedPython(root); err==nil {t.Fatal("malformed lock accepted")}
'''+needle)
p.write_text(s,encoding='utf-8',newline='\n')

p=root/'tests/runtime/runtime_v24_test.py'
s=p.read_text(encoding='utf-8').replace('import importlib.util\n','import importlib.util\nimport hashlib\n')
s=s.replace('        env = dict(os.environ, **self.env(case="A04"))\n', '''        lock = json.loads((ROOT/"execution/toolchains/locked.json").read_bytes())["tools"]["python"]
        python = Path(lock["path"])
        self.assertTrue(python.is_absolute())
        self.assertEqual(hashlib.sha256(python.read_bytes()).hexdigest(), lock["sha256"])
        env = dict(os.environ, **self.env(case="A04"))
''')
s=s.replace('[sys.executable, "-X", "utf8", str(ROOT/"ops/ci/runtime_v24.py")','[str(python), "-X", "utf8", str(ROOT/"ops/ci/runtime_v24.py")')
s=s.replace('import sys\n','')
p.write_text(s,encoding='utf-8',newline='\n')

p=Path(__file__).parent/'w05-routing-test-controller.py'
s=p.read_text(encoding='utf-8').replace("run=RECEIPT/'checks-01'","run=RECEIPT/'checks-02'")
s=s.replace("'note':'Development checks only, no formal acceptance; old native suites not called.'", "'attempt_index':2,'failure_origin':'w05-routing-author-go-unused-import-20261104','previous_attempt':'checks-01','note':'Directed retry after removing unused import; development checks only, no formal acceptance; old native suites not called.'")
s=s.replace("['w05-routing-author.py','w05-routing-refine.py','w05-routing-test-controller.py']", "['w05-routing-author.py','w05-routing-refine.py','w05-routing-fix-01.py','w05-routing-test-controller.py','w05-routing-test-controller-r2.py']")
(Path(__file__).parent/'w05-routing-test-controller-r2.py').write_text(s,encoding='utf-8',newline='\n')
print('removed unused import and strengthened independent routing/locked-interpreter tests; retry2 prepared')
