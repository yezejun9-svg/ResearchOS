from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
p=ROOT/'apps/cli/cli_prompt_test.go'
s=p.read_text(encoding='utf-8')
assert 'func TestCLIPromptSurfaceQualifications' not in s
s+='''
func TestCLIPromptSurfaceQualifications(t *testing.T) {
    entries,_,_,_:=surfaceEntries()
    count:=0
    for _,item:=range entries {
        entry:=item.(map[string]any)
        if entry["command"]!="task" && entry["command"]!="run" {continue}
        mode:=entry["explicit_prompt_mode"].(map[string]any)
        if entry["state"]!="ACCEPTED" || mode["state"]!="IMPLEMENTED" || mode["qualification"]!="DEVELOPMENT_ONLY" || mode["independent_acceptance"]!="NOT_EVALUATED" || entry["state_scope"]==nil {t.Fatalf("prompt inherited legacy acceptance: %v",entry)}
        count++
    }
    if count!=2 {t.Fatal("missing explicit prompt metadata")}
}
'''
p.write_text(s,encoding='utf-8',newline='\n')
print('prompt qualification test added')
