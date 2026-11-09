from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
p=ROOT/'apps/cli/cli_prompt.go'
s=p.read_text(encoding='utf-8').replace('strings.Cut(strings.TrimLeft(token, "-"), "=")','strings.Cut(strings.TrimPrefix(strings.TrimPrefix(token, "-"), "-"), "=")')
p.write_text(s,encoding='utf-8',newline='\n')
TEST=r'''package main

import (
    "bufio"
    "bytes"
    "context"
    "encoding/json"
    "io"
    "net/http"
    "net/http/httptest"
    "os"
    "os/exec"
    "path/filepath"
    "reflect"
    "strings"
    "sync/atomic"
    "testing"
    "time"
)

func TestCLIPromptParseExplicit(t *testing.T) {
    for _,tc:=range []struct{name string;args []string;text string;host []string}{
        {"separate",[]string{"--prompt","中文\n多行\r\n"},"中文\n多行\r\n",[]string{}},
        {"equals",[]string{"--prompt=中文 空格","--project","p1","--output=jsonl"},"中文 空格",[]string{"--project=p1","--output=jsonl"}},
        {"leading-single-hyphen",[]string{"--prompt","-dir"},"-dir",[]string{}},
        {"leading-double-hyphen",[]string{"--prompt=--prompt-file=x"},"--prompt-file=x",[]string{}},
        {"literal-prompt-option",[]string{"--prompt","--prompt"},"--prompt",[]string{}},
        {"host-before-prompt",[]string{"--session=s1","--writer-epoch","3","--prompt","text"},"text",[]string{"--session=s1","--writer-epoch=3"}},
        {"max-runes",[]string{"--prompt",strings.Repeat("😀",cliPromptMaxRunes)},strings.Repeat("😀",cliPromptMaxRunes),[]string{}},
    } {t.Run(tc.name,func(t *testing.T){p,args,problem:=parseExplicitCLIPrompt(tc.args);if problem!=nil||p==nil||p.text!=tc.text||!reflect.DeepEqual(args,tc.host){t.Fatalf("p=%v args=%v problem=%v",p,args,problem)}})}
}

func TestCLIPromptLegacyArgsUntouched(t *testing.T) {
    for _,args:=range [][]string{
        nil,{}, {"a normal positional prompt","--project","p1"},
        {"-dir","old","-job","job"},
        {"--replace","--prompt","--file","a","--check","x"},
        {"--replace=x=>--prompt","--file=a","--check=x"},
        {"--file","--prompt-file","--replace=a=>b","--check=x"},
        {"--","--prompt"},
    } {p,out,problem:=parseExplicitCLIPrompt(args);if p!=nil||problem!=nil||!reflect.DeepEqual(out,args){t.Fatalf("legacy invocation changed: %v -> %v %v",args,out,problem)}}
}

func TestCLIPromptRejectInvalid(t *testing.T) {
    for _,tc:=range []struct{name string;args []string}{
        {"missing",[]string{"--prompt"}}, {"missing-file",[]string{"--prompt-file="}},
        {"empty",[]string{"--prompt="}}, {"whitespace",[]string{"--prompt"," \r\n\t"}},
        {"duplicate",[]string{"--prompt=a","--prompt=b"}},
        {"conflicting-sources",[]string{"--prompt=a","--prompt-file=b"}},
        {"legacy-file",[]string{"--prompt=a","--file=x"}},
        {"legacy-check",[]string{"--prompt=a","-check","cmd"}},
        {"legacy-dir-first",[]string{"-dir","old","--prompt=a"}},
        {"extra-positional",[]string{"--prompt=a","extra"}},
        {"unknown",[]string{"--prompt=a","--model=other"}},
        {"triple-prefix",[]string{"--prompt=a","---project=p1"}},
        {"duplicate-host",[]string{"--prompt=a","--project=p1","--project=p2"}},
        {"missing-host",[]string{"--project","--prompt=a"}},
        {"bad-output",[]string{"--prompt=a","--output=text"}},
        {"bad-epoch",[]string{"--prompt=a","--writer-epoch=bad"}},
        {"negative-sequence",[]string{"--prompt=a","--after-sequence=-1"}},
        {"unsafe-integer",[]string{"--prompt=a","--expected-revision=9007199254740992"}},
        {"invalid-utf8",[]string{"--prompt",string([]byte{0xff})}},
        {"too-many-runes",[]string{"--prompt",strings.Repeat("中",cliPromptMaxRunes+1)}},
    } {t.Run(tc.name,func(t *testing.T){p,_,problem:=parseExplicitCLIPrompt(tc.args);if p!=nil||problem==nil||problem.code!=exitUsage {t.Fatalf("invalid input accepted: p=%v problem=%v",p,problem)};if strings.Contains(problem.detail,"secret-prompt") {t.Fatal("error exposed body")}})}
}

type cliPromptCountingReader struct {read int; remaining int}
func (r *cliPromptCountingReader) Read(p []byte)(int,error){if r.remaining==0{return 0,io.EOF};n:=len(p);if n>r.remaining{n=r.remaining};for i:=0;i<n;i++{p[i]='a'};r.read+=n;r.remaining-=n;return n,nil}

func TestCLIPromptFileBounded(t *testing.T) {
    dir:=t.TempDir();file:=filepath.Join(dir,"中文 空格.txt")
    valid:=strings.Repeat("😀",cliPromptMaxRunes)
    if err:=os.WriteFile(file,[]byte(valid),0600);err!=nil{t.Fatal(err)}
    p,_,problem:=parseExplicitCLIPrompt([]string{"--prompt-file",file})
    if problem!=nil||p==nil||p.text!=valid{t.Fatalf("65536-byte exact boundary failed: %v",problem)}
    for _,raw:=range [][]byte{{0xff},[]byte(" \r\n"),[]byte(strings.Repeat("a",cliPromptMaxFileBytes+1))} {
        if err:=os.WriteFile(file,raw,0600);err!=nil{t.Fatal(err)}
        if p,_,problem:=parseExplicitCLIPrompt([]string{"--prompt-file="+file});p!=nil||problem==nil{t.Fatal("invalid file accepted")}
    }
    if _,_,problem:=parseExplicitCLIPrompt([]string{"--prompt-file",dir});problem==nil{t.Fatal("directory accepted")}
    if _,_,problem:=parseExplicitCLIPrompt([]string{"--prompt-file",filepath.Join(dir,"absent")});problem==nil||problem.code!=exitFailed{t.Fatal("missing file accepted")}
    reader:=&cliPromptCountingReader{remaining:1<<20}
    if _,problem:=readCLIPrompt(reader);problem==nil||reader.read!=cliPromptMaxFileBytes+1{t.Fatalf("unbounded read: %d %v",reader.read,problem)}
}

func TestCLIPromptTypedStepsRetainSnapshotAndText(t *testing.T) {
    file:=filepath.Join(t.TempDir(),"prompt.txt");text:="--prompt-file=literal\r\n中文 -dir"
    os.WriteFile(file,[]byte(text),0600)
    p,args,problem:=parseExplicitCLIPrompt([]string{"--prompt-file",file,"--project=p1"})
    if problem!=nil{t.Fatal(problem)}
    os.WriteFile(file,[]byte("changed after parsing"),0600)
    steps,reason,_:=verbStepsWithPrompt("run",args,&v2Context{},cliConfig{WorkspaceRef:"fixed-ws",Model:"fixed-model"},p)
    if reason!=""||len(steps)!=3||steps[0].method!="session.create"||steps[0].payload["model_config_ref"]!="fixed-model"||steps[1].method!="session.send"||steps[1].payload["text"]!=text||len(steps[1].payload)!=3{t.Fatalf("typed prompt changed flow/authority: %+v %s",steps,reason)}
    if _,has:=firstPositional(args);has{t.Fatal("prompt was serialized back into argv")}
}

// This child invokes only the CLI entry against explicit loopback HTTP fixtures.
// Native credential acquisition is disabled by its fixture credential. The old
// cascade is replaced with a spy and is never executed by these tests.
func TestCLIPromptChildEntry(t *testing.T) {
    if os.Getenv("RESEARCHOS_TEST_PROMPT_CHILD")!="1"{return}
    var args []string
    if err:=json.Unmarshal([]byte(os.Getenv("RESEARCHOS_TEST_PROMPT_ARGS")),&args);err!=nil{panic(err)}
    acceptedRun=func(args []string){outJSON(map[string]any{"command":"legacy-cascade-spy","args":args})}
    os.Args=append([]string{os.Args[0]},args...)
    main()
    os.Exit(0)
}

func cliPromptChild(t *testing.T,args []string,url string)([]byte,[]byte,int) {
    t.Helper();dir:=t.TempDir();discoveryFile,configFile:=filepath.Join(dir,"host.json"),filepath.Join(dir,"config.json")
    raw,_:=json.Marshal(discovery{URL:url});if err:=os.WriteFile(discoveryFile,raw,0600);err!=nil{t.Fatal(err)}
    raw,_=json.Marshal(cliConfig{ProjectID:"p1",WorkspaceRef:"ws-fixture",Model:"fixed-model"});if err:=os.WriteFile(configFile,raw,0600);err!=nil{t.Fatal(err)}
    encoded,_:=json.Marshal(args)
    ctx,cancel:=context.WithTimeout(context.Background(),15*time.Second);defer cancel()
    cmd:=exec.CommandContext(ctx,os.Args[0],"-test.run=^TestCLIPromptChildEntry$")
    cmd.Env=append(os.Environ(),"RESEARCHOS_TEST_PROMPT_CHILD=1","RESEARCHOS_TEST_PROMPT_ARGS="+string(encoded),"RESEARCHOS_CLI_DISCOVERY="+discoveryFile,"RESEARCHOS_CLI_CONFIG="+configFile,"RESEARCHOS_CLI_CREDENTIAL=fixture-only","RESEARCHOS_CLI_CLIENT_ID=c1")
    var stdout,stderr bytes.Buffer;cmd.Stdout=&stdout;cmd.Stderr=&stderr
    err:=cmd.Run();code:=0
    if err!=nil {if e,ok:=err.(*exec.ExitError);ok{code=e.ExitCode()}else{t.Fatal(err)}}
    return stdout.Bytes(),stderr.Bytes(),code
}

func cliPromptSummary(t *testing.T,raw []byte)map[string]any{
    t.Helper();scanner:=bufio.NewScanner(bytes.NewReader(raw));scanner.Buffer(make([]byte,4096),1<<20)
    var summary map[string]any
    for scanner.Scan(){var row map[string]any;if err:=json.Unmarshal(scanner.Bytes(),&row);err!=nil{t.Fatalf("non-JSON stdout: %s",scanner.Text())};if row["command"]!=nil{summary=row}}
    if scanner.Err()!=nil||summary==nil{t.Fatalf("missing JSON summary: %v %s",scanner.Err(),raw)}
    return summary
}

func TestCLIPromptEntryFixture(t *testing.T) {
    for _,verb:=range []string{"run","task"}{for _,fileMode:=range []bool{false,true}{t.Run(verb+map[bool]string{false:"/text",true:"/file"}[fileMode],func(t *testing.T){
        f:=newCLIStreamFixture(t,"paged");text:="--prompt-file=literal\r\n中文 -dir -job"
        args:=[]string{verb,"--prompt",text,"--output=jsonl"}
        if fileMode {file:=filepath.Join(t.TempDir(),"中文 prompt.txt");os.WriteFile(file,[]byte(text),0600);args=[]string{verb,"--prompt-file="+file,"--session=s1","--output=jsonl"}}
        stdout,stderr,code:=cliPromptChild(t,args,f.server.URL);summary:=cliPromptSummary(t,stdout)
        if code!=0||summary["command"]!=verb||summary["status"]!="EXECUTION_REPORTED"||cliObject(summary["execution"])["independent_acceptance"]!="NOT_EVALUATED"{t.Fatalf("code=%d out=%v stderr=%s",code,summary,stderr)}
        f.mu.Lock();defer f.mu.Unlock()
        if f.sendCalls!=1||f.pages<2{t.Fatalf("calls=%d pages=%d",f.sendCalls,f.pages)}
        var env map[string]any;json.Unmarshal([]byte(f.sendBodies[0]),&env)
        payload:=cliObject(env["payload"])
        if payload["text"]!=text||len(payload)!=3||env["writer_epoch"]!=float64(1){t.Fatalf("text/authority changed: %v",env)}
        for _,method:=range f.methods{if method=="goal.start"{t.Fatal("changed protocol into explicit Goal")}}
    })}}
}

func TestCLIPromptEntryRejectsBeforeHTTP(t *testing.T) {
    var requests atomic.Int64
    server:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){requests.Add(1);http.Error(w,"unexpected request",500)}));defer server.Close()
    badFile:=filepath.Join(t.TempDir(),"bad.txt");os.WriteFile(badFile,[]byte{0xff},0600)
    for _,verb:=range []string{"task","run"}{for _,args:=range [][]string{
        {"--prompt"},{"--prompt="},{"--prompt"," \n"},{"--prompt=a","--prompt=b"},{"--prompt=a","--prompt-file=x"},
        {"--prompt=a","--file=x"},{"--prompt=a","-dir","old"},{"--prompt=a","--model=changed"},
        {"--prompt=a","--writer-epoch=bad"},{"--prompt=a","--output=text"},{"--project","--prompt=a"},
        {"--prompt-file",badFile},{"--prompt-file",filepath.Join(t.TempDir(),"absent")},
    }{stdout,stderr,code:=cliPromptChild(t,append([]string{verb},args...),server.URL);summary:=cliPromptSummary(t,stdout);if code==0||summary["status"]!="REJECTED"||summary["reason"]=="HOST_DISCOVERY_UNAVAILABLE"{t.Fatalf("invalid input reached host: code=%d out=%v stderr=%s",code,summary,stderr)}}}
    if requests.Load()!=0{t.Fatalf("invalid input made %d HTTP requests",requests.Load())}
}

func TestCLIPromptLegacyCascadeDelegated(t *testing.T) {
    for _,args:=range [][]string{{"run"},{"run","-dir","old","-job","j"},{"run","-dir=--prompt","-job=j"}}{
        stdout,_,code:=cliPromptChild(t,args,"");summary:=cliPromptSummary(t,stdout)
        if code!=0||summary["command"]!="legacy-cascade-spy"{t.Fatalf("legacy run changed: %s",stdout)}
        encoded,_:=json.Marshal(args[1:]);got,_:=json.Marshal(summary["args"]);if !bytes.Equal(encoded,got){t.Fatalf("legacy arguments changed: %s -> %s",encoded,got)}
    }
    stdout,_,code:=cliPromptChild(t,[]string{"task"},"")
    if code!=2||!bytes.Contains(stdout,[]byte("task: INVALID_REQUEST: -file is required")){t.Fatalf("legacy task changed: code=%d %s",code,stdout)}
}

func TestCLIPromptFollowRetainsOutcomes(t *testing.T) {
    for _,tc:=range []struct{mode string;code int}{{"blocked",3},{"unknown",3},{"children",3},{"missing-artifact",3},{"failed",1},{"cancel-pending",130}}{t.Run(tc.mode,func(t *testing.T){
        f:=newCLIStreamFixture(t,tc.mode);p,args,problem:=parseExplicitCLIPrompt([]string{"--prompt=--literal"});if problem!=nil{t.Fatal(problem)}
        c:=&v2Context{clientID:"c1",credential:"fixture-only",projectID:"p1",commandID:"typed-follow",baseURL:f.server.URL}
        options:=cliFollowOptions{300*time.Millisecond,time.Millisecond,120*time.Millisecond,f.signals,func(map[string]any){}}
        out,code:=runCLIVerbWithPrompt("run",args,c,cliConfig{WorkspaceRef:"ws-fixture",Model:"fixed-model"},options,p)
        if code!=tc.code||out["status"]=="ACCEPTED"||cliObject(out["execution"])["independent_acceptance"]!="NOT_EVALUATED"{t.Fatalf("code=%d out=%v",code,out)}
    })}
}
'''
p=ROOT/'apps/cli/cli_prompt_test.go'
assert not p.exists()
p.write_text(TEST,encoding='utf-8',newline='\n')
print('prompt-specific tests written; no runtime/provider/native called')
