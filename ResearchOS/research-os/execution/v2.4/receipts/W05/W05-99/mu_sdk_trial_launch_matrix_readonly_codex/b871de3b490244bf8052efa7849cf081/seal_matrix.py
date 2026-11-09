import ast,hashlib,json,os
from pathlib import Path
O=Path(__file__).resolve().parent
P=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef/mu_sdk_trial.v7.final.proposed.py")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
raw=P.read_bytes();ref=pin(P);assert ref["sha256"]=="d527eaf03d83208751c046d024747cb42bdc2f806474f8dda7f8ae70c2716a98" and ref["bytes"]==84032
assert raw==(O/("source-"+ref["sha256"]+".raw")).read_bytes()
tree=ast.parse(raw);matrix=json.loads((O/"matrix-draft.json").read_bytes());matrix["source_ref"]=ref
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PHASE_BASIS_KEYS" for t in n.targets):matrix["phase_basis_keys"]=list(ast.literal_eval(n.value))
matrix["source_function_locations"]={n.name:{"start":n.lineno,"end":n.end_lineno} for n in tree.body if isinstance(n,ast.FunctionDef)}
matrix["entry_argv"]=["<pinned Python>","<actual pinned source.py>","precheck-bootstrap|bootstrap|precheck-execute|execute","<absolute executable-input.json>"]
matrix["authority_input_ref_names"]=["input_basis_ref","root_registration","root_review","root_grant","owner_lease","root_checkpoint","outer_job_contract","job_probe_receipt","controller_source","controller_review"]
matrix["child_environment_allowlist"]=["SystemRoot","WINDIR","PATH","USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"]
matrix["child_environment_fixed"]={"RESEARCHOS_CLI_DISCOVERY":"input.discovery_file","RESEARCHOS_CLI_CONFIG":"input.cli_config_file"}
put("launch-matrix.json",matrix)
put("source-read-integrity.json",{"source_ref":ref,"raw_snapshot_ref":pin(O/("source-"+ref["sha256"]+".raw")),"entry_exit_raw_same":True,"candidate_imported":False,"candidate_executed":False,"sql_executed":False,"phase_basis_keys_count":len(matrix["phase_basis_keys"]),"file_matrix_count":len(matrix["file_matrix"]),"new_tool_failures":0})
print(json.dumps({"report":pin(O/"report.md"),"matrix":pin(O/"launch-matrix.json"),"source":ref,"basis_keys":len(matrix["phase_basis_keys"]),"files":len(matrix["file_matrix"]),"status":"READONLY_EXTRACTION_COMPLETE"},ensure_ascii=False))

