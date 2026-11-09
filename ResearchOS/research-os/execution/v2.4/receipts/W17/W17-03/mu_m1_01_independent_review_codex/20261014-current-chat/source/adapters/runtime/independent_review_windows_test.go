//go:build windows
package runtime
import("testing";"os";"path/filepath";"encoding/json";"bytes";"golang.org/x/sys/windows")
func TestIndependentCheckpointReaderBoundAndSharing(t *testing.T){
 root:=t.TempDir();path:=filepath.Join(root,"snapshot.json")
 for _,n:=range []int{0,MaxPauseCheckpointBytes,MaxPauseCheckpointBytes+1}{
  if e:=os.WriteFile(path,bytes.Repeat([]byte("x"),n),0600);e!=nil{t.Fatal(e)}
  b,e:=readPauseFile(path);if n==MaxPauseCheckpointBytes {if e!=nil||len(b)!=n{t.Fatal("exact max rejected",e)}} else if e==nil {t.Fatal("invalid bound accepted",n)}
 }
 if _,e:=readPauseFile(root);e==nil{t.Fatal("directory accepted")}
 if e:=os.WriteFile(path,[]byte("snapshot"),0600);e!=nil{t.Fatal(e)}
 name,_:=windows.UTF16PtrFromString(path)
 h,e:=windows.CreateFile(name,windows.GENERIC_WRITE,windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE,nil,windows.OPEN_EXISTING,0,0);if e!=nil{t.Fatal(e)}
 if _,e:=readPauseFile(path);e==nil{windows.CloseHandle(h);t.Fatal("concurrent writable handle accepted")};windows.CloseHandle(h)
}
func TestIndependentCheckpointSealCorrelation(t *testing.T){
 root:=t.TempDir();binding:=json.RawMessage(`{"project_id":"p","run_id":"r","runtime_epoch":1}`)
 fact:=[]byte(`{"project_id":"p","run_id":"r","epoch":1,"manifest_hash":"mh","dispatch_key":"d","sequence":6,"content_hash":"hash"}`)
 path:=filepath.Join(root,"checkpoint-6.json");if e:=os.WriteFile(path,fact,0600);e!=nil{t.Fatal(e)}
 w:=&Bridge{directory:root,journal:BridgeJournal{ManifestHash:"mh",DispatchKey:"d",CheckpointSequence:6,Checkpoint:&PauseCheckpoint{PauseID:"pause",ContentHash:"hash",Binding:binding}}}
 valid:=CheckpointSeal{Type:"checkpoint.sealed",Version:PauseProtocol,PauseID:"pause",Binding:binding,Sequence:6,ContentHash:"hash",CheckpointArtifactID:"a",CheckpointUseReceiptHash:Hash([]byte("use")),CheckpointUsePrincipal:"executor",JournalCheckpointHash:Hash(fact)}
 if e:=w.validateCheckpointSeal(valid);e!=nil{t.Fatal(e)}
 cases:=map[string]func(*CheckpointSeal){"foreign_binding":func(s *CheckpointSeal){s.Binding=json.RawMessage(`{"project_id":"q","run_id":"r","runtime_epoch":1}`)},"old_sequence":func(s *CheckpointSeal){s.Sequence=5},"wrong_hash":func(s *CheckpointSeal){s.ContentHash="changed"},"missing_artifact":func(s *CheckpointSeal){s.CheckpointArtifactID=""},"missing_principal":func(s *CheckpointSeal){s.CheckpointUsePrincipal=""},"false_receipt":func(s *CheckpointSeal){s.CheckpointUseReceiptHash="true"},"wrong_pause":func(s *CheckpointSeal){s.PauseID="other"}}
 for name,mutate:=range cases{t.Run(name,func(t *testing.T){s:=valid;mutate(&s);if w.validateCheckpointSeal(s)==nil{t.Fatal("bad seal accepted")}})}
 changed:=bytes.Replace(fact,[]byte(`"run_id":"r"`),[]byte(`"run_id":"foreign"`),1);if e:=os.WriteFile(path,changed,0600);e!=nil{t.Fatal(e)}
 if w.validateCheckpointSeal(valid)==nil{t.Fatal("changed journal bytes accepted")}
 valid.JournalCheckpointHash=Hash(changed);if w.validateCheckpointSeal(valid)==nil{t.Fatal("rehash hid foreign journal identity")}
}
