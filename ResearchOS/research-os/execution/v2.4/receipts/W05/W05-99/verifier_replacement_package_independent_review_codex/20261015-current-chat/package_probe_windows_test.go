//go:build windows

package host

import (
 "debug/buildinfo"
 "encoding/json"
 "os"
 "path/filepath"
 "testing"
 "unsafe"
 "golang.org/x/sys/windows"
 "researchos.local/research-os/internal/domain"
 "researchos.local/research-os/internal/verifier"
)

func TestIndependentPackageNativeACLAndReplacementRead(t *testing.T) {
 root:=os.Getenv("REVIEW_PACKAGE_ROOT");if root==""{t.Fatal("explicit isolated package required")}
 user,e:=windows.GetCurrentProcessToken().GetTokenUser();if e!=nil{t.Fatal(e)};sid:=user.User.Sid.String()
 for _,row:=range []struct{name,hash string;limit int64}{
  {"runtime-verifier-installation.json","sha256:74ca846daf8f6ad82692b43dcd3b664fe2970247072546495d05519b01358609",64<<10},
  {"runtime-verifier.exe","sha256:f255f4d49c5b217462bb38a8ec2292e9d62889d8506488569ff3638237708a43",128<<20},
 } {
  t.Run(row.name,func(t *testing.T){
   path:=filepath.Join(root,"apps","desktop","resources","control",row.name)
   sd,e:=windows.GetNamedSecurityInfo(path,windows.SE_FILE_OBJECT,windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION);if e!=nil{t.Fatal(e)}
   owner,_,e:=sd.Owner();if e!=nil||owner==nil||owner.String()!=sid{t.Fatalf("owner mismatch: %v",e)}
   control,_,e:=sd.Control();if e!=nil||control&windows.SE_DACL_PROTECTED==0{t.Fatalf("unprotected DACL: %v",e)}
   acl,_,e:=sd.DACL();if e!=nil||acl==nil||acl.AceCount!=1{t.Fatalf("non-private DACL: %v",e)}
   var ace *windows.ACCESS_ALLOWED_ACE;if e=windows.GetAce(acl,0,&ace);e!=nil{t.Fatal(e)}
   aceSID:=(*windows.SID)(unsafe.Pointer(&ace.SidStart)).String()
   if aceSID!=sid||ace.Header.AceType!=windows.ACCESS_ALLOWED_ACE_TYPE||ace.Header.AceFlags!=0||ace.Mask!=0x001f01ff{t.Fatal("unexpected ACE")}
   raw,e:=replacementRead(path,row.limit);if e!=nil{t.Fatalf("frozen replacementRead: %v",e)}
   if domain.Digest(raw)!=row.hash{t.Fatal("unexpected bytes")}
   t.Logf("path=%q current_sid=%q owner=%q dacl_protected=true ace_count=%d ace_sid=%q ace_type=%d ace_flags=%d mask=0x%08x bytes=%d digest=%s replacementRead=PASS",path,sid,owner.String(),acl.AceCount,aceSID,ace.Header.AceType,ace.Header.AceFlags,ace.Mask,len(raw),domain.Digest(raw))
  })
 }
}

func TestIndependentPackageActualLoaders(t *testing.T){
 root:=os.Getenv("REVIEW_PACKAGE_ROOT");if root==""{t.Fatal("explicit isolated package required")}
 control:=filepath.Join(root,"apps","desktop","resources","control")
 install,e:=LoadRuntimeVerifierInstallation(filepath.Join(control,"runtime-verifier-installation.json"));if e!=nil{t.Fatal(e)}
 if install.Executable!=filepath.Join(control,"runtime-verifier.exe")||install.SourceCommit!="4f4023c956f84d65743f39ce77d6c8899a21ada1"||install.ServiceID!=verifier.ServiceID||install.Protocol!=verifier.Protocol||len(install.Arguments)!=0{t.Fatalf("installation mismatch: %+v",install)}
 assets,e:=LoadRuntimeSetupAssets(filepath.Join(control,"runtime"));if e!=nil{t.Fatal(e)}
 if assets.Executable!=filepath.Join(control,"runtime","node.exe")||assets.BundleFile!=filepath.Join(control,"runtime","mu-worker.mjs"){t.Fatalf("runtime paths mismatch: %+v",assets)}
 meta,e:=os.ReadFile(filepath.Join(control,"runtime","mu-worker.mjs.build.json"));if e!=nil{t.Fatal(e)}
 var m map[string]any;if e=json.Unmarshal(meta,&m);e!=nil{t.Fatal(e)}
 if m["mu_commit"]!="8dfebe36508ac0c2508735bb866756dab9283e74"||m["vendored_files_verified"]!=float64(5083)||m["bundle_sha256"]!="2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441"{t.Fatal("legacy runtime provenance mismatch")}
 t.Logf("LoadRuntimeVerifierInstallation=PASS installation=%+v",install)
 t.Logf("LoadRuntimeSetupAssets=PASS legacy_mu=%s assets=%+v",m["mu_commit"],assets)
}

func TestIndependentPackageNativeBuildMetadata(t *testing.T){
 root:=os.Getenv("REVIEW_PACKAGE_ROOT");if root==""{t.Fatal("explicit isolated package required")}
 for _,row:=range []struct{name,path string}{
  {"researchos-control.exe","researchos.local/research-os/apps/control"},
  {"runtime-verifier.exe","researchos.local/research-os/apps/runtime-verifier"},
 } {t.Run(row.name,func(t *testing.T){
  path:=filepath.Join(root,"apps","desktop","resources","control",row.name)
  info,e:=buildinfo.ReadFile(path);if e!=nil{t.Fatal(e)}
  settings:=map[string]string{};for _,s:=range info.Settings{settings[s.Key]=s.Value}
  if info.Path!=row.path||info.GoVersion!="go1.27.1"||settings["vcs.revision"]!="4f4023c956f84d65743f39ce77d6c8899a21ada1"||settings["vcs.modified"]!="false"||settings["GOOS"]!="windows"||settings["GOARCH"]!="amd64"{t.Fatalf("build provenance mismatch: %+v %+v",info,settings)}
  t.Logf("path=%q main=%q GoVersion=%q settings=%v",path,info.Path,info.GoVersion,settings)
 })}
}
