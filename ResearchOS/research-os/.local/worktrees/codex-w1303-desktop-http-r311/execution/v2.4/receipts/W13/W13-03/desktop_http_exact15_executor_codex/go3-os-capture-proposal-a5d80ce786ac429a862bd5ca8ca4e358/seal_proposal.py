"""Write proposal evidence and static syntax validation only; never run proposed helper."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess

HERE=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
WT=MAIN/'.local/worktrees/codex-w1303-desktop-http-r311'
NS=WT/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex'
CURRENT=NS/'revision-r317-a7f44ed9b4ae4225bd072adcf708e24b'
AUDIT=CURRENT/'final-audit-2d44db33d4874f8bb806b44137292e08'
OLD=NS/'revision-r317-8c81bc59bc444fe2b0c5916e282f04a1/cohort-7da1948601f74dfca08b3d91b30b2191/units-91cca01a34d34a1caaa541a99d15393d'
RESOURCE=WT/'.local/desktop-wire/19e75d3970f54c2eab44fcac2f43d61d'

def ref(p):
    data=p.read_bytes()
    return {'path':p.resolve().as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def put(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    return ref(HERE/name)

for name in ('run_go3.py','windows_debug_owned_process.py'):
    ast.parse((HERE/name).read_text(encoding='utf-8'),filename=name)
descriptor=RESOURCE/'apps/desktop/resources/client-wire/descriptor.json'
d=json.loads(descriptor.read_text(encoding='utf-8'))
compiled=[ref(descriptor)]
for name in ('go_tool_ref','compile_invocation_ref','full_input_manifest_ref','compiler_generated_importcfg_archives_ref'):
    item=d[name]
    p=Path(item['path'])
    if not p.is_absolute():
        p=WT/p
    observed=ref(p)
    assert observed['sha256']==item['sha256'],(name,p)
    compiled.append(observed)
sourcepins=json.loads((AUDIT/'whole15.current.json').read_text(encoding='utf-8'))
for row in sourcepins:
    assert ref(WT/row['path'])['sha256']==row['sha256']
git=subprocess.run(['git','rev-parse','HEAD'],cwd=WT,capture_output=True)
put('git-head.actual.json',{'argv':['git','rev-parse','HEAD'],'cwd':str(WT),'actual_exit':git.returncode,'stdout':git.stdout.decode(),'stderr':git.stderr.decode()})
assert git.returncode==0 and git.stdout.decode().strip()=='06b1fbcb5934cbc70e5d65a46481e60c05c6594b'
old_stdout=OLD/'000-pure-Go-exact3/stdout.raw'
passes=re.findall(r'^\s*--- PASS: ([^ ]+)',old_stdout.read_text(encoding='utf-8'),re.MULTILINE)
assert len(passes)==64
selectors=['TestWireParserPreservesAdjacentIntegers','TestWireParserRejectsAmbiguousJSONAndWorkExhaustion','TestWirePrivatePacketExactKeysAndTypes']
exe=ref(RESOURCE/'validator.test.exe')
assert exe['sha256']=='983f41306992f162854901cc1ade5b3fc3901ca1894c15f4e1e05e92fd6d210f'
spec={
 'schema':'researchos.receipt.go3-debug-component-proposal.v1',
 'status':'PROPOSED_NOT_AUTHORIZED_NOT_EXECUTED',
 'source_commit':'06b1fbcb5934cbc70e5d65a46481e60c05c6594b',
 'source_writer':'STOPPED','product_source_mutations':0,
 'runner_ref':ref(HERE/'run_go3.py'),'helper_ref':ref(HERE/'windows_debug_owned_process.py'),
 'test_exe':exe,'cwd':WT.as_posix(),'selectors':selectors,'anchored_selector':'^('+'|'.join(selectors)+')$',
 'expected_pass_records':passes,'top_functions':3,'leaf_records':63,'pass_records_including_parent':64,
 'input_vector_ref':ref(AUDIT/'full-inputs.current.json'),'input_file_count':8577,
 'compiled_evidence_refs':compiled,
 'historical_actual_once_ref':ref(OLD/'result.json'),'historical_stdout_ref':ref(old_stdout),
 'historical_actual_os_gap_ref':ref(AUDIT/'Go-component-bridge.json'),
 'node_current_handoff_ref':ref(AUDIT/'handoff.json'),
 'caps':{'test_processes':1,'test_executions':1,'test_timeout_seconds':120,'owned_run_timeout_seconds':150,
         'termination_observation_seconds':5,'outer_timeout_seconds':600,'debug_events':4096,
         'loaded_file_events':256,'individual_module_file_bytes':268435456,'aggregate_module_file_bytes':1073741824,
         'http':0,'sdk_model':0,'external':0,'paid':0,'source_edits':0,'new_selectors':0},
 'accounting':{'prior_phase_http':302,'r317_http_including_failed_first_control':162,'combined_http':464,
               'new_component_http':0,'old_failures_and_actual_exits_retained':True},
 'procedure':[
  'Root/non-author approve this exact new helper/runner/spec and emit the exact grant. Preparing this proposal does not authorize a child.',
  'Verify grant SHA and exact runner/helper/spec/source/executable/three selectors. Rehash all 8577 current inputs, actual compiled evidence, WORK/generated/importcfg/archive references.',
  'Import only the receipt helper and pre-enumerate current Python imports/runtime DLLs; pin all observed public runtime files. Create exclusive new receipt directory and once claim.',
  'Create one unnamed kill-on-close Job and the pinned test child suspended with DEBUG_ONLY_THIS_PROCESS; assign before resume, keep CreateProcess process/thread handles. No DebugActiveProcess, OpenProcess(PID), shell, taskkill, foreign PID/Job or breakaway.',
  'Drain actual Windows CREATE_PROCESS/LOAD_DLL debug notifications throughout the short child lifetime. Hash only their actual file handles before continuing each event; retain duplicates for post-exit byte rehash. Missing/null/unreadable handles cause an incomplete result, never a guessed path list.',
  'Continue the initial debugger breakpoint only; preserve application handling for subsequent exceptions. Record actual exit notification plus independent wait/get-exit on the held original process handle and Job active count.',
  'On first unexpected event/capture error/deadline terminate only the owned Job and drain debug events for at most 5 seconds. Requested termination code and observed exit are separate; unknown remains null.',
  'After actual exit/Job idle close exact inherited stdout/stderr file handles and caller streams. These are file handles, not pipes; no invented pipe-close observation.',
  'Rehash retained actual-loaded files, all inputs and Python runtime paths; record added Python modules as incomplete. Compare actual 64 PASS records/zero FAIL/SKIP with frozen original roster; retain all raw even on failure.',
  'Write separate component outcome and manifest. This is not a repeat of Node159+7+3 and is not source/formal acceptance.'
 ],
 'mandatory_review_points':[
  'New debug-event capability differs from original r308 helper, which prohibits caller debug flags. That original remains byte-for-byte unchanged. Proposed copy adds only a fixed own-child flag.',
  'Windows x64 DEBUG_EVENT layout (176 bytes, union offset16, exception first-chance offset152), received file-handle ownership and debugger event draining must be independently reviewed before execution.',
  'Actual Windows DLL events must include the executable and each notified module until EXIT_PROCESS. Missing readable hFile or missing exit event fails the component evidence gate; no static PE-import substitution.',
  'The user-mode debugger changes process conditions/timing. This additional component observation is under debug and cannot be labelled the historical normal-mode run.',
  'Python before/after runtime inventories are point-in-time inventories of actual loaded modules; they cannot retroactively prove no transient load/unload. If the independent evidence requirement demands every Python dynamic load too, this runner is insufficient and must not launch.'
 ],
 'limitations':[
  'NOT_RUN. The proposed WinAPI/debug path has had AST syntax checks only, no native validation.',
  'Hashes identify bytes from handles of observed load files, not an attestation of relocated executable memory.',
  'Failure to obtain any module file handle is an evidence failure, not permission to omit that module.',
  'All original Go3 old actual0 and missing-OS limitation remain immutable. A future successful supplemental run does not manufacture historical facts.',
  'Node159+7+3 current outputs are frozen and are not rerun or merged into an invented new full run.',
  'Actual Host, packaged native GUI, NVDA, public provider and formal CURRENT gates remain HOLD.'
 ]}
spec_ref=put('spec.json',spec)
put('root-grant-template.NOT_AUTHORIZED.json',{'authorized':False,'issuer':None,'operation':'GO3_SINGLE_DEBUG_EVENT_COMPONENT_EVIDENCE','max_executions':1,
    'spec_ref':spec_ref,'runner_ref':spec['runner_ref'],'helper_ref':spec['helper_ref'],
    'source_commit':spec['source_commit'],'selectors':selectors,'http_cap':0,'model_cap':0,
    'notice':'This template is not Root authorization. Do not pass it to the runner.'})
put('public-inputs.before-after.json',{'before_ref':ref(AUDIT/'whole15.current.json'),
    'current':[ref(WT/row['path']) for row in sourcepins], 'drift':[], 'git_source_commit':spec['source_commit']})
put('tool-diagnostics.json',[
 {'tool_chunk':'fac826','actual_outer_exit':0,'native_exit':0,'kind':'READ_OUTPUT_TRUNCATED','meaning':'AGENTS read complete; oversized Go bridge raw output was truncated, no product failure; later bounded JSON queries used.'},
 {'tool_chunk':'a6b514','actual_outer_exit':0,'native_exit':0,'kind':'READ_ORIGINAL_RUNNER'},
 {'tool_chunk':'7ae982','actual_outer_exit':1,'native_exit':1,'kind':'RG_NO_MATCH_READONLY','argv':['rg','-n','--glob','*.py','--glob','*.h','--glob','*.go','--max-count','2','WaitForDebugEvent|LOAD_DLL_DEBUG_EVENT',str(MAIN/'.local/tools/go1.27.1/go/src'),str(MAIN/'execution/v2.4/receipts/W05/W05-99/integration_codex')],'stdout':'','stderr':'','product_executed':False,'failure_origin_count':1,'cause':'No matches in bounded public paths; not a product or test failure.'},
 {'tool_chunk':'4243c2','actual_outer_exit':0,'native_exit':0,'kind':'BOUNDED_JSON_SHAPE_READ'},
 {'tool_chunk':'8e6286','actual_outer_exit':0,'native_exit':0,'kind':'CREATE_EXCLUSIVE_RECEIPT_DIRECTORY'},
 {'tool_chunk':'ac22c1','actual_outer_exit':0,'native_exit':0,'kind':'GENERATE_PROPOSED_HELPER_AST_ONLY'},
 {'tool_chunk':'4ebc3c','actual_outer_exit':0,'native_exit':0,'kind':'READ_COMPILED_VECTOR_DESCRIPTOR'}])
handoff=put('handoff.json',{'status':'PROPOSAL_PENDING_INDEPENDENT_REVIEW_AND_ROOT_GRANT','writer':'codex:/root/sources_parent_impl',
    'source_writer':'STOPPED','spec_ref':spec_ref,'runner_ref':spec['runner_ref'],'helper_ref':spec['helper_ref'],
    'actual_test_launches':0,'source_changes':0,'new_tool_nonzero_origin':ref(HERE/'tool-diagnostics.json'),
    'current_node_handoff_ref':spec['node_current_handoff_ref'],'source_acceptance':False})
manifest=put('manifest.json',[ref(p) for p in sorted(HERE.iterdir()) if p.is_file()])
print(json.dumps({'handoff':handoff,'spec':spec_ref,'manifest':manifest},ensure_ascii=False))
