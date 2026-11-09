//go:build windows

package supervisor

import (
 "os"
 "path/filepath"
 "strings"
 "testing"
 "golang.org/x/sys/windows"
)

func TestReviewNativeACLContinuityAndAppendOnly(t *testing.T) {
 operator:=testOperatorSID(t)
 trusted:="(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;"+operator+")"
 for _,target:=range []string{"ancestor", "final"} {t.Run(target,func(t *testing.T){
  dir:=filepath.Join(reviewFixtureDir(t),"selected")
  if err:=os.Mkdir(dir,0700);err!=nil{t.Fatal(err)}
  setTestImageDACL(t,dir,"D:P"+trusted+"(A;;0x4;;;WD)")
  path:=filepath.Join(dir,"selected.exe")
  raw,err:=os.ReadFile(os.Args[0]);if err!=nil{t.Fatal(err)}
  if err=os.WriteFile(path,raw,0600);err!=nil{t.Fatal(err)}
  sd,err:=windows.GetNamedSecurityInfo(dir,windows.SE_FILE_OBJECT,windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
  if err!=nil{t.Fatal(err)};t.Logf("NATIVE_DIRECTORY_SDDL %s",sd.String())
  im,err:=ownedNativeImage(path);if err!=nil{t.Fatalf("isolated FILE_ADD_SUBDIRECTORY rejected: %v",err)};defer im.Close()
  wide,_:=windows.UTF16PtrFromString(dir)
  writer,e:=windows.CreateFile(wide,windows.GENERIC_WRITE,windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,nil,windows.OPEN_EXISTING,windows.FILE_FLAG_BACKUP_SEMANTICS,0)
  if e==nil {defer windows.CloseHandle(writer);t.Log("DIRECTORY_GENERIC_WRITE_OPENED")} else {t.Logf("DIRECTORY_GENERIC_WRITE_DENIED %v",e)}
  if err=os.Rename(dir,dir+"-moved");err==nil{t.Fatal("selected directory renamed under retention")};t.Logf("SELECTED_RENAME_DENIED %v",err)
  if target=="ancestor" {setTestImageDACL(t,dir,"D:P"+trusted+"(A;;GR;;;BU)")} else {setTestImageDACL(t,path,"D:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;"+operator+")(A;;GR;;;BU)")}
  if err=verifyOwnedImageFile(im,im.final.volume,im.final.index);err==nil{t.Fatal("authorized but changed ACL accepted")};t.Logf("AUTHORIZED_ACL_DRIFT_REFUSED %v",err)
 })}
}

func TestReviewInheritOnlyAppliedAtDescendant(t *testing.T) {
 operator:=testOperatorSID(t)
 dir:=filepath.Join(reviewFixtureDir(t),"inherit-only")
 if err:=os.Mkdir(dir,0700);err!=nil{t.Fatal(err)}
 setTestImageDACL(t,dir,"D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;"+operator+")(A;OIIO;GW;;;WD)")
 parent,err:=windows.GetNamedSecurityInfo(dir,windows.SE_FILE_OBJECT,windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION);if err!=nil{t.Fatal(err)}
 if err=imageSecurityAuthorized(parent,true);err!=nil{t.Fatalf("inherit-only on parent rejected: %v",err)}
 path:=filepath.Join(dir,"child.exe");if err=os.WriteFile(path,[]byte("owned review image"),0600);err!=nil{t.Fatal(err)}
 child,err:=windows.GetNamedSecurityInfo(path,windows.SE_FILE_OBJECT,windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION);if err!=nil{t.Fatal(err)}
 t.Logf("NATIVE_INHERIT_ONLY_PARENT %s CHILD %s",parent.String(),child.String())
 if im,e:=ownedNativeImage(path);e==nil{im.Close();t.Fatal("effective inherited write reached retained image")}else if !strings.Contains(e.Error(),"image DACL grants write or control"){t.Fatalf("unexpected refusal: %v",e)}else{t.Logf("INHERITED_CHILD_WRITE_REFUSED %v",e)}
}
