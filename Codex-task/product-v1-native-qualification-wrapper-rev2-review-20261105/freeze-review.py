from pathlib import Path
import json,hashlib,shutil
out=Path(__file__).resolve().parent;root=out.parent
candidate=root/'product-v1-native-qualification-producer-author-20261105-rev2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
m=read(candidate/'MANIFEST.json')
assert sha(candidate/'MANIFEST.json')=='37dcac943c5a8fe694f24d152b4a34fbaf46914d25b0a4942f2aa74a54e5d503'
def cp(src,rel):
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
cp(candidate/'MANIFEST.json','candidate/MANIFEST.json')
pins={}
for row in m['files']:
 p=candidate/'source'/row['path'];assert sha(p)==row['source_sha256']
 pins[row['path']]=sha(p);cp(p,'candidate/source/'+row['path'])
for name,field in [('changes.patch','forward_patch_sha256'),('changes.inverse.patch','inverse_patch_sha256')]:
 assert sha(candidate/name)==m[field];cp(candidate/name,'candidate/'+name)
repo=Path('D:/作品集/ResearchOS/research-os')
scope=repo/'execution/product-v1/receipts/single-harness-20261104/native-qualification-producer/scope.json'
assert sha(scope)==m['scope_sha256'];cp(scope,'contract/scope.json')
for rel,h in m['contract_sha256'].items():
 assert sha(repo/rel)==h;cp(repo/rel,'contract/'+Path(rel).name)
