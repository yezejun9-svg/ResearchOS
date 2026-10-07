import hashlib, json, pathlib, subprocess, datetime, re
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[6]
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,value): (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
runs=[]
for folder in sorted(HERE.glob('run-*')):
    if not (folder/'result.json').exists(): continue
    result=json.loads((folder/'result.json').read_text('utf8'))
    raw=(folder/'test.stdout').read_text('utf8')
    counts={key:int(re.search(r'\b'+key+r' (\d+)',raw).group(1)) for key in ('tests','pass','fail','cancelled','skipped')}
    runs.append({'directory':folder.relative_to(ROOT).as_posix(),'result':result,'counts':counts,'test_invocation':ref(folder/'test.invocation.json'),'stdout':ref(folder/'test.stdout'),'stderr':ref(folder/'test.stderr')})
candidate=[item for item in runs if item['counts']=={'tests':20,'pass':20,'fail':0,'cancelled':0,'skipped':0} and not item['result']['source_drift']]
current=sha(ROOT/'adapters/runtime/mu/worker.mjs')
candidate=[item for item in candidate if json.loads((ROOT/item['directory']/'bundle.build.json').read_text('utf8'))['source_sha256']==current]
if len(candidate)!=1: raise RuntimeError('exact final current source run required')
final=candidate[0]; vector=json.loads((ROOT/final['directory']/'source.before.json').read_text('utf8'))
if len(vector)<27000: raise RuntimeError('full installed dependency vector required')
scope_names=[
('execution/v2.4/receipts/W05/W05-99/integration_codex/model-stream-scope-930258b26ad4418b8a69ac47e2572dfa/scope_registration.json','61b1ab7d059c7f6cd0727d73eb6c647609333afe319a613d483419c2bac47f7b'),
('execution/v2.4/receipts/W05/W05-99/streaming_scope_review_codex/b6d64337-f8cc-4f9b-bbeb-97a3c7aa51c7/scope_review.json','eaeee0fe0fe0756c4339ab0c19d741d52eababde0228066bb4eaf3c762abf48b'),
('execution/v2.4/receipts/W05/W05-99/integration_codex/model-stream-owner-split-711e93105e3d491da535575a89fa5ba7/scope_amendment.json','6357d17f22b7ecd04c334d1dbd4b4d6b89fb046ead5146325acb69819880b5cf'),
('execution/v2.4/receipts/W05/W05-99/integration_codex/model-stream-wire-freeze-d6a45a6308994f4c9d84a280d08f5eb1/interface.original.json','29d52a7900ed854ba889d110002474cb7e51660c64144bcacbc52d117512141b'),
('execution/v2.4/receipts/W05/W05-99/integration_codex/model-stream-wire-freeze-d6a45a6308994f4c9d84a280d08f5eb1/registration.json','034888970cf956829f15927d80615580748fb4930462fd62b6d6607661b17d58')]
for path,expected in scope_names:
    if sha(MAIN/path)!=expected: raise RuntimeError('scope drift '+path)
save('finite_state_design.json',{
 'schema':'researchos.worker.MODEL_SSE_V1.finite-state.v1','actor':'codex:/root/command_queue_impl',
 'binding':'Exact frozen seven-key auxiliary envelope; actual init ACK barrier; host additionally requires durable DELIVERED source qualification. Ordinary effect/command sequence independent.',
 'bounds':{'active_model':1,'lifetime_model':'original configured max_calls, <=32','original_raw_bytes_per_model':2097152,'data_fragment':8192,'pending_nonterminal_data':4,'pending_observations':1,'data_descriptors_per_worker':262144,'observation_credit_descriptors_per_worker':262144,'sdk_actual_pushed_unconsumed':4096,'text_parts_per_model':64,'stdout_queued_writes':64,'stdin_line_bytes':65536,'json_depth':64,'request_deadline_seconds':90},
 'producer':'Wrapper counts every actual SDK push. Existing hook chained unchanged only after previous pushed sequence is post-yield consumed by real awaited agent listeners. No event count predicted from chunk contents. Exhaustion aborts actual SDK iterator and resolves only actual SDK failed result without queueing an extra event.',
 'raw_storage':'One preallocated 2MiB buffer + rolling SHA; descriptors retain offsets/hash, no duplicate raw copies. At most2MiB terminal withheld bytes; bounded data-record count covers tiny fragments. No public text emitted from thinking/tool events.',
 'terminal':'Terminal raw can receive transport credit while held to avoid originalACK deadlock; no SDK read/EOF until exact terminal marker plus original CONFIRMED ACK. Successful actual SDK message_end observation credit closes active stream; public END remains host final reconciliation.',
 'abort':'Observation and raw waits abort independently of command actor; original effect pending identity retained for exact late ACK. Failed stream permits original cancel/error sealing only under existing host effect/process/queue rules.',
 'canonical':'RFC8785-compatible recursive UTF16 key order/JSON.stringify; strict wire parser rejects duplicate keys/nonfinite numbers/lone surrogates; bounded raw input Transform rejects malformed UTF8 before readline replacement.',
 'measurement_mode':'FIXTURE_ONLY_NOT_LIVE_OR_FORMAL_ACCEPTANCE'})
save('failure_origins.json',{'old_history_unchanged':True,'new_origins':[
 {'id':'initial-tool-fixture-loop','raw':['test-01.stdout.txt','test-01.stderr.txt','test-01.invocation.json'],'cause':'Mixed actual Agent test returned tool calls again for every follow-up MODEL; fixture lacked a terminal second response, causing hot looping. Killed only verified owned Node child97248. Changed fixture second response to finish-only; product original max_calls unchanged.','input_capture_limit':'First pre-run harness source snapshot was not saved; original worker bundle source hash dc9f317bba249aeac6e7a26327e299346b0192849ea944b3c46edfe1da8833ef came from actual builder stdout. Later runs preserve source copies and before/after full vectors.'},
 {'id':'runner-root-depth','actual_tool_chunk':'b4f20f','exit_code':1,'cause':'parents[8] resolved worktrees parent, build.mjs missing; changed only runner to parents[7]. No product test ran.'},
 {'id':'runner-console-encoding','actual_tool_chunk':'1ff0bb','exit_code':1,'cause':'GBK console could not encode esbuild warning U+2575 after successful captured build; set runner stdout UTF8. build raw remains in run-f5f2ff5c335e4f3388ee8783aa9158c8.'},
 {'id':'huge-event-fixture-count','run':'run-d32c4dcb31404fb9a14fec4f7072f1b0','cause':'15000 repetitions produced24 fragments; >32 assertion failed. Increased genuine single-event input to25000 repetitions; no product limit changed.'},
 {'id':'stdin-transform-kept-worker-alive','run':'run-d5aec602cfe643d695f681d1720643cc','cause':'Added strict UTF8 input Transform remained piped after reader close; two real worker normal-exit tests timed out. Product fix unpipes/destroys input and pauses stdin on normal close; cancellation behavior retained.'},
 {'id':'handoff-reader-encoding','actual_tool_chunk':'4abf2a','python_exit_code':1,'shell_final_exit_code':0,'cause':'freeze.py one read_text call omitted UTF8 and decoded Chinese path through GBK, producing JSON invalid escape. Fixed exact metadata read; product source/tests unchanged.'}], 'actual_runs':runs})
save('handoff.json',{'schema':'researchos.worker.MODEL_SSE_V1.candidate-handoff.v1','status':'IMPLEMENTED_PENDING_COMBINED_SOURCE_REVIEW','actor':'codex:/root/command_queue_impl','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_commit':'32cd8f1b2b55c1a9698086a2c4f1bd26258e6c6c','source':[ref(ROOT/'adapters/runtime/mu/worker.mjs'),ref(ROOT/'adapters/runtime/mu/worker-stream.test.mjs')],'scope_refs':[{'path':p,'sha256':h} for p,h in scope_names],'wire_addendum':{'path':'execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/wire-addendum-d094f83f19574b4ca117fd3a6f26aca1/addendum.json','sha256':'8ca87295b8d9750d47be998fea2ecfabfb3ace6bb4673bf4d3d246c448e139e6','source_parent_actual_message_confirmation':True},'final_run':final,'final_input_count':len(vector),'build':json.loads((ROOT/final['directory']/'bundle.build.json').read_text('utf8')),'protected_old_queue_test_sha256':sha(ROOT/'adapters/runtime/mu/worker-control.test.mjs'),'failure_origins':ref(HERE/'failure_origins.json'),'finite_state_design':ref(HERE/'finite_state_design.json'),'limits':['No actual Go SQLite durable credit is claimed by Node harness: it is labelled FIXTURE_TRANSPORT_ONLY_NOT_SQLITE_OR_LIVE. SourceParent owns real Go/API/CLI composed tests.','No external provider request, model credential, public schema, SQL, pinned fork, build source, canonical registry or formal acceptance changed.','Old queue controls pass; remaining S6/full CLI/restore and positive final transcript provenance require SourceParent combined validation.','Builder existing ignored-bare-import warning preserved; source manifest5083 verified by actual existing builder.','Initial instrumentation failures remain disclosed; later candidates include immutable source snapshots and actual argv/cwd/env/exit/stdout/stderr.'],'formal_acceptance_delta':0})
save('manifest.json',{'schema':'researchos.worker.candidate-files.v1','self_excluded':True,'files':[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='manifest.json']})
print(json.dumps({'handoff':ref(HERE/'handoff.json'),'manifest':ref(HERE/'manifest.json'),'source':current},ensure_ascii=True))
