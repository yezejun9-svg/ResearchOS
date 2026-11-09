//go:build windows

package domain

import (
 "encoding/json"
 "fmt"
 "math"
 "strconv"
 "testing"

 "researchos.local/research-os/internal/canonical"
 sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

func TestIndependentSandboxIdentityNestedJSON(t *testing.T) {
 check:=func(id string,ok bool,actual any){t.Helper();status:="PASS";if !ok{status="FAIL"};raw,_:=json.Marshal(Object{"id":id,"status":status,"actual":actual});fmt.Println("S2_IDENTITY_ASSERT "+string(raw));if !ok{t.Errorf("%s: %v",id,actual)}}
 for _,created:=range []int64{0,9007199254740993,1790787239271034300,math.MaxInt64}{
  wanted:=strconv.FormatInt(created,10)
  value:=Object{"execution":Object{"host_receipt":sandbox.Receipt{PID:123,Created:created},"suspended_identity":sandbox.Identity{PID:123,Created:created}}}
  raw,e:=json.Marshal(value);if e!=nil{t.Fatal(e)}
  decoded,e:=Decode(raw);check(wanted+"-domain-decode",e==nil,fmt.Sprint(e));if e!=nil{continue}
  execution:=decoded["execution"].(map[string]any)
  for _,key:=range []string{"host_receipt","suspended_identity"}{
   object:=execution[key].(map[string]any);check(wanted+"-"+key+"-exact-string",object["process_created_ns"]==wanted,object["process_created_ns"])
   nested,_:=json.Marshal(object);canon,e:=canonical.JSON(nested);check(wanted+"-"+key+"-canonical",e==nil,fmt.Sprint(e))
   if key=="host_receipt"{var receipt sandbox.Receipt;e=json.Unmarshal(canon,&receipt);check(wanted+"-"+key+"-typed-roundtrip",e==nil&&receipt.Created==created,strconv.FormatInt(receipt.Created,10))}else{var identity sandbox.Identity;e=json.Unmarshal(canon,&identity);check(wanted+"-"+key+"-typed-roundtrip",e==nil&&identity.Created==created,strconv.FormatInt(identity.Created,10))}
  }
  again,e:=json.Marshal(decoded);if e!=nil{t.Fatal(e)};_,e=Decode(again);check(wanted+"-nested-remarshal-decode",e==nil,fmt.Sprint(e))
 }
 old:=[]byte(`{"execution":{"host_receipt":{"process_created_ns":1790787239271034300},"suspended_identity":{"process_created_ns":1790787239271034300}}}`)
 _,e:=Decode(old);check("legacy-lossy-numeric-still-rejected",e!=nil,fmt.Sprint(e))
}
