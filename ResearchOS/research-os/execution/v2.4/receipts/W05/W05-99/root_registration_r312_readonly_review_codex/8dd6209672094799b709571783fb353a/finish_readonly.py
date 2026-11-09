import ast,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
D=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-exact1-r312'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(ROOT).as_posix(),'sha256':h(b),'bytes':len(b)}
def save(n,x):
 with (HERE/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def need(x,s):
 if not x:raise RuntimeError(s)
pins={'register.py':'0a60043f9b5e962679a2c0b8c558363cfcf12a80ddbf936bf066bafcaa2d13ef','run.py':'807d88a1b80e76fa41a277278f83047820543e330389b0899824aafb8f8432c8','prepared_refs.json':'697cf3703f454579e79bbb21aef52539acdf81613177c4d62ef45ef076911882','audit.json':'1960f875d8113f19763ba9235d9958a2f0729202cd7fe267564f0e97f5543bbe','scope_registration.json':'31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c'}
for n,v in pins.items():need(h((D/n).read_bytes())==v,'draft '+n)
p=json.loads((D/'prepared_refs.json').read_bytes())
for x in p['verified_refs']:need(ref(ROOT/x['path'])==x,'reference '+x['path'])
copies=[]
for i,x in enumerate(p['canonical_before']):
 c=HERE/f'canonical-before-{i+1}-{Path(x["path"]).name}'
 need(c.read_bytes()==(ROOT/x['path']).read_bytes(),'canonical snapshot')
 need(h(c.read_bytes())==x['sha256'] and c.stat().st_size==x['bytes'],'canonical pin')
 copies.append(ref(c))
original=(HERE/'git-08.stdout.raw').read_bytes()
candidate=(HERE/'git-06.stdout.raw').read_bytes()
body=original[255:]
need(len(original)==14888 and len(body)==14633,'body exact offset/length')
need(h(body)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1' and body in candidate,'protected body')
need(h(candidate)=='e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0','candidate')
for n in ['register.py','run.py']:
 ast.parse((D/n).read_bytes())
for n in ['register.py','run.py','prepared_refs.json','audit.json','scope_registration.json','source_before.json','failure-origins.cut.json']:
 with (HERE/('reviewed-'+n)).open('xb') as f:f.write((D/n).read_bytes())
origin={'origin_key':'r312-independent-audit-25be22-protected-body-boundary','actor':'codex:/root/w05_merge_review','actual_outer_exit':1,'actual_native_exit':None,'tool_output_id':'25be22','product_test_failures':0,'cause':'Reviewer compared original14633-byte protected body against entire14888-byte22752 file. Saved Git bytes prove suffix offset255 length14633 correct and present unchanged in candidate.','original_script_ref':ref(HERE/'audit_readonly.py'),'original_source_blob_ref':ref(HERE/'git-08.stdout.raw'),'raw_file':None,'raw_limitation':'Original exception resides in tool trace25be22; Git stdout/stderr were captured before assertion.','correction_tool':'0be860','counter_reset':False,'pending_next_Root_CAS_not_in_r312_cut':True}
save('failure_origins.json',[origin])
checks=[
 'Exact5 draft hashes and all18 prepared refs match current public bytes. Four canonical snapshots match ordered original hashes and bytes.',
 'Readonly Git queries in original audit all8 exited0: Main2cdb,13status11D,empty index,G2head9a34clean and three pinned source blobs; correction uses saved bytes only, no repeated Git or runtime execution.',
 'Both new origins unique and absent from old384, equal audit/cut/prepared records. Nativecase0 distinct from Root driver1; locator nativeNULL retained.',
 'Wrapper checks independent review/schema/decision/four script+metadata draft hashes and ordered four snapshots against current live canonical before launch; pinned Python/Git and optimize0 required.',
 'Registrar caches verified ref bytes, persists original four metadata and desired two bytes before mutation; durable intent and per-replace done/exception records; no automatic retry/recovery.',
 'Immediately before each replacement: all4 expected live bytes plus HEAD/status checked. Expected live and READS updated after each write. Postcheck preserves old384/formal/ST/commands/HEAD/status.',
 'Only one test path gets fresh Cmd worktree lease; Desktop disjoint existing scope remains intact. Exact14/max224 fixture HTTP, fresh compiler/exe/fixtures and firstUnexpectedStop; no SDK/Node/model/private/external.',
 'Original14633 body at oldfile offset255 verified; candidate contains full exact body. Domain source hash protected; Root sidecar assertion and old proof/DB/WAL/SHM remain unchanged.',
 'CLI221 is a finite union receipt update, source-ready flags remain false and formal/Main integration unchanged.'
]
save('audit.json',{'checks':checks,'verified_refs':p['verified_refs'],'canonical_before':p['canonical_before'],'original_body':{'whole_original_bytes':len(original),'whole_original_sha256':h(original),'offset':255,'bytes':len(body),'sha256':h(body),'candidate_contains_exact_body':True},'draft_import_or_execution':False,'SQL_Go_tests_models':0,'new_failure_origins_ref':ref(HERE/'failure_origins.json'),'wrapper_limitation':'If child launch raises before subprocess returns, wrapper does not produce invocation.json; Root actual outer/raw remains required. No canonical mutation occurs before launch; registrar own intent/exception journaling covers its mutations.'})
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,'expected_before':[311,139,384],'expected_after':[312,140,386],'register_sha256':pins['register.py'],'wrapper_sha256':pins['run.py'],'prepared_refs_sha256':pins['prepared_refs.json'],'audit_sha256':pins['audit.json'],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'reviewed_at':datetime.now(timezone.utc).isoformat(),'scope_ref':ref(D/'scope_registration.json'),'independent_audit_ref':ref(HERE/'audit.json'),'conditions':['Only Root executes pinned wrapper against unchanged four metadata/HEAD/status.','This is exact1 lease registration review, not author test correction source acceptance, Main integration, or formal acceptance.','Preserve independent audit25be22 failed locator-boundary check for nextCAS, outside fixed384→386 cut.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'failure_origins_ref':ref(HERE/'failure_origins.json')}
for x in p['canonical_before']:need(ref(ROOT/x['path'])==x,'final canonical unchanged')
save('review.json',review)
entries=[ref(x) for x in sorted(HERE.rglob('*')) if x.is_file()]
save('manifest.json',{'entries':entries,'count':len(entries)})
save('handoff.json',{'review_ref':ref(HERE/'review.json'),'manifest_ref':ref(HERE/'manifest.json'),'audit_ref':ref(HERE/'audit.json'),'failure_origins_ref':ref(HERE/'failure_origins.json'),'actual_registration_executed':False})
print(json.dumps({k:ref(HERE/k) for k in ['review.json','manifest.json','handoff.json','failure_origins.json']},ensure_ascii=False,indent=2))
