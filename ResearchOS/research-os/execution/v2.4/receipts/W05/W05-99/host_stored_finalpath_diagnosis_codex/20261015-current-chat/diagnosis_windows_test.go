//go:build windows
package host

import (
 "encoding/json"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "unicode/utf16"
 "unicode/utf8"
)

func modeledBug(path string) string {
 raw := "\\\\?\\" + path
 n := len(utf16.Encode([]rune(raw)))
 if len(raw)>n { raw=raw[:n] }
 return strings.TrimPrefix(raw, "\\\\?\\")
}

func TestDiagnosisExistingProductionIdentity(t *testing.T) {
 base:=os.Getenv("DIAGNOSIS_FIXTURE_ROOT")
 if base=="" {t.Fatal("explicit owned fixture root required")}
 base,err:=filepath.Abs(base);if err!=nil {t.Fatal(err)}
 if !strings.Contains(base,"host-stored-finalpath-diagnosis-20261015-tmp") {t.Fatal("outside owned scope")}
 cases:=[]string{"ascii-tail-20261012","unicode-工作区-tail-20261012","nonbmp-😀-tail-20261012","collision-000001","collision-000002"}
 finals:=[]string{};ids:=[]uint64{}
 for _,leaf:=range cases {
  path:=filepath.Join(base,leaf)
  if err:=os.MkdirAll(path,0700);err!=nil {t.Fatal(err)}
  vol,id,final,err:=fileIdentity(path)
  if err!=nil {t.Fatal(err)}
  expected:=modeledBug(path)
  if final!=expected {t.Fatalf("not reproduced: got %q modeled %q",final,expected)}
  if final==path {t.Fatal("expected known UTF16/UTF8 mismatch under owned CJK root")}
  if vol==""||id==0 {t.Fatal("missing existing production native identity")}
  raw:= "\\\\?\\"+path
  b,_:=json.Marshal(map[string]any{"path":path,"final":final,"volume":vol,"file_id":id,"raw_utf8_bytes":len(raw),"raw_utf16_units":len(utf16.Encode([]rune(raw))),"lost_bytes":len(path)-len(final),"utf8_valid":utf8.ValidString(final),"modeled_bug_matches":true})
  t.Log(string(b))
  finals=append(finals,final);ids=append(ids,id)
 }
 if finals[3]!=finals[4] {t.Fatal("expected same truncated final string for different suffixes")}
 if ids[3]==ids[4] {t.Fatal("expected distinct native file IDs for separate owned dirs")}
 t.Log("Distinct fresh directories collide in truncated FinalPath but retain distinct native IDs")
}

func TestDiagnosisFrozenMetadataArithmetic(t *testing.T) {
 // Frozen strings only: never open the original workspace or registry.
 path:="D:\\作品集\\ResearchOS\\research-os\\.local\\worktrees\\w05-own-cli-product-agent-20261012"
 stored:="D:\\作品集\\ResearchOS\\research-os\\.local\\worktrees\\w05-own-cli-product-agent-20"
 got:=modeledBug(path)
 if got!=stored {t.Fatalf("frozen suffix mismatch got %q want %q",got,stored)}
 b,_:=json.Marshal(map[string]any{"frozen_real_path":path,"frozen_stored_final_path":stored,"modeled_result":got,"lost_bytes":len(path)-len(stored),"exact_match":true,"original_path_opened":false})
 t.Log(string(b))
}
