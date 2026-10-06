package domain
import ("bytes";"testing";"encoding/json")
func TestIndependentModelQuarantineSDKSemanticMerges(t *testing.T) {
 for _,kind:=range []string{"reasoning-alias","reasoning.text","reasoning.summary"} {
 t.Run(kind,func(t *testing.T){
 secret:="REVIEW_SYNTHETIC_ALPHA_OMEGA";q,_:=newModelSSEQuarantine(secret)
 var forwarded,rawAll []byte
 for i,text:=range []string{"REVIEW_SYNTHETIC_ALPHA_","OMEGA"}{
 delta:=map[string]any{}
 if kind=="reasoning-alias" {key:="reasoning";if i==1{key="reasoning_content"};delta[key]=text} else {
 field:="text";if kind=="reasoning.summary"{field="summary"}
 delta["reasoning_details"]=[]any{map[string]any{"type":kind,field:text}}
 }
 b,_:=json.Marshal(map[string]any{"choices":[]any{map[string]any{"index":0,"delta":delta}}})
 event:=append(append([]byte("data: "),b...),[]byte("\n\n")...);rawAll=append(rawAll,event...)
 r,e:=q.Feed(event);if e!=nil{t.Log("correctly rejected before downstream");return};forwarded=append(forwarded,r...)
 }
 end:=[]byte("data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"safe\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
 rawAll=append(rawAll,end...);r,e:=q.Feed(end);if e!=nil{return};forwarded=append(forwarded,r...)
 raw,tail,e:=q.Finish();if e!=nil{return};forwarded=append(forwarded,tail...)
 if !bytes.Equal(rawAll,raw)||!bytes.Equal(forwarded,raw){t.Fatal("probe byte bookkeeping")}
 t.Fatalf("SYNTHETIC_SECRET_NOT_QUARANTINED lane=%s original_bytes=%d hash=%s",kind,len(raw),Digest(raw))
 })
 }
}

