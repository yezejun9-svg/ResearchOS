package domain
import ("bytes";"testing")
func TestIndependentModelQuarantineReasoningAliasSplit(t *testing.T) {
 secret := "REVIEW_SYNTHETIC_ALPHA_OMEGA"
 q,err:=newModelSSEQuarantine(secret);if err!=nil {t.Fatal(err)}
 parts:=[][]byte{
 []byte("data: {\"choices\":[{\"index\":0,\"delta\":{\"reasoning\":\"REVIEW_SYNTHETIC_ALPHA_\"}}]}\n\n"),
 []byte("data: {\"choices\":[{\"index\":0,\"delta\":{\"reasoning_content\":\"OMEGA\"}}]}\n\n"),
 []byte("data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"safe\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n"),
 }
 var forwarded []byte
 for _,p:=range parts{released,e:=q.Feed(p);if e!=nil {t.Log("correctly rejected before SDK");return};forwarded=append(forwarded,released...)}
 raw,tail,e:=q.Finish();if e!=nil {t.Log("correctly rejected before SDK terminal");return}
 forwarded=append(forwarded,tail...)
 if !bytes.Equal(forwarded,raw){t.Fatal("probe forwarded byte bookkeeping")}
 t.Fatalf("SYNTHETIC_SECRET_NOT_QUARANTINED: exact original SSE %d bytes delivered, reasoning + reasoning_content concatenate to protected synthetic secret",len(forwarded))
}

