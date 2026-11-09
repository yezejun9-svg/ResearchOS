import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";C=B/"mu_sdk_root_coordinator_source_v5_codex/14882883e85f4e849eb087a01800e22d";O=Path(__file__).resolve().parent;ST=B/"integration_codex/staged-runtime-prepare-root-59ef355458e14c0082ae8f82d98"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
doc=json.loads((C/"input.model-trial.template.json").read_bytes())
mapping={"bootstrap_result_ref":ST/"bootstrap.result.json","bootstrap_lifecycle_ref":ST/"bootstrap.lifecycle.actual.json","bootstrap_guard_cleanup_ref":ST/"bootstrap.source-guard.cleanup.actual.json","host_seed_ref":ST/"seed.public.actual.json","intake_review_ref":B/"provider_resource_intake_review_codex/948c0201-2b62-42e7-a1b0-b12a6acfa473/review.json","public_route_manifest_ref":ST/"public-route.actual.json","parent_checkpoint_ref":R/"execution/v2.4/checkpoint.json","parent_ownership_ref":R/"execution/v2.4/path_ownership.json","runtime_prepare_receipt_ref":ST/"runtime.prepare.actual.json","prepare_receipt_ref":ST/"prepare.finalized.actual.json","runtime_prepare_invocation_ref":ST/"runtime-prepare.invocation.json","finalize_prepare_invocation_ref":ST/"finalize-prepare.invocation.json","runtime_prepare_closure_ref":ST/"runtime-prepare.closure.actual.json","finalize_prepare_closure_ref":ST/"finalize-prepare.closure.actual.json","normal_host_closure_ref":ST/"normal-host.closure.actual.json","cli_goal_closure_ref":ST/"cli-goal.closure.actual.json"}
for key,path in mapping.items():doc[key]=pin(path)
assert json.loads(mapping["parent_checkpoint_ref"].read_bytes())["revision"]==348
assert doc["parent_checkpoint_ref"]["sha256"]=="5991855edd56cea2042cbb0231226e46ce574adbb54d783507d7573036a69f6d"
doc["output_dir"]=str(O/"trial-output")
assert not Path(doc["output_dir"]).exists()
basis={k:v for k,v in doc.items() if k!="root_execution_authority_ref"}
authority=json.loads((C/"root-execution-authority.template.json").read_bytes())
authority.update(approved=True,input_basis_sha256=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest())
authority_ref=save("root.execution-authority.actual.json",authority);doc["root_execution_authority_ref"]=authority_ref
input_ref=save("input.model-trial.actual.json",doc)
review_ref=pin(B/"mu_sdk_root_coordinator_v5_independent_review_codex/88b5d07928484b6cb968a6dad2fa4cc4/review.json")
assert review_ref["sha256"]=="2df3adbc8dde38832b29fd5883f9a8a42e0c338653b4689fcf834b7fd354347f"
launch=save("launch.refs.actual.json",dict(input_ref=input_ref,review_ref=review_ref,coordinator_source_ref=doc["coordinator_source_ref"],pre_trial_provider_requests=0,qualification_admitted=False,root_user_authorization="Active user /goal plus provided opencode-go credential and preferred DeepSeek; bounded3 requests/8192 output tokens/300s/noautomaticretry"))
print(json.dumps(dict(launch_ref=launch,input_ref=input_ref,review_ref=review_ref,output_dir=doc["output_dir"],provider_requests=0)),flush=True)

