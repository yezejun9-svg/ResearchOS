package runtime
import("testing";"os";"encoding/json";"fmt")
func TestIndependentActualC01Replay(t *testing.T){
 stdout,e:=os.ReadFile(`D:\作品集\ResearchOS\research-os\execution\receipts\W06\continuation-live\65ebbc11-20bd-4136-aa39-faa2fa3c4849\C01-000.stdout`);if e!=nil{t.Fatal(e)}
 stderr,e:=os.ReadFile(`D:\作品集\ResearchOS\research-os\execution\receipts\W06\continuation-live\65ebbc11-20bd-4136-aa39-faa2fa3c4849\C01-000.stderr`);if e!=nil{t.Fatal(e)}
 p:=ParseStreams(stdout,stderr,0);var r map[string]any;if e=json.Unmarshal(p.Result,&r);e!=nil{t.Fatal(e)}
 fmt.Printf("ACTUAL_C01_REPLAY settled=%v failure=%q total=%v operation=%v tool_count=%d\n",p.Settled,p.Failure,r["total"],r["operation"],p.ToolsCompleted)
 if !p.Settled||p.Failure!=""||r["total"]!=float64(425)||r["operation"]!="MULTIPLY"||p.ToolsCompleted!=0{t.Fatal(p,r)}
}
