from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-product-coding-profile-core-20261012'
p=OUT/'reviewer_coding_windows_test.go';s=p.read_text(encoding='utf-8')
s=s.replace('digest=Hash(r)','r.RequestID=ID();id=r.RequestID;digest=Hash(r)')
s=s.replace("`UPDATE idempotency SET request_hash=?,body=? WHERE operation='host:coding-confirmation' AND key=?`,digest,Bytes(r),id", "`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:coding-confirmation',?,?,200,?,'{}',?)`,f.owner,f.project,id,digest,Bytes(r),Now()")
s=s.replace('f,c,runID,key:=desktopExitFixture(t);ctx:=context.Background()', 'f,c,runID,key:=reviewerDesktopExitFixture(t,mode);ctx:=context.Background()')
start=s.index('    case "streams_not_drained","cleanup_incomplete":')
end=s.index('    default:',start)
s=s[:start]+'''    case "streams_not_drained","cleanup_incomplete","missing_started_stage","missing_frozen_profile":
     return nil // Injected before the fixture's immutable evidence is sealed.
'''+s[end:]
s=s.replace('_,profile,err:=c.sessionModel(tx,f.project,Str(result,"model_config_ref"));if err!=nil{t.Fatal(err)}', '''runtime,err:=load(tx,f.project,"RuntimeRegistration",Str(result,"runtime_id"));if err!=nil{t.Fatal(err)}
 _,artifact,err:=c.service.currentRuntimeBinding(tx,f.project,runtime);if err!=nil{t.Fatal(err)}
 profile,err:=runtimeProfileBody(tx,f.project,artifact);if err!=nil{t.Fatal(err)}''')
raw=(WT/'internal/domain/runtime_drain_windows_test.go').read_text(encoding='utf-8')
f=raw[raw.index('func desktopExitFixture('):raw.index('func TestDesktopExitCompletedLocalUnknownPreservesReleaseGate')]
f=f.replace('func desktopExitFixture(t *testing.T)', 'func reviewerDesktopExitFixture(t *testing.T, mode string)')
f=f.replace('effect, e = c.service.beginEffectTx(tx, c.schedulerCredential(f.project), f.project, runID, key)', 'if mode != "missing_started_stage" { effect, e = c.service.beginEffectTx(tx, c.schedulerCredential(f.project), f.project, runID, key) }')
needle='\t\tif _, e = tx.Exec(`UPDATE runtime_dispatches SET state='
idx=f.index(needle)
f=f[:idx]+'''        if mode == "streams_not_drained" { observation["streams_drained"] = false }
        if mode == "cleanup_incomplete" { observation["cleanup_complete"] = false }
        if mode == "missing_frozen_profile" {
            ref := admission["profile_ref"].(map[string]any)
            ref["id"] = "reviewer-absent-frozen-artifact"
            admission["profile_hash"] = Hash(ref)
            observation["spec"].(map[string]any)["profile_hash"] = Hash(ref)
            dispatch["manifest_hash"] = Hash(manifest)
            observation["manifest_hash"] = dispatch["manifest_hash"]
            if _, e = tx.Exec(`UPDATE runtime_dispatches SET manifest=?,manifest_hash=? WHERE project=? AND run=?`, Bytes(manifest),Hash(manifest),f.project,runID); e != nil { return e }
        }
'''+f[idx:]
p.write_text(s+'\n'+f,encoding='utf-8')
print('Preserved attempt1; revised isolated fixtures seal malformed witnesses initially, not by rewriting immutable rows.')
