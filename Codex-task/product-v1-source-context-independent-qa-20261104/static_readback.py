from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
OLD=R.parent/'product-v1-backend-independent-qa-20261104/run-04/frozen-source'
old=(OLD/'adapters/runtime/codex_driver_windows.go').read_text(encoding='utf-8')
new=(R/'source/adapters/runtime/codex_driver_windows.go').read_text(encoding='utf-8')
def arguments(s):
 a=s.index('func (d *codexCLI) arguments(');b=s.index('\n}\n',a)+3;return s[a:b]
assert arguments(old)==arguments(new)
assert new.index('executionInput, err := codexExecutionInput')<new.index('binary, err := os.Open')<new.index('os.Mkdir(in.Directory')<new.index('launchWithCallback')
assert 'stdinW.Write(executionInput)' in new and 'io.WriteString(stdinW, in.Prompt)' not in new
oldtest=(OLD/'internal/domain/runtime_harness_windows_test.go').read_text(encoding='utf-8')
newtest=(R/'source/internal/domain/runtime_harness_windows_test.go').read_text(encoding='utf-8')
a=oldtest.index('\tprogram := `package main');b=oldtest.index('\n\tif err := os.WriteFile(source',a)
na=newtest.index('\tprogram := `package main');nb=newtest.index('\n\tif err := os.WriteFile(source',na)
assert oldtest[:a]==newtest[:na] and oldtest[b:]==newtest[nb:]
v={'fixed_arguments_profile_and_cwd_builder_unchanged':True,'execution_input_budget_precedes_executable_directory_pipe_job_launch':True,'actual_stdin_writes_execution_envelope':True,'domain_test_only_embedded_fake_program_changed':True,'domain_wait_fail_unknown_cancel_cas_atomic_assertions_unchanged':True,'source_refs':['adapters/runtime/codex_driver_windows.go:47-96','adapters/runtime/codex_driver_windows.go:126-143','adapters/runtime/codex_driver_windows.go:317','internal/domain/runtime_harness_windows_test.go:32-40'],'old_snapshot_manifest_sha256':'ecc1e5574588d9de6ac450259eb363e5e2bea1fb1b7e716e3e9014c0ca287572','formal_increment':0}
p=R/'static-review.json';assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'static_boundaries':True,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
