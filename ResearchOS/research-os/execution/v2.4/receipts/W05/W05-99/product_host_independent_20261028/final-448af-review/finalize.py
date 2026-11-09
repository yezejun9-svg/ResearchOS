import json,hashlib,pathlib,subprocess,datetime,re
P=pathlib.Path;R=P('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/desktop-installed-delivery-20261025';E=P(__file__).resolve().parent;I=E.parent
A=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028'
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def js(p):return json.loads(P(p).read_bytes())
def req(v,m):
 if not v:raise RuntimeError(m)
def put(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
refs={};manifests=[(A/'BASE-5ee2-MANIFEST.json','1e37c66ffef97ea4cc6f558c9e2722593dac3bdf353557cec98e1db8d9bb8d80'),(A/'FINAL-MANIFEST.json','c0957ec54ab37b464e029c59325d3b1fe7e99c5ad6e61decd988fdb3563a8829'),(A/'marker-fixture-cp563/FINAL-MANIFEST.json','58a1d85cd0e4a07ffce07a8f7a30e791be4996814b494582f9546f703df131d3')]
def collect(x):
 if isinstance(x,dict):
  if all(k in x for k in ['path','sha256','bytes']) and P(x['path']).is_absolute():
   p=P(x['path']);key=str(p).lower();row={'path':str(p),'sha256':x['sha256'],'bytes':x['bytes']}
   req(key not in refs or refs[key]==row,'conflicting reference');refs[key]=row
  for v in x.values():collect(v)
 elif isinstance(x,list):
  for v in x:collect(v)
for p,digest in manifests:req(sha(p)==digest,'manifest hash');collect(js(p))
for row in refs.values():req(sha(row['path'])==row['sha256'] and P(row['path']).stat().st_size==row['bytes'],'ref mismatch '+row['path'])
put('AUTHOR-REFERENCE-AUDIT.json',{'status':'PASS','manifests':[{'path':str(p),'sha256':d} for p,d in manifests],'unique_references_checked':len(refs),'references':list(refs.values())})
root=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp563/product-host-final-build-root-verification.json';req(sha(root)=='8bdc5e6f5f913f6db809bc32b2e868c1f48d20d2a1419acca1e86fad3f72a559','root review hash')
# Bind the targeted status fixture to the committed production delta, without rerunning it.
b=js(A/'host-metadata-cp562/source.before.json');a=js(A/'host-metadata-cp562/source.after.json');req(b['files']==a['files'],'metadata input drift')
for r in b['files']:req(sha(W/r['path'])==r['sha256'],'metadata current bytes')
raw=(A/'host-metadata-cp562/stdout.raw').read_text(encoding='utf8');req(len(re.findall(r'^--- PASS:',raw,re.M))==3 and js(A/'host-metadata-cp562/exit.json')['exit_code']==0,'metadata3')
# Main VM4 uses frozen copied source; production main/helper unchanged through current commit.
for rel in ['apps/desktop/main/main.js','apps/desktop/main/lib/product-layout.js']:
 req(sha(I/'source-preview-02'/rel)==sha(W/rel),'VM4 frozen source drift')
req(all(r['pass'] for r in js(I/'source-preview-02/MAIN-LIFECYCLE-PROBES.json')['results']),'VM4')
focused=js(I/'focused-9361-review/RESULT.json');req(focused['source_unchanged'],'focused source drift');req({r['name']:r['exit_code'] for r in focused['commands']}=={'node':1,'python':0,'go':0},'focused historical results')
current=js(E/'BUILD04-REVIEW.json');model=js(I/'modelstream-review/REVIEW.json');req(model['status']=='INDEPENDENT_ARTIFACT_REVIEW_PASS','model artifact review')
files=[E/'BUILD04-REVIEW.json',E/'INPUTS.json',E/'DEPENDENCY-DELTA.json',E/'AUTHOR-REFERENCE-AUDIT.json',I/'modelstream-review/REVIEW.json',I/'modelstream-review/INPUTS.json',I/'focused-9361-review/RESULT.json',I/'focused-9361-review/source.before.json',I/'focused-9361-review/source.after.json',I/'focused-9361-review/node-diagnostic.result.json',I/'focused-9361-review/TEMP-CLEANUP.json',I/'focused-9361-review/TEMP-CLEANUP-DETAIL.json',I/'source-preview-02/MAIN-LIFECYCLE-PROBES.json',I/'build03-review/BUILD-REVIEW.json',I/'frozen-5ee2c694-review/SOURCE-INPUTS.json',I/'frozen-5ee2c694-review/CP562-MODELSTREAM-IMPACT.md',root,*[p for p,d in manifests]]
inputs=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
report={
 'schema':'researchos.independent-product-host-source-build-review.v1',
 'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'LIMITED_SOURCE_BUILD_FIXTURE_ACCEPTED',
 'reviewer':'codex:/root/product_host_independent_20261028',
 'source_build_accepted':True,'accepted_commit':current['head'],'accepted_tree':current['tree'],
 'accepted_build':str(W/'.local/product-layout-cp558-20261028-04'),
 'accepted_marker_sha256':current['marker_sha256'],'accepted_installation_id':current['installation_id'],
 'scope':'CP558 exact14 + CP562 metadata exact2 + CP563 test-only exact1 successor; source/build and explicitly listed pure/mock/local fixture evidence only',
 'productCore_runs':0,'productElectron_runs':0,'product_native_lifecycle_runs':0,'formal_increment':0,
 'observed_evidence':{
  'current_build04':current,
  'Node_product_host':'8/8 author PASS; before/after two input hashes and pinned Node equal; run at dirty9361, bytes equal final448af commit; independently reviewed, not rerun',
  'Go_product_host':'Independent PASS at clean9361, 8 effective top-level tests plus child helper; source/tool before-after identical; final change touches only separate Node test',
  'Python_builder':'Independent 2/2 PASS at clean9361; source/tool before-after identical; final change touches only separate Node test',
  'Main_VM':'4/4 independent VM mocks on source-preview02; captured main/helper bytes equal final448af; no Electron process',
  'Host_metadata':'3 top-level plus2 metadata subcases author PASS; production bytes before/after equal current; selected-session status now completes; original negative exit retained',
  'ModelStream':'7 top-level plus5 semantic subcases PASS on5ee; 122 artifacts and11 TLS child exits independently hashed/read; SQLite causal/durability/quarantine assertions rechecked read-only; no rerun on successors',
  'readonly_consumers':'build03 bundledNode loader and CLI version/help/commands exit0, isolated profile/data writes0; same product implementation retained, newbuild04 fullinventory/hash verified; no claim of execution onbuild04'
 },
 'resolved_findings':['F01 case-sensitive inventory ordering with casefold duplicate protection','F02 trusted STARTING with dead previous discovery','F03 interactive missing-project guidance','F04 failed startup retains usable diagnostic entry','F05 host-bound alias and interactive-leading-flag dispatch','F06 product marker absence fails closed','witness retirement failure retains retryable host','CP562 host.status metadata session field rejection','CP563 Node marker-removal fixture now verifies absence'],
 'historical_failures_preserved':['Original F01 preparation reproduction','Node boundary215 missing-env failures remain failed and non-native-qualified','Go initial ModelStream7 missing Node/Mu env failures retained; CP561 success is new bounded fixture evidence','Original W18 status INVALID_REQUEST retained; CP562 targeted fixture resolves only that branch','W18 pagination CONTINUATION_HTTP_403 remains open and not rerun','Independent Node7pass1fail at9361 and deletion timing retained; CP563 corrected fixture PASS is separate','Reviewer diagnostic whole-record timestamp comparison failure retained as reviewer error, not product failure','Two owned-temp cleanup commands rejected before execution; no cleanup after Root stop'],
 'unaccepted':['N01-N06 native product lifecycle, GUI/CLI simultaneous entry, real reopening with nonempty history, busy-close behavior','Installer packaging/registration/upgrade/rollback/uninstall and clean Windows user','C57 distinct-identity recovery, sleep/reboot/overnight','Real provider/business qualification','Full HTTP renderer wire suite and unrelated pagination failure','22 parent tasks and42 formal cases'],
 'limitations':['Frozen review matrix is a design/coverage index, not a claim every matrix row was dynamically executed. Only observed_evidence is accepted.','ModelStream is local TLS/inprocessHost-Native3/compiled devCLI:2 cases normalCLI exit,9 exceptional cases test-owned Process.Kill+wait after assertions.','Historical environment values were reconstructed; complete per-PID OS lineage not captured; postflight zero owned-process matches is a point-in-time observation.','Own temporary cache/profile directories retained because automatic policy rejected deletion with reason blocked by policy.'],
 'evidence_refs':inputs
}
put('FINAL-REVIEW.json',report)
print(json.dumps({'status':report['status'],'source_build_accepted':True,'author_unique_refs_checked':len(refs),'report_sha256':sha(E/'FINAL-REVIEW.json')}))
