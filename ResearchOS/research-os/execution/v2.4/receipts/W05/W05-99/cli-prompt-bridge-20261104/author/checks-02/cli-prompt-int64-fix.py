from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
p=ROOT/'apps/cli/cli_prompt.go'
s=p.read_text(encoding='utf-8')
assert 'n > 9007199254740991' in s
s=s.replace('err != nil || n < 0 || n > 9007199254740991','err != nil || n < 0')
s=s.replace('exact nonnegative protocol integers','exact nonnegative int64 protocol integers')
p.write_text(s,encoding='utf-8',newline='\n')
p=ROOT/'apps/cli/cli_prompt_test.go'
s=p.read_text(encoding='utf-8').replace('{"unsafe-integer", []string{"--prompt=a", "--expected-revision=9007199254740992"}}','{"overflow-int64", []string{"--prompt=a", "--expected-revision=9223372036854775808"}}')
assert '"unsafe-integer"' not in s
s+='''
func TestCLIPromptExactInt64HostArguments(t *testing.T) {
    t.Setenv("RESEARCHOS_CLI_CREDENTIAL","fixture-only")
    for _,value:=range []int64{9007199254740993,9223372036854775807} {
        text:=fmt.Sprint(value)
        p,args,problem:=parseExplicitCLIPrompt([]string{"--prompt=--literal","--session=s1","--expected-revision="+text,"--writer-epoch="+text,"--after-sequence="+text})
        if problem!=nil {t.Fatalf("legal int64 rejected: %v",problem)}
        c:=newV2Context("run",args,cliConfig{ProjectID:"p1"},"http://127.0.0.1")
        if c.revision!=value || c.epoch!=value {t.Fatalf("integer changed: %+v",c)}
        steps,reason,_:=verbStepsWithPrompt("run",args,c,cliConfig{},p)
        if reason!="" || steps[len(steps)-1].payload["after_sequence"]!=value {t.Fatalf("sequence changed: %v %s",steps,reason)}
        raw,err:=json.Marshal(steps[len(steps)-1].payload)
        if err!=nil || !bytes.Contains(raw,[]byte(text)) {t.Fatalf("sequence rounded on wire: %s %v",raw,err)}
        env,why:=v2EnvelopeFor(c,"session.send",steps[1].payload)
        if why!="" {t.Fatal(why)}
        raw,err=json.Marshal(env)
        if err!=nil || !bytes.Contains(raw,[]byte("\\\"expected_revision\\\":"+text)) || !bytes.Contains(raw,[]byte("\\\"writer_epoch\\\":"+text)) {t.Fatalf("CAS/epoch rounded: %s %v",raw,err)}
    }
}
'''
s=s.replace('"encoding/json"\n','"encoding/json"\n    "fmt"\n')
p.write_text(s,encoding='utf-8',newline='\n')
print('removed unsupported 2^53 cap; added exact >2^53 and MaxInt64 wire tests')
