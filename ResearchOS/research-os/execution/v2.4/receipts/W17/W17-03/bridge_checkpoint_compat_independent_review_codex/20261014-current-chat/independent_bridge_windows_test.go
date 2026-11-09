//go:build windows

package runtime

import (
 "bytes"
 "compress/gzip"
 "context"
 "encoding/base64"
 "encoding/json"
 "os"
 "path/filepath"
 "testing"
 "time"
 sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

func TestIndependentMuUnnegotiatedNormalNative(t *testing.T) {
 if *pauseWorkerBundle=="" || *pauseWorkerNode=="" {t.Fatal("pinned assets required")}
 bundle,e:=os.ReadFile(*pauseWorkerBundle);if e!=nil {t.Fatal(e)}
 node,e:=os.ReadFile(*pauseWorkerNode);if e!=nil {t.Fatal(e)}
 config:=map[string]any{"ref":"fixture","api":"openai-completions","provider":"openai","model":"fixture","endpoint":"https://fixture.invalid","route":"broker","max_output_tokens":128,"max_calls":1,"tools":[]any{}}
 workerConfig,_:=json.Marshal(config)
 profile:=map[string]any{"backend":"mu-sdk-broker-v1","model":"fixture","sandbox":"appcontainer-zero-capabilities-v1","adapter_revision":BridgeRevision,"build_hash":Hash(node),"bundle_hash":Hash(bundle),"model_config":config,"argv":[]string{"--preserve-symlinks-main","--preserve-symlinks","{bundle}","{manifest}"},"timeout_seconds":60,"outputs":[]string{"result.json"}}
 manifest,_:=json.Marshal(map[string]any{"task_id":"task","run_id":"unnegotiated","epoch":1,"dispatch_key":"ordinary-mu","admission":map[string]any{"profile":profile}})
 hash,_:=canonicalHash(manifest)
 request,_:=json.Marshal(map[string]any{"task_id":"task","run_id":"unnegotiated","epoch":1,"input_refs":[]any{},"context":map[string]any{},"task_title":"ordinary Mu turn","task_description":"one ordinary prompt","queue_control":false})
 ctx,cancel:=context.WithTimeout(context.Background(),65*time.Second);defer cancel()
 w,e:=StartBridge(ctx,filepath.Join(t.TempDir(),"ordinary"),BridgeRequest{WorkerID:"ordinary-mu",Manifest:manifest,ManifestHash:hash,Executable:*pauseWorkerNode,Inputs:map[string][]byte{"request.json":request,"worker.json":workerConfig,"mu-worker.mjs":bundle},BeforeResume:func(i sandbox.Identity)error{return nil}})
 if e!=nil {t.Fatal(e)}
 t.Cleanup(func(){w.Cancel("test cleanup");<-w.Done()})
 models:=0;completed:=false
 for frame:=range w.Frames() {
  var reply any
  switch frame.Type {
  case "context.ready":
  case "effect.request":
   models++
   sse:=[]byte("data: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"ordinary reply\"},\"finish_reason\":null}]}\n\ndata: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
   var buf bytes.Buffer;z:=gzip.NewWriter(&buf);z.Write(sse);z.Close()
   reply=map[string]any{"sequence":frame.Sequence,"key":frame.Key,"state":"CONFIRMED","payload":map[string]any{"status":200,"content_type":"text/event-stream","body_encoding":"gzip+base64","body_gzip_base64":base64.StdEncoding.EncodeToString(buf.Bytes()),"body_sha256":Hash(sse)}}
  case "turn.completed":completed=true
  default:t.Fatalf("unexpected ordinary frame %s",frame.Type)
  }
  if e=w.Acknowledge(ctx,frame.Sequence,reply);e!=nil {t.Fatal(e)}
 }
 <-w.Done();j:=w.Read()
 if models!=1 || !completed || j.State!="EXITED" || j.PauseProtocol!="" || j.CheckpointSequence!=0 || j.Paused || j.Checkpoint!=nil || !j.Receipt.Stopped || !j.Receipt.StreamsDrained || !j.Receipt.CleanupComplete || !j.Receipt.OutputCopied || j.Receipt.ExitCode!=0 || j.Frames!=j.Acknowledged {t.Fatalf("ordinary result models=%d completed=%v journal=%+v",models,completed,j)}
 if _,e=ReadBridgeTerminal(w.Directory(),hash);e!=nil {t.Fatal(e)}
 raw,e:=os.ReadFile(filepath.Join(w.Directory(),"output","result.json"));if e!=nil {t.Fatal(e)}
 result,e:=bridgeMap(raw);if e!=nil || bridgeNumber(result,"model_calls")!=1 {t.Fatal("ordinary result",e)}
 reviewCaptureBridge(t,"ordinary-unnegotiated-mu",w.Directory())
 t.Logf("INDEPENDENT_NATIVE ordinary unnegotiated Mu completed, pid=%d model_calls=1 checkpoint_disabled=true",j.Identity.PID)
}

func TestIndependentPauseProtocolExplicitNullAndModeErasure(t *testing.T) {
 manifest,_:=checkpointCompatInputs("fixture",nil);m,_:=bridgeMap(manifest)
 for _,raw:=range []string{`{"task_id":"task","run_id":"run","epoch":1,"pause_protocol":null}`,`{"task_id":"task","run_id":"run","epoch":1,"pause_protocol":false}`,`{"task_id":"task","run_id":"run","epoch":1,"pause_protocol":"RESEARCHOS_PAUSE_V1","pause_protocol":null}`} {
  if _,e:=checkpointModeForRequest(m,[]byte(raw));e==nil {t.Fatal("invalid explicit protocol accepted",raw)}
 }
 for _,backend:=range []string{"fixture","mu-sdk-broker-v1"} {
  d,j:=checkpointCompatTerminal(t,backend,PauseProtocol)
  j.PauseProtocol="";j.Checkpoint=nil;j.CheckpointSeal=nil;j.PauseRequested=false;j.PauseID=""
  if e:=save(filepath.Join(d,"bridge.json"),j);e!=nil {t.Fatal(e)}
  if _,e:=ReadBridgeTerminal(d,j.ManifestHash);e==nil {t.Fatal("journal erasure downgraded",backend)}
 }
}
