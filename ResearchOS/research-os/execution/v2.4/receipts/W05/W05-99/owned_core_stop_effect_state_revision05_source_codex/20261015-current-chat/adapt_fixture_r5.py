from pathlib import Path

p = Path(__file__).with_name("fixture_e2e_r5.py")
s = p.read_text(encoding="utf-8")
lines = s.splitlines()
for i, line in enumerate(lines):
    if line.startswith("WORKTREE = "):
        lines[i] = 'WORKTREE = Path.cwd().resolve()\nREPO = WORKTREE.parents[2]'
    elif line.startswith("GO = "):
        lines[i] = 'GO = REPO / ".local/tools/go1.27.1/go/bin/go.exe"'
    elif line.startswith("FIXTURE = "):
        lines[i] = 'FIXTURE = Path(r"C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-effect-state-r5-20261015/fixture-r5.exe")'
    elif line.startswith("parent_helper="):
        lines[i] = 'parent_helper=Path(r"C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-effect-state-r5-20261015/fixture-parent-r5.exe")'
    elif line.startswith("go_env="):
        lines[i] = 'TASK_TEMP = REPO / ".local/owned-core-stop-effect-state-r5-20261015-tmp"\ngo_env={"GOMODCACHE":str(REPO / ".local/tools/gopath/pkg/mod"),"GOCACHE":str(TASK_TEMP / "gocache"),"GOTMPDIR":str(TASK_TEMP / "gotmp"),"TMP":str(TASK_TEMP),"TEMP":str(TASK_TEMP),"GOOS":"windows","GOARCH":"amd64"}'
    elif line.startswith("data=Path("):
        lines[i] = 'data=TASK_TEMP/CASE.name/"data"'
s = "\n".join(lines) + "\n"
s = s.replace('("review_malformed_effect_preflight","positive",', '("r5_missing","r5_null","positive",')
s = s.replace('MODE=="review_malformed_effect_preflight"', 'MODE in ("r5_missing","r5_null")')
s = s.replace('json.dumps({"payload":{"capability":"MODEL"}})', 'json.dumps({"payload":{"capability":"MODEL"},**({"state":None} if MODE=="r5_null" else {})})')
s = s.replace('"review-extra-malformed-model"', '"r5-extra-malformed-model"')
s = s.replace('        unexpected=plan["eligibility"]=="ELIGIBLE_FOR_INDEPENDENT_REVIEW"', '        rejected=plan["eligibility"]=="STOP_UNAVAILABLE" and plan["preflight_safety"]["non_model_effects"]>=1')
s = s.replace('"additional_effect_body":{"payload":{"capability":"MODEL"}},"stop_grant_built":False,"native_signal_count":0,"source_safety_failure_reproduced":unexpected', '"additional_effect_body":{"payload":{"capability":"MODEL"},**({"state":None} if MODE=="r5_null" else {})},"stop_grant_built":False,"native_signal_count":0,"source_safety_rejected":rejected,"core_alive":core.poll() is None,"zero_stop_attempt":not (out/"STOP_ATTEMPT.json").exists()')
s = s.replace('        if unexpected:raise AssertionError("STOP-R4-F01: actual compiled preflight authorized malformed additional MODEL effect")', '        if not rejected or core.poll() is not None or (out/"STOP_ATTEMPT.json").exists():raise AssertionError("r5 compiled preflight failed to reject unresolved additional MODEL effect")')
p.write_text(s, encoding="utf-8")