for name,h in m['b1_overlay_sha256'].items():assert sha(Path(m['b1_overlay_source'])/name)==h
report={
 'schema':'researchos.independent-partial-source-review.v1',
 'decision':'REQUIRES_CHANGES',
 'review_scope':'Supplementary private wrapper / preparation-failure provenance / phase lifecycle only. All eight candidate files are hash-bound; this report is not a complete probe/helper/syscall/Job/capture security review.',
 'source_head':m['base_head'],
 'selected_candidate':str(candidate),
 'candidate_manifest_sha256':sha(candidate/'MANIFEST.json'),
 'source_sha256':pins,
 'formal_increment':0,'product_increment':0,
 'pending_blockers':['Before the wrapper consumes its qualification attempt or enters ensureLaunch, reject all invalid launch inputs that B1 would reject: canonical positive int64 epoch, nonblank prompt <=65536 bytes, required callbacks and existing launch/path/time constraints. A malformed model launch must not run Native qualification first.','Inspect the revised freeze and Root-controlled Go compile/fake results. This source-only review claims no test execution.','The separate principal security review of all eight files remains necessary; its independent capture/probe/resource findings are not overridden here.'],
 'diagnostic_events':[{'origin_key':'native-qualification-wrapper:preflight-before-native','classification':'SOURCE_VALIDATION_ORDER_DEFECT','detail':'qualifiedRPC.Start checks only nonempty epoch and selected path/source/time fields before setting q.state=RUNNING and calling ensureLaunch. Prompt/callback validation and canonical-positive epoch validation occur only in later B1.Start. Thus bad epoch, blank prompt or nil callbacks can consume qualification and execute Native before their inevitable model-launch rejection. This is unnecessary preparation for malformed input, not an observed model-permission bypass.'},{'origin_key':'native-qualification-wrapper-rev2-review:patch-filename-discovery','classification':'RESOLVED_REVIEW_CAPTURE_DIAGNOSTIC','detail':'Initial evidence capture used a guessed forward.patch filename. Directory inspection identified changes.patch and changes.inverse.patch; capture was corrected and their manifest hashes verified. No product file was changed.'}],
 'required_narrow_fix':'Add a side-effect-free full wrapper launch validator in the same B3 file before q.state consumption/ensureLaunch, matching pinned B1 validation. No B1/shared DTO edits. Add negative tests invoking the wrapper with malformed launch and asserting no state consumption or qualification/delegation entry, without launching Native.',
 'verified_static_boundaries':[
  'Host-only constructor accepts fixed approved root, S source, shipped helper/hash and Host build/hash; SourceBindingHash is bound from the individual Start into private observation rather than taken from a startup descriptor or serialized qualification. No supplied provider/PASS bool/imported receipt can qualify production.',
  'qualifiedRPC owns a private qualifier and an attempt state guarded by a mutex. Once valid Start enters RUNNING, repeated Start fails rather than spawning another qualification. Ensure is fast revalidation of existing observation, not another Native invocation.',
  'Rev2 sets used=true immediately after checking observed state, before identity validation. A first Ensure mismatch consumes the observation; correcting arguments cannot retry it. The added test source explicitly checks that sequence.',
  'Ensure compares Task/Run/epoch/source hash, full RPC policy identity, rendered config hash, source/owned cwd, binary/helper/build, environment, normal home, boot and expiry; it rechecks canonical source/helper paths and binary/helper contents. It cannot by itself replace B1 same-start permission validation.',
  'The wrapper sets delegateAttempted before calling B1.Start. Any attempted delegation, including a Start error with nil delegate, blocks the preparation-failure accessor. A nil delegate is not treated as proof of no child.',
  'Delegated Wait uses context.Background after cancellation propagation, avoiding an early context error that would skip owned cleanup. Cancel forwards to an existing delegate; a cancellation during delegation is checked after delegate publication.',
  'CodexPreparationFailureForHandle recognizes only private *qualifiedHandle, requires terminal done, takes its mutex, rejects delegated state, checks launch/template/boot provenance and fixed reason list, and returns copied values. Arbitrary external handles and serialized projections cannot mint it.',
  'NoQualificationChild is initialized as an internal preflight fact and is cleared immediately before collectQualification. A zero PID after entering collection is conservatively not accepted as known no-child. When a child exists, the accessor requires nonzero qualification PID plus JobZero/drain/cleanup. Qualification PID remains a separately named field; model result Identity is not populated from it.',
  'Qualification timeout is capped at 60 seconds within the wrapper deadline; only remaining original duration is passed to B1. Cancellation/deadline failure before delegation produces separate preparation facts; it does not cause a second qualification or retry. These paths have not been executed by this review.',
  'Synthetic qualification files/cwd/receipts live under approved root; ensureLaunch avoids precreating B1 launch.Directory. Source must equal the preauthorized S path. Capability/readiness queries do not invoke qualification.'
 ],
 'coverage_limits':[
  'Current wrapper tests cover Ensure identity/single-use and private terminal accessor cases. They do not drive complete wrapper Start -> qualification -> cancel/delegate -> Wait with a fake child, or assert actual remaining-time propagation. Source reasoning is not execution evidence for those phase transitions.',
  'The helper fact projection exports qualification PID and receipt path, while full creation/Job identity remains in the captured receipt; the later domain settlement must keep that evidence distinct and must not relabel it as model identity.',
  'The main security reviewer reported separate potential compile/capture/control/resource defects. Those are not fully verified or adjudicated by this limited review and remain under the main review.',
  'No claim is made that Native permission qualification passed, that a model was invoked, or that the final B1/B2/B3 combination is approved.'
 ],
 'integrity':{'candidate_source8_verified':True,'patches_verified':True,'scope_and_contracts_verified':True,'pinned_B1_overlay8_verified':True},
 'review_execution':{'go_tests':0,'native_cli':0,'app':0,'model':0,'product_source_writes':0,'D_writes':0}
}
(out/'review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','SHA256SUMS.json'])
(out/'SHA256SUMS.json').write_text(json.dumps({rel:sha(out/rel) for rel in files},indent=2)+'\n',encoding='utf-8')
(out/'archive-file-list.json').write_text(json.dumps({'root':str(out),'files':files+['SHA256SUMS.json']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(out/'review-report.json'),'archive_sha256':sha(out/'archive-file-list.json'),'archive_files':len(files)+1},indent=2))
