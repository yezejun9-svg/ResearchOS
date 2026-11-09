//go:build windows
package runtime
import("encoding/json";"os";"path/filepath";"testing"; sandbox "researchos.local/research-os/ops/experiment_sandbox")
func TestVerifierBridgeUntrustedFrames(t *testing.T) {
 cases:=map[string]string{
 "effect_before_context":`{"sequence":1,"type":"effect.request","key":"k","route":"fixture","capability":"fixture.echo","payload":{}}`,
 "checkpoint_before_context":`{"sequence":1,"type":"checkpoint","path":"checkpoint.json"}`,
 "completed_before_context":`{"sequence":1,"type":"turn.completed"}`,
 "trailing_second_json":`{"sequence":1,"type":"turn.completed"} {"sequence":2,"type":"effect.request"}`,
 "duplicate_type":`{"sequence":1,"type":"effect.request","type":"turn.completed"}`,
 }
 rows:=[]map[string]any{}
 for name,line:=range cases {t.Run(name,func(t *testing.T){
  directory:=t.TempDir();stdout,e:=os.Create(filepath.Join(directory,"stdout.raw"));if e!=nil{t.Fatal(e)};defer stdout.Close();stderr,e:=os.Create(filepath.Join(directory,"stderr.raw"));if e!=nil{t.Fatal(e)};defer stderr.Close()
  w:=&Bridge{directory:directory,stdout:stdout,stderr:stderr,frames:make(chan BridgeFrame,32),streamOffsets:map[string]int64{},journal:BridgeJournal{State:"STARTED",InputHash:"expected"}}
  err:=w.consume(sandbox.StreamChunk{Stream:"stdout",Offset:0,Data:[]byte(line+"\n")});errText:="";if err!=nil{errText=err.Error()}
  row:=map[string]any{"case":name,"raw":line,"error":errText,"context_ready":w.journal.ContextReady,"frames":w.journal.Frames,"protocol_complete":w.journal.ProtocolComplete,"queued":len(w.frames)};rows=append(rows,row);t.Logf("VERIFIER_BRIDGE %s",mustVerifierJSON(row))
 })}
 raw,e:=json.MarshalIndent(rows,"","  ");if e!=nil{t.Fatal(e)};if e=os.WriteFile(filepath.Join(os.Getenv("INDEPENDENT_S2_EVIDENCE"),"bridge-frames.json"),raw,0600);e!=nil{t.Fatal(e)}
}
func mustVerifierJSON(v any)string{b,_:=json.Marshal(v);return string(b)}
