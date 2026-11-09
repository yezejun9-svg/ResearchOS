//go:build windows
package host
import("context";"encoding/json";"os";"path/filepath";"strings";"testing";"researchos.local/research-os/internal/domain")
func TestIndependentActual326ProductionChecker(t *testing.T){
 scopePath:=os.Getenv("REVIEW_SCOPE_INPUT");workspace:=os.Getenv("REVIEW_ACTUAL326_FIXTURE");if scopePath==""||workspace==""{t.Fatal("explicit read-only fixture inputs required")}
 raw,e:=os.ReadFile(scopePath);if e!=nil{t.Fatal(e)}
 var s struct{SourcePaths []string;Package,TestPattern,ToolchainRoot,VendorRoot string}
 if e=json.Unmarshal(raw,&s);e!=nil{t.Fatal(e)};if len(s.SourcePaths)!=326{t.Fatal("wrong original scope",len(s.SourcePaths))}
 root,e:=os.OpenRoot(workspace);if e!=nil{t.Fatal(e)};defer root.Close()
 check:=domain.RuntimeCodingCheck{SourcePaths:s.SourcePaths,Package:s.Package,TestPattern:s.TestPattern,ToolchainRoot:s.ToolchainRoot,VendorRoot:s.VendorRoot}
 e=validateCodingCheckSources(context.Background(),root,workspace,check)
 if os.Getenv("REVIEW_BASELINE")=="1"{if e==nil||!strings.Contains(e.Error(),"missing same-package helper: any"){t.Fatalf("baseline wrong reproduction: %v",e)};t.Log("BASELINE_REAL326_REJECTED_ANY: "+e.Error())}else{if e!=nil{t.Fatal(e)};t.Log("CANDIDATE_REAL326_PRODUCTION_CHECKER_PASS read=326 unchanged scope")}
}
func TestIndependentAnyAndMissingHelper(t *testing.T){
 for _,name:=range []string{"production_any_nil","test_nested_any_nil","helper_missing_in_test","helper_missing_in_production","omitted_test_helper","dot_import_with_any"}{t.Run(name,func(t *testing.T){
  root,workspace,check:=codingInventory(t)
  write:=func(p,s string){t.Helper();if e:=os.WriteFile(filepath.Join(workspace,filepath.FromSlash(p)),[]byte(s),0600);e!=nil{t.Fatal(e)}}
  write("pkg/main.go","package pkg\nfunc Value() any{return any(nil)}\n")
  write("pkg/main_test.go","package pkg\nimport \"testing\"\nfunc TestSelected(t *testing.T){if Value()!=nil {t.Fatal(\"expected nil\")}}\n")
  positive:=false
  switch name{
  case "production_any_nil":positive=true
  case "test_nested_any_nil":positive=true;write("pkg/main.go","package pkg\nfunc Value()int{return 1}\n");write("pkg/main_test.go","package pkg\nimport \"testing\"\nfunc TestSelected(t *testing.T){if any(any(nil))!=nil{t.Fatal(\"expected nil\")}}\n")
  case "helper_missing_in_test":write("pkg/main_test.go","package pkg\nimport \"testing\"\nfunc TestSelected(t *testing.T){missingHelper(any(nil));_=any(nil)}\n")
  case "helper_missing_in_production":write("pkg/main.go","package pkg\nfunc Value()any{return missingHelper(any(nil))}\n")
  case "omitted_test_helper":write("pkg/omitted_test.go","package pkg\nfunc missingHelper(x any){}\n");write("pkg/main_test.go","package pkg\nimport \"testing\"\nfunc TestSelected(t *testing.T){missingHelper(any(nil))}\n")
  case "dot_import_with_any":write("pkg/main_test.go","package pkg\nimport . \"testing\"\nfunc TestSelected(t *T){_=any(nil)}\n")
  }
  e:=validateCodingCheckSources(context.Background(),root,workspace,check)
  if os.Getenv("REVIEW_BASELINE")=="1" && positive {if e==nil||!strings.Contains(e.Error(),"missing same-package helper: any"){t.Fatalf("expected old any rejection: %v",e)};return}
  if positive {if e!=nil{t.Fatal(e)};return}
  if e==nil {t.Fatal("unauthorized helper/import accepted")}
  if os.Getenv("REVIEW_BASELINE")!="1" && name!="dot_import_with_any"&&!strings.Contains(e.Error(),"missing same-package helper: missingHelper"){t.Fatalf("wrong rejection: %v",e)}
 })}
}
