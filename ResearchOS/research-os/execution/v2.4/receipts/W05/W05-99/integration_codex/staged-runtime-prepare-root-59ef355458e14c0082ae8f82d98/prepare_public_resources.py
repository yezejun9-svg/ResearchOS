SOURCE_NAMESPACE="D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_v4_codex/staged-root-69e7c3008fd968419f4d4072c3c8"
import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";S=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d";O=Path(__file__).resolve().parent
SRC=Path(SOURCE_NAMESPACE)
old=S/"actual-cli-bootstrap-v3-80c7b29a01c341a884597b7da9e17c4a";intent=json.loads((old/"bootstrap.intent.json").read_bytes())
data=Path(intent["data_root"]);workspace=Path(intent["workspace"]);witness=intent["witness_ref"]
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
assert pin(witness["path"])==witness
assert not (data/"host/trusted-qualification-state.json").exists()
cfg=json.loads((data/"cli-config.json").read_bytes());assert cfg["project_id"]=="a814e5698c6b65a8423bbe0bcd1c94f1" and cfg["workspace_ref"]=="wsref-4025b6c00d1a0adb" and cfg["session_id"]==""
profile=json.loads((SRC/"profile.template.json").read_bytes())
profile["model_config"].update(ref="modelcfg-mu-sdk-opencode-go-deepseek-v4.1-flash",provider="opencode-go",model="deepseek-v4.1-flash",endpoint="https://opencode.ai/zen/go/v1/chat/completions",route="mu-sdk-trial-model-route")
profile_ref=save("profile.public-template.actual.json",profile)
seed=json.loads((SRC/"seed.template.json").read_bytes())
node=Path("C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe");bundle=S/"actual-go-validation-v4-mu-cancel/mu-worker.frozen.mjs"
node_ref=pin(node);bundle_ref=pin(bundle)
assert node_ref["sha256"]=="5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
assert bundle_ref["sha256"]=="2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441"
seed.update(data_root=str(data),discovery_file=str(data/"discovery.json"),cli_config_file=str(data/"cli-config.json"),project_id=cfg["project_id"],draft_goal_id="",workspace_ref=cfg["workspace_ref"],workspace_dir=str(workspace),witness_sha256=witness["sha256"],witness_bytes=witness["bytes"],profile_file=profile_ref["path"],profile_sha256=profile_ref["sha256"],node_executable=node_ref["path"],node_sha256=node_ref["sha256"],bundle_file=bundle_ref["path"],bundle_sha256=bundle_ref["sha256"],read_only_vault_dir=str(R/".local/resources/opencode-go-ce065ae070f74c7f800ca8fcf3aeb098/host"),credential_ref="cred-opencode_go-api_key-1791292735825831100-02e9207a-d97edec4",provider="opencode-go")
assert Path(seed["read_only_vault_dir"]).is_dir()
seed_ref=save("seed.public.actual.json",seed)
route_ref=save("public-route.actual.json",dict(schema="researchos.mu-sdk-trial.public-route.v1",provider_id="opencode-go",model_id="deepseek-v4.1-flash",base_url="https://opencode.ai/zen/go/v1",endpoint="https://opencode.ai/zen/go/v1/chat/completions",credential_ref=seed["credential_ref"],measurement_mode="LIVE",bearer_token_present=False,qualification_model_calls=1,ordinary_model_calls=2,max_output_tokens=2730,max_cost=None,model_upper_bound=None,function_tool_names=["read"],tool_upper_bound=dict(amount="0",currency="USD")))
print(json.dumps(dict(seed_ref=seed_ref,profile_ref=profile_ref,public_route_ref=route_ref,source_namespace=str(SRC),project_id=cfg["project_id"],provider_requests=0)),flush=True)

