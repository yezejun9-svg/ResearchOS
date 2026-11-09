import pathlib,json,hashlib,difflib
M=pathlib.Path('D:/作品集/ResearchOS/research-os');H=pathlib.Path(__file__).resolve().parent;OLD=H.parent/'cc88ef8c-d066-4b10-b6c5-1d9bba89baad';A=M/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-public-cohort-r292/public12_scope_amendment.json'
def ref(p):p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,o):
 with (H/n).open('x',encoding='utf-8') as f:json.dump(o,f,indent=2,ensure_ascii=False);f.write('\n')
assert ref(A)['sha256']=='6e018065f6021f450d74dfde533cf1d5cbb1427a228d154078bb8193599fbe55';a=json.loads(A.read_text(encoding='utf-8'));oldpath=OLD/'independent_provider_public_boundary_windows_test.go';assert ref(oldpath)['sha256']=='c300fb61dd2855bea5ba2f9bce329dcabc53662d4bb30169a59846d187105676';old=oldpath.read_text(encoding='utf-8');s=old
s=s.replace('root     string','root     string\n expectedDestination string') if 'root     string' in s else s
# Operate on actual gofmt source with exact anchors, fail before execution on drift.
a1='func (s *independentWorkspace) SnapshotWorkspace(_ context.Context, b WorkspaceBinding, principal string, _ BackupWorkspaceLimits)';assert a1 in s;s=s.replace(a1,a1.replace('principal string','destination string'))
a1='principal != "fixture-author"';assert a1 in s;s=s.replace(a1,'filepath.Clean(destination) != filepath.Clean(s.expectedDestination) || b.PrincipalID != s.expected.PrincipalID')
a1='"principal": principal';assert a1 in s;s=s.replace(a1,'"principal": b.PrincipalID, "destination": destination')
if 'expectedDestination string' not in s:
 at=s.index('type independentWorkspace struct {')+len('type independentWorkspace struct {');s=s[:at]+'\n expectedDestination string'+s[at:]
a1='ws = &independentWorkspace{expected: b}';assert a1 in s;s=s.replace(a1,'ws = &independentWorkspace{expected: b, expectedDestination: filepath.Join(dir, "archive")}')
a1='rews = &independentWorkspace{expected: bs[0], restored: true, root: BackupWorkspaceDestination(destination, "tool-workspace")}';assert a1 in s;s=s.replace(a1,'rews = &independentWorkspace{expected: bs[0], restored: true, root: BackupWorkspaceDestination(destination, "tool-workspace"), expectedDestination: again}')
a1='if e = json.Unmarshal(files["workspace-index.json"], &idx); e != nil {\n\t\tt.Fatal("workspace index", e)\n\t}'
assert a1 in s
s=s.replace(a1,'if wantWorkspace {\n if e = json.Unmarshal(files["workspace-index.json"], &idx); e != nil || idx.Format != "RESEARCHOS_WORKSPACE_SNAPSHOT_V1" { t.Fatal("workspace index", e) }\n } else {\n for name := range files { if strings.HasPrefix(name,"workspace-") { t.Fatal("unexpected workspace decoded resource",name) } }\n for _, entry := range m.Files { if strings.HasPrefix(entry.Name,"workspace-") { t.Fatal("unexpected workspace manifest resource",entry.Name) } }\n }')
a1='hasWorkspace := spec["id"] == "0"';assert a1 in s;s=s.replace(a1,a1+'\n if !hasWorkspace { var allBindings int; if e=db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind=\'WorkspaceBinding\'`).Scan(&allBindings); e!=nil || allBindings!=0 { t.Fatal("original all WorkspaceBinding rows must be zero",allBindings,e) }; result["original_all_workspace_binding_count"]=allBindings }')
(H/oldpath.name).write_text(s,encoding='utf-8',newline='\n');(H/'overlay-two-corrections.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(oldpath),tofile=str(H/oldpath.name))),encoding='utf-8')
(H/'export.json').write_bytes((OLD/'export.json').read_bytes());(H/'synthetic_workspace_evidence.txt').write_bytes((OLD/'synthetic_workspace_evidence.txt').read_bytes());(H/'inputs').mkdir();inputs=json.loads((OLD/'original7.before.json').read_text(encoding='utf-8'))
for e in inputs:
 src=pathlib.Path(e['original']['path']);assert ref(src)==e['original'];dst=H/'inputs'/(e['id']+'.sqlite');dst.write_bytes(src.read_bytes());e['copy']=ref(dst)
write('original7.before.json',inputs);write('amendment-ref.json',ref(A));driver=(OLD/'driver.py').read_text(encoding='utf-8').replace('cache-r291','cache-r292');start=driver.index('  for i,(key,mode,cause)');end=driver.index("  for mode in ['positive','missing-dispatch-transport']:",start);driver=driver[:start]+driver[end:];driver=driver.replace('assert len(plan)==76','assert len(plan)==12');(H/'driver.py').write_text(driver,encoding='utf-8',newline='\n');write('cohort.json',{'scope':ref(A),'original_internal64_review':ref(OLD/'review.json'),'original_internal64_binary':ref(OLD/'independent.domain.test.exe'),'no_executable_equivalence_claim':True,'new_public_control_limit':12,'prior_actual_controls':65,'cumulative_max_actual':77,'source2_no_change':True,'original_overlay':ref(oldpath)})
print(json.dumps({'new':str(H),'overlay':ref(H/oldpath.name)},ensure_ascii=False))
