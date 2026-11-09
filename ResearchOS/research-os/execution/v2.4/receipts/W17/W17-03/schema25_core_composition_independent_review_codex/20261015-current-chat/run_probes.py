import pathlib,json,subprocess,os,hashlib,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os');E=pathlib.Path(__file__).parent
W=R/'.local/worktrees/schema25-core-composition-20261015';A=R/'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=W/'internal/host/runtime_verifier_replacement_windows_test.go'
extra=r'''
func TestIndependentCompositionSchema25VerifierRefusesReadonly(t *testing.T) {
 f:=newReplacementFixture(t)
 f.exec(t,"INSERT INTO schema_migrations VALUES(25)")
 before,e:=os.ReadFile(filepath.Join(f.Root,"researchos.sqlite"));if e!=nil {t.Fatal(e)}
 if e=replacementTestGate(f.Root);e!=nil {t.Fatal("clean startup history unexpectedly rejected",e)}
 _,e=RuntimeVerifierReplacement(context.Background(),f.Input)
 if e==nil || !strings.Contains(e.Error(),"supported schema 24 required") {t.Fatalf("schema25 replacement did not fail closed: %v",e)}
 after,e:=os.ReadFile(filepath.Join(f.Root,"researchos.sqlite"));if e!=nil || !bytes.Equal(before,after) {t.Fatal("readonly refusal changed fixture DB",e)}
 if _,e=os.Stat(f.Plan);!os.IsNotExist(e) {t.Fatal("schema25 refusal created plan",e)}
}
func TestIndependentCompositionSchema25PreservesHistoryGate(t *testing.T) {
 f:=newReplacementFixture(t);in:=f.preflight(t)
 result,e:=RuntimeVerifierReplacement(context.Background(),in)
 if e!=nil || result.State!="COMMITTED" {t.Fatal("schema24 fixture replacement",result,e)}
 f.exec(t,"INSERT INTO schema_migrations VALUES(25)")
 before,e:=os.ReadFile(filepath.Join(f.Root,"researchos.sqlite"));if e!=nil {t.Fatal(e)}
 if e=replacementTestGate(f.Root);e!=nil {t.Fatal("valid terminal history rejected on25",e)}
 replacementTestWrite(t,filepath.Join(f.Root,"host","runtime-verifier-installation.json"),f.Record)
 if e=replacementTestGate(f.Root);e==nil || !strings.Contains(e.Error(),"latest replacement registration drift") {t.Fatalf("schema25 bypassed history gate: %v",e)}
 after,e:=os.ReadFile(filepath.Join(f.Root,"researchos.sqlite"));if e!=nil || !bytes.Equal(before,after) {t.Fatal("startup gate changed fixture DB",e)}
}
'''
overlayfile=E/'host-boundary-overlay.go';overlayfile.write_bytes(source.read_bytes()+extra.encode())
overlay=E/'overlay.json';write('overlay.json',dict(Replace={str(source):str(overlayfile)}))
ref=read(A/'T2-verifier-host.json');env=os.environ.copy();env.update(ref['environment_allowlist'])
tmp=E/'scratch';tmp.mkdir(exist_ok=True)
for k in ['TEMP','TMP','GOTMPDIR']:env[k]=str(tmp)
guardpaths=read(A/'FINAL.json')['exact_changed_paths']+read(R/'execution/v2.4/receipts/W17/W17-03/composition_map_independent_codex/20261015-current-chat/COMPOSITION-MAP.json')['bounded_builder_scope']['protected_main_paths']
def guard():return {p:pin(W/p)['sha256'] for p in guardpaths}
commands=[('fresh-host-boundary',[ref['argv'][0],'test','-mod=readonly','-overlay',str(overlay),'-json','./internal/host','-run','^TestIndependentCompositionSchema25','-count=1','-timeout=3m']),('missing-core-budget-release',[ref['argv'][0],'test','-mod=readonly','-json','./internal/domain','-run','^Test(W12BudgetLeaseTakeover|CompletedRuntimeLocalLaunchRelease)$','-count=1','-timeout=3m'])]
for label,argv in commands:
 before=guard();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (E/(label+'.stdout.jsonl')).open('wb') as out,(E/(label+'.stderr.raw')).open('wb') as err:
  r=subprocess.run(argv,cwd=W,env=env,stdout=out,stderr=err,timeout=240)
 after=guard();write(label+'.json',dict(argv=argv,cwd=str(W),environment_allowlist={k:env[k] for k in ref['environment_allowlist']},started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_exit=r.returncode,stdout=pin(E/(label+'.stdout.jsonl')),stderr=pin(E/(label+'.stderr.raw')),guard_before=before,guard_after=after,source_unchanged=before==after,overlay=pin(overlay),overlay_source=pin(overlayfile),formal_increment=0))
 print(label,r.returncode,flush=True)
