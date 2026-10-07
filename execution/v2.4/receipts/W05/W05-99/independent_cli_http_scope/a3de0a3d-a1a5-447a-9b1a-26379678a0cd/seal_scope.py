from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}
def load(p):return json.loads(p.read_bytes())
def save(n,v):
 with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
p=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-http-scope-proposal-ed0ec17c9f60493c819a6e75fdbcc7ba/proposal.json'
assert digest(p)=='279d34d93463312c831b9bd33616489c9b493e5115f231479bd12aa7484d2abd'
proposal=load(p);exact=['apps/cli/cli_v2.go','apps/cli/cli_http_status_test.go'];assert proposal['exact_source_paths']==exact
for item in proposal['source_before']:
 f=ROOT/item['path'];assert f.is_file()==item['expected_present']
 if f.is_file():assert digest(f)==item['sha256']
for item in proposal['protected_refs']:assert digest(ROOT/item['path'])==item['sha256']
stream=ROOT/'execution/v2.4/receipts/W05/W05-99/streaming_scope_review_codex/b6d64337-f8cc-4f9b-bbeb-97a3c7aa51c7/scope_review.json'
assert not set(load(stream)['exact_source_paths'])&set(exact)
basis=ROOT/proposal['basis_ref']['path'];assert digest(basis)==proposal['basis_ref']['sha256']
spec=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
paths=[p,basis,ROOT/load(basis)['audit_ref']['path'],stream,ROOT/exact[0],spec/'14_CLI_DESKTOP_PRODUCT.md',spec/'22_CLIENT_INTERFACE_DETAILS.md',spec/'contracts/product.contract.json',spec/'contracts/client.protocol.schema.json']+[ROOT[i['path'] for i in proposal['protected_refs']]
# Read and hash full bytes; scope does not execute tests or HTTP.
refs=[ref(f) for f in paths]
source=(ROOT/exact[0]).read_text(encoding='utf-8')
assert source.index('json.Unmarshal(raw, &reply)') < source.index('if resp.StatusCode < 200 || resp.StatusCode >= 300')
assert 'return reply, "HOST_HTTP_" + strconv.Itoa(resp.StatusCode), exitNotImplemented' in source
save('audit.json',{'schema':'researchos.w05.independent-cli-http-scope-read-audit.v1','issued_at':datetime.now(timezone.utc).isoformat(),'actual_read_refs':refs,'new_test_path_present':False,'streaming19_overlap':[],'source_lines':{'transport':221,'read_before_status':245,'parse_before_status':250,'all_non2xx_exit3':253,'strict_identity':256},'read_search_errors':[{'requested_path':'spec/v2.4/contracts/product.contract.json','result':'missing; actual frozen v2.4 root from prior bound audit used'},{'requested_path':'spec/v2.0/contracts/product.contract.json','result':'missing; no baseline substituted'},{'requested_path':'legacy diagnosis/read_audit.json','result':'missing; actual audit.json obtained from review.audit_ref'}],'tests_or_network':0,'source_registry_state_writes':0})
review={'schema':'researchos.w05.independent-cli-http-scope-review.v1','reviewer_id':'codex:/root/w05_merge_review','issued_at':datetime.now(timezone.utc).isoformat(),'decision':'SOURCE_SCOPE_READY','proposal_ref':ref(p),'basis_ref':ref(basis),'audit_ref':ref(OUT/'audit.json'),'exact_source_paths':exact,'source_before':proposal['source_before'],'protected_refs':proposal['protected_refs'],'scope_only':True,'finding':'Actual generic transport reads/parses body before status and maps parsed HTTP5xx to3. The frozen CLI spec line93 maps execution/check failure to1 and authorization/resource blockage to3. This is a current product classification gap independently observed in preserved legacy raw, not a reason to weaken old assertions.','minimal_change_bounds':{'production':'Only v2CallTransport non2xx classification, immediately after receiving headers and deferring response-body Close, before JSON parsing or unbounded error-body reading. 500..599 -> nil reply/HOST_HTTP_n/exitFailed1;401/403 ->nil reply/HOST_HTTP_n/exitNotImplemented3; remaining non2xx retain HTTP rejection3. Do not decode/echo untrusted error body or adopt any context from it.','preserve':'Preserve successful2xx limit1MiB/read errors/JSON parsing/strictIdentity parameter behavior/command+method+session/protocol checks, status semantics/adoption, request envelope and logging, context timeout8s, Bearer handling and no redirects. No retries, provider/config/session/cancellation changes.','tests':'One new cli_http_status_test.go only; use real local HTTP servers and actual transport both strict and generic where relevant. No old harness or exit-assertion edits.','coordination':'Neither path overlaps current streaming19. Root isolated implementation; independent source review before integration. Combined streaming tests use final composed CLI bytes. L02 and L04 stay deferred.'},'required_checks':['Actual500/503 JSON/nonJSON/secret/oversized error bodies ->1 with nil reply and sanitized reason; actual401/403 all body forms ->3; other representative non2xx retain3.','Malformed and oversized200 remain1, valid200/current identity checks unchanged; HTTP errors cannot mutate project/session/revision/epoch or pretend completed.','302/307 remain rejected without contacting redirect destination or forwarding Bearer.','Run focused meaningful transport tests then current CLI regression appropriate to source change; preserve full143 prior baseline and all original29 contract failures/raw without relabeling. Freeze actual source/dependency/tool/raw vectors; independent source review required.'],'implementation_or_product_acceptance':False,'missing':[],'failed':[],'formal_acceptance_delta':0,'source_registry_canonical_changes':0}
save('scope_review.json',review)
print(json.dumps({'review':ref(OUT/'scope_review.json'),'audit':ref(OUT/'audit.json')},ensure_ascii=False))
