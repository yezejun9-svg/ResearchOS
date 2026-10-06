package runtime
import("testing";"fmt")
func TestIndependentReconnectOrdering(t *testing.T){
 retry:="{\"type\":\"error\",\"message\":\"Reconnecting... 2/5 (stream disconnected before completion: connection reset)\"}\n"
 complete:="{\"type\":\"turn.completed\"}\n"
 raw:=retry+complete+retry
 p:=ParseStreams([]byte(raw),nil,0)
 fmt.Printf("INDEPENDENT_RECONNECT actual_settled=%v failure=%q expected_settled=false expected_failure=missing_settled\n",p.Settled,p.Failure)
 if p.Settled || p.Failure!="missing_settled" {t.Fatal("an identical later reconnect diagnostic was deduplicated across turn.completed; no later completion exists")}
}
