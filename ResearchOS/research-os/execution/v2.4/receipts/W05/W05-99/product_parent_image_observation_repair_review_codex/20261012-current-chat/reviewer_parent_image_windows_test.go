//go:build windows

package supervisor

import (
 "os"
 "testing"
 "golang.org/x/sys/windows"
)

func TestReviewerParentImageActualSeparatedBounds(t *testing.T) {
 if *observedElectronPID==0 { t.Fatal("original live Electron PID required") }
 h,e:=windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION,false,uint32(*observedElectronPID));if e!=nil{t.Fatal(e)}
 defer windows.CloseHandle(h)
 buf:=make([]uint16,32768);n:=uint32(len(buf));if e=windows.QueryFullProcessImageName(h,0,&buf[0],&n);e!=nil{t.Fatal(e)}
 path:=windows.UTF16ToString(buf[:n]);st,e:=os.Stat(path);if e!=nil{t.Fatal(e)}
 if st.Size()!=204521984{t.Fatalf("original image size changed: %d",st.Size())}
 if _,_,e=exactImage(path);e==nil{t.Fatal("unchanged release policy accepted actual large Electron")}
 digest,e:=observedProcessImageDigest(path);if e!=nil||digest!=*observedElectronHash{t.Fatal("observation did not accept exact original large image",e)}
 p,e:=ObserveProcess(uint32(*observedElectronPID));if e!=nil||p.ImageSHA256!=digest{t.Fatal("OS identity mismatch",e)}
 if alive,e:=(NativeFixtureDriver{}).Alive(p);e!=nil||!alive{t.Fatal("original identity not alive",e)}
 t.Logf("same actual OS path: exactImage_128=refused observed_256=accepted size=%d SHA256=%s PID=%d CreatedNS=%d no_signal=true",st.Size(),digest,p.PID,p.CreatedNS)
}
