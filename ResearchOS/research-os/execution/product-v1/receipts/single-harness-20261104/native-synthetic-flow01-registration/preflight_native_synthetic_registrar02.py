import hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'product-v1-native-synthetic-flow-01-registrar-candidate-rev2/register_product_v1_native_synthetic_flow01.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='543e821950055160ee201e34fcf1be427b6c1358b6f9b0cd43f8568cd61a6d2a'
spec=importlib.util.spec_from_file_location('researchos_readonly_registrar02',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
before={str(p):p.exists() for p in [module.OUT,module.RUN_ROOT,module.AUTHORITY_SCOPE,module.AUTHORITY_RUN]}
assert not any(before.values())
module.fixed_inputs()
pins,manifest,manifest_sha,result=module.verified_build()
assert len(pins)==67 and len(manifest['files'])==135 and result['root_exit_code']==0
assert {str(p):p.exists() for p in [module.OUT,module.RUN_ROOT,module.AUTHORITY_SCOPE,module.AUTHORITY_RUN]}==before
print(json.dumps(dict(status='READONLY_FIXED_INPUTS_AND_ACTUAL_BUILD_PREFLIGHT_PASSED',source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),source_pins=67,bundle_files=135,manifest_sha256=manifest_sha,main_called=False,registration_outputs_created=False,app_helper_native_model_task_calls=0,formal_increment=0)))
