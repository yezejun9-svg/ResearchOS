package domain
import "testing"
func TestRepairProbeNestedToolJSON(t *testing.T){
 q,_:=newModelSSEQuarantine("permission-loopback-fixture")
 parts:=[]string{`{"x":"perm\u0069`, `ssion-loopback-fixture"}`}
 for _,part:=range parts { raw:=streamTestDelta(Object{"tool_calls":[]any{Object{"index":0,"function":Object{"arguments":part}}}});if _,err:=q.Feed(raw);err!=nil{return} }
 t.Fatal("second-level decoded synthetic credential reached SDK input")
}
