package main
import("os";"time";"path/filepath";"encoding/json";"encoding/base64";"crypto/sha256";"fmt";"io";"os/exec")
var binding string
func main(){
 if len(os.Args)>1&&os.Args[1]=="--hold-public-pipe"{time.Sleep(12*time.Second);return}
 executable,_:=os.Executable();modeBytes,_:=os.ReadFile(filepath.Join(filepath.Dir(executable),"fixture-mode.txt"));mode:=string(modeBytes)
 raw,_:=io.ReadAll(io.LimitReader(os.Stdin,33555461));var p map[string]interface{};json.Unmarshal(raw,&p)
 if mode=="nonzero"{os.Exit(7)}
 if mode=="hang"{time.Sleep(40*time.Second);return}
 if mode=="stderr-cap"{os.Stderr.Write(make([]byte,16385));time.Sleep(time.Second);return}
 if mode=="output-cap"{os.Stdout.Write(make([]byte,67108865));return}
 if mode=="truncated"{fmt.Print("{\"schema\":");return}
 req,_:=base64.StdEncoding.DecodeString(fmt.Sprint(p["request_raw_base64"]));res,_:=base64.StdEncoding.DecodeString(fmt.Sprint(p["response_raw_base64"]))
 v:=map[string]interface{}{"schema":"researchos.desktop.http-validation/1","phase":p["phase"],"nonce":p["nonce"],"http_status":p["http_status"],"request_sha256":fmt.Sprintf("%x",sha256.Sum256(req)),"response_sha256":fmt.Sprintf("%x",sha256.Sum256(res)),"schema_sha256_pair":[]string{"8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b","b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54"},"build_input_digest":binding,"outcome":"VALID","reason":"","value":nil}
 switch mode{case "version":v["schema"]="wrong";case "nonce":v["nonce"]="wrong";case "request-digest":v["request_sha256"]="wrong";case "response-digest":v["response_sha256"]="wrong";case "http-status":v["http_status"]=200;case "phase":v["phase"]="RESPONSE"}
 if mode=="unreaped"{c:=exec.Command(executable,"--hold-public-pipe");c.Stdout=os.Stdout;c.Stderr=os.Stderr;if c.Start()!=nil{os.Exit(9)};fmt.Fprintf(os.Stderr,"PUBLIC_FIXTURE_PIPE_HOLDER_PID=%d\n",c.Process.Pid)}
 b,_:=json.Marshal(v);if mode=="nbsp"{os.Stdout.Write([]byte{0xc2,0xa0})};os.Stdout.Write(b)
 if mode=="two-values"{os.Stdout.Write([]byte(" {}"))}
}
