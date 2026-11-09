from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
p=ROOT/'apps/cli/cli_contract.go'
s=p.read_text(encoding='utf-8')
old='''		entries = append(entries, map[string]any{"command": n, "handler": c.handler, "check_id": c.check,
			"owner": c.owned, "state": state, "needs": c.needs, "method_sent": c.method,
			"proven_by": c.proven, "proven_count": len(c.proven)})'''
new='''		entry := map[string]any{"command": n, "handler": c.handler, "check_id": c.check,
			"owner": c.owned, "state": state, "needs": c.needs, "method_sent": c.method,
			"proven_by": c.proven, "proven_count": len(c.proven)}
        if n=="task" || n=="run" {
            entry["state_scope"]="existing legacy/positional branch; explicit prompt qualification is separate"
            entry["explicit_prompt_mode"]=map[string]any{"state":"IMPLEMENTED","qualification":"DEVELOPMENT_ONLY","independent_acceptance":"NOT_EVALUATED","method_sent":"session.send + session.events","sources":[]string{"--prompt","--prompt-file"}}
        }
        entries=append(entries,entry)'''
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
print('help modes distinguish legacy state from explicit prompt development qualification')
