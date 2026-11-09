from pathlib import Path
import hashlib
import json

B=Path(__file__).parent
original=B/'verify_B_r2_frozen_inputs.py'
source=original.read_text(encoding='utf8')
old="    assert result['argv']==row['argv'] and result['cwd']==row['cwd'],row['tag']"
new="""    command_path=E/(row['tag']+'.command.json')
    command=read(command_path)
    assert command['argv']==row['argv'] and command['cwd']==row['cwd'],row['tag']
    recipe_path=E/command['recipe']
    assert ref(recipe_path)['sha256']==command['recipe_sha256'],row['tag']
    assert result['stdout_sha256']==row['stdout_sha256'] and result['stderr_sha256']==row['stderr_sha256'],row['tag']
    refs[str(command_path)]=ref(command_path)
    refs[str(recipe_path)]=ref(recipe_path)"""
assert source.count(old)==1
source=source.replace(old,new).replace("O=B/'continuation-cp521-inputs'","O=B/'continuation-cp521-inputs-retry02'")
expanded=B/'verify_B_r2_frozen_inputs_retry02.expanded.py'
with expanded.open('x',encoding='utf8') as f: f.write(source)
recipe=B/'verify_B_r2_frozen_inputs_retry02.derivation.json'
with recipe.open('x',encoding='utf8') as f:
    json.dump({'original_script':str(original),'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'replacement_old':old,'replacement_new':new,'output_directory_changed_to':'continuation-cp521-inputs-retry02','expanded_script_sha256':hashlib.sha256(expanded.read_bytes()).hexdigest()},f,ensure_ascii=False,indent=2)
exec(compile(source,str(expanded),'exec'))
