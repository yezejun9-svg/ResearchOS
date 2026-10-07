package domain
import("os";"testing")
func TestIndependentSignedZeroToolIdentity(t *testing.T){
 raw,e:=os.ReadFile(os.Getenv("RESEARCHOS_REVIEW_SSE"));if e!=nil{t.Fatal(e)}
 q,e:=newModelSSEQuarantine("permission-loopback-fixture");if e!=nil{t.Fatal(e)}
 out,e:=q.Feed(raw);if e!=nil{return};original,terminal,e:=q.Finish();if e!=nil{return}
 t.Fatalf("protected semantic tool string admitted: feed=%d terminal=%d original=%d",len(out),len(terminal),len(original))
}
