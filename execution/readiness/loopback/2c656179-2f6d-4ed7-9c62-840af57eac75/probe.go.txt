package main
import("context";"encoding/json";"net";"os";"os/exec";"time";"fmt")
func emit(v any){ json.NewEncoder(os.Stdout).Encode(v) }
func main(){
 l,e:=net.Listen("tcp4","127.0.0.1:0"); if e!=nil{emit(map[string]any{"stage":"listen","error":e.Error()});os.Exit(2)};defer l.Close()
 emit(map[string]any{"stage":"listen","address":l.Addr().String()})
 go func(){for{c,e:=l.Accept();if e!=nil{return};go func(){defer c.Close();c.SetDeadline(time.Now().Add(3*time.Second));b:=make([]byte,4);n,e:=c.Read(b);if e==nil{c.Write(b[:n])}}()}}()
 began:=time.Now();c,e:=net.DialTimeout("tcp4",l.Addr().String(),3*time.Second)
 r:=map[string]any{"stage":"go_client","elapsed_ms":time.Since(began).Milliseconds()}
 if e!=nil{r["error"]=e.Error()}else{c.SetDeadline(time.Now().Add(3*time.Second));_,e=c.Write([]byte("diag"));b:=make([]byte,4);n,re:=c.Read(b);r["echo"]=string(b[:n]);if e!=nil{r["write_error"]=e.Error()};if re!=nil{r["read_error"]=re.Error()};c.Close()};emit(r)
 ctx,cancel:=context.WithTimeout(context.Background(),8*time.Second);defer cancel()
 py:=`import socket,sys,json,time; host,port=sys.argv[1].split(':'); start=time.monotonic()
try:
 s=socket.create_connection((host,int(port)),3);s.settimeout(3);s.sendall(b'diag');result={'stage':'python_client','echo':s.recv(4).decode(),'elapsed_ms':round((time.monotonic()-start)*1000)};s.close()
except Exception as e: result={'stage':'python_client','error':str(e),'elapsed_ms':round((time.monotonic()-start)*1000)}
print(json.dumps(result))`
 raw,e:=exec.CommandContext(ctx,os.Args[1],"-X","utf8","-c",py,l.Addr().String()).CombinedOutput();fmt.Print(string(raw));if e!=nil{emit(map[string]any{"stage":"python_process","error":e.Error()})}
}