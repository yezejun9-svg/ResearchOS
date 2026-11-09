import ast,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
C=json.loads((N/'source.integration.choice.json').read_bytes())
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,b):
 b=b if isinstance(b,bytes) else b.encode('utf-8')
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
 return pin(p)
def js(n,v):return put(n,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
all_inputs=C['original_input_refs']
for ref in all_inputs:
 actual=pin(ref['path']);assert (actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes'])
copies={}
for relative,ref in C['sources'].items():
 raw=Path(ref['path']).read_bytes();copied=put('reviewed-six-source/'+relative,raw)
 assert (copied['sha256'],copied['bytes'])==(ref['sha256'],ref['bytes']);copies[relative]=copied
for name in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py','source_controls.py','construct_source.py'):
 ast.parse((N/name).read_bytes(),filename=name)
controls=json.loads((N/'source-controls.result.final.json').read_bytes());assert controls['check_count']==53 and controls['status']=='PASS_SOURCE_ONLY'
delta=json.loads((N/'caller-exact-reversible-delta.final.json').read_bytes())
for item in delta:
 assert pin(item['candidate_ref']['path'])==item['candidate_ref']
 assert ''.join(line for op in item['opcodes'] for line in op['old_lines']).encode()==Path(item['original_ref']['path']).read_bytes()
 assert ''.join(line for op in item['opcodes'] for line in op['new_lines']).encode()==Path(item['candidate_ref']['path']).read_bytes()
assert all(not Path(p).exists() for p in C['fixed_paths'].values())
cfg=pin(N/'source.integration.choice.json');prep=pin(N/'prepare_w09_c19.actual_owned.py');run=pin(N/'run_w09_c19.actual_owned.py')
python='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
cp=C['checkpoint_ref']
commands=dict(preparation_argv=[python,'-I','-S','-B','-X','utf8',prep['path'],cp['sha256'],str(cp['bytes']),'364'],producer_caller_argv_template=[python,'-I','-S','-B','-X','utf8',run['path'],cfg['sha256'],str(cfg['bytes']),cp['sha256'],str(cp['bytes']),'364','PIN_FROM_NEW_ISOLATION_READY_SHA256','PIN_FROM_NEW_ISOLATION_READY_BYTES'],cwd=str(R),required_current_checkpoint=cp,required_revision=364,fixed_paths=C['fixed_paths'],run_once=True,automatic_retry=False,execution_grant=False)
js('root-calling-contract.json',commands)
put('calling-contract.md','''# W09 C19 source caller

Source preparation only. Root must independently review/adopt these exact caller and choice pins, then register the narrow current scope before actual execution. This package grants no run.

The JSON calling contract contains the exact locked Python and seven producer-caller parameters; the last two must come from the new preparation isolation.ready.json, never an old run. Both callers check current CP364 SHA256/bytes/revision. If canonical state moves, stop for new Source registration; do not update these sealed files in place.

Preparation runs six bounded owned Git observations/worktree steps, with a fixed new sparse detached worktree and fixed isolated environment. It may create the new W09-99/integration_codex parent for its fixed output only. Main Git config/index are not changed; candidate metadata gets sparse patterns. Existing tracked-dirty cardinality and empty staging are verified exactly as the adopted base caller.

Producer caller copies exactly the six reviewed v6 files byte for byte. No gofmt. It then runs one owned Go list -test -deps -compiled -json inventory, retains actual compiler/product/embed/tool inputs using SourceReadGuard, and invokes locked Python retrieval.py once, with task W09 / empty check / case C19 / fixture. The sole Go test command is formed inside that unchanged producer. Its order is ChainInvalidation then ExplicitOriginAndUnknown. The Python process, its PATH Git observations and Go child inherit one exclusive kill-on-close Job. GOTOOLCHAIN local, GOPROXY off, GOSUMDB off, GOWORK off, CGO off; no model/provider call.

The output base must not preexist. Archive selection is the sole newly-created run child plus agreement with emitted report_reference/tool_run_reference, never latest. Exact report, tool-run, raw stdout/stderr and owned exports are copied into the official receipt with original-to-archive pins before any producer success assertion. Original absolute paths and relative refs remain unchanged; retain the isolated worktree for the independent review and both formal consumers. If a launch/timeout prevents report emission, raw caller streams and any archived partial producer directory remain failure evidence; no retry.

Root must examine validation.closed.json AND every source-guard cleanup receipt plus owned Job evidence. Native producer closure is not C19 acceptance. Both formal consumers remain NOT_RUN_REGISTRY_UNBOUND. After independent review of this actual run, two route-specific FIXTURE decisions must name the same immutable native report/tool-run. Root/W02 serially appends exact C19 routes while preserving existing branches, then runs both read-only consumers; they must not call the producer again. Do not preforge post-run review or mode decisions.

The 53 Source controls use synthetic in-memory report objects only to verify routing/argv ordering. They are not native evidence or formal consumer runs. Initial construction/52-control outputs are superseded by final caller pins, final reversible delta, and the 53-control result. Mechanical 921 is the prior wrong-parent Get-Content shell failure: command_exit_code=1, native/Python/functions numeric exit=NULL; its original return and correction are retained.
''')
js('source-summary.json',dict(status='SOURCE_READY_FOR_INDEPENDENT_REVIEW',sources=C['sources'],exact_source_copies=copies,prepare_caller_ref=prep,producer_caller_ref=run,choice_ref=cfg,controls_ref=pin(N/'source-controls.result.final.json'),delta_ref=pin(N/'caller-exact-reversible-delta.final.json'),original_inputs_unchanged=True,original_input_refs=all_inputs,caller_construction_stages=['initial_source_construction','exception_and_partial_archive_source_refinement','missing_new_receipt_parent_source_fix','53_final_source_controls'],producer_order_note='Prior alleged mismatch corrected: router verifies sorted roster and passes source selected_tests to closure; both consumers therefore use producer order. Six v6 sources unchanged.',actual_git_go_producer_consumers_executed=False,current_checkpoint=cp,mechanical_921_original_io=pin(N/'mechanical-921.original-tool-io.json'),root_canonical_adopted=False,formal_acceptance=False))
put('REPORT.md','''# W09 C19 Source handoff

Six reviewed v6 files are byte-identical and a fixed sparse preparation/one-producer caller is ready for independent Source review. 53 Source-only controls pass. The two C19 consumers receive producer selected_tests in its original order and reconstruct the same exact argv; the earlier order concern was corrected without changing any v6 file.

The actual sequence is six owned Git preparation jobs, one owned compiler-input inventory, then one owned locked-Python producer job whose Go child runs only the two C19 tests. Native IDs remain C19-01..05; formal IDs remain C19-01..03. Native report and all raw/owned files are preserved under an official receipt with exact original/archive hashes. Full actual compiler closure is gathered and held by the future caller; this Source preparation does not claim it has been observed.

Current CP364 is frozen at the exact hash/size in root-calling-contract.json. No actual preparation, Git, Go, producer, service/SQLite test, formal consumer, command registry update, Main mutation, model request or acceptance occurred. Independent Source review, Root narrow scope registration, one actual run, independent actual review, route-specific decisions, two formal read-only consumers, and independent C19 acceptance remain required in that order.

Main and all 16 construction input files remain byte-identical. Mechanical failure 921 (Get-Content against the nonexistent parent AGENTS.md) is retained with shell exit 1 and null actual Python/native/functions numeric exits. No original failure was relabeled as PASS.
''')
for ref in all_inputs:
 actual=pin(ref['path']);assert (actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes'])
js('final-source-input-guard.json',dict(status='ALL_ORIGINAL_INPUT_PINS_UNCHANGED',refs=[pin(ref['path']) for ref in all_inputs],actual_execution=False))
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
mf=js('manifest.json',dict(schema='researchos.source-packet-manifest.v1',members=members,member_count=len(members),handoff_separate_root_pin=True))
hd=js('handoff.json',dict(schema='researchos.w09-c19-caller-source-handoff.v1',status='SOURCE_READY_FOR_INDEPENDENT_REVIEW',manifest_ref=mf,summary_ref=pin(N/'source-summary.json'),report_ref=pin(N/'REPORT.md'),calling_contract_ref=pin(N/'root-calling-contract.json'),prepare_caller_ref=prep,producer_caller_ref=run,choice_ref=cfg,source_controls_ref=pin(N/'source-controls.result.final.json'),reviewed_source_count=6,source_control_count=53,checkpoint_ref=cp,checkpoint_revision=364,execution_grant=False,main_canonical_changed=False,actual_native_executed=False,formal_consumer_registry='UNBOUND',formal_acceptance=False))
assert len(json.loads(Path(mf['path']).read_bytes())['members'])==len(members)
for ref in members:assert pin(ref['path'])==ref
print(json.dumps(dict(handoff_ref=hd,manifest_ref=mf,prepare_ref=prep,producer_ref=run,choice_ref=cfg,members=len(members),source_only=True),ensure_ascii=False))
