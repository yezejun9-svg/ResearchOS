from pathlib import Path
import hashlib,json,subprocess
old=Path(__file__).with_name('materialize_cli_prompt_closure.py')
source=old.read_text(encoding='utf-8')
source=source.replace("result=git('sparse-checkout','add','--no-cone',", "assert git('config','--get','core.sparseCheckoutCone').decode().strip()=='false'\nresult=git('sparse-checkout','add',")
source=source.replace("record={'action':", "record={'prior_root_tool_failure':{'tool_chunk':'6d4fc6','python_exit':1,'git_exit':129,'cause':'sparse-checkout add does not accept --no-cone; argument parsing failed before applying patterns','first_script_sha256':hashlib.sha256(Path(__file__).with_name('materialize_cli_prompt_closure.py').read_bytes()).hexdigest(),'counter_reset':False},'action':")
compile(source,'materialize_cli_prompt_closure_r2.generated','exec')
exec(compile(source,'materialize_cli_prompt_closure_r2.generated','exec'))
