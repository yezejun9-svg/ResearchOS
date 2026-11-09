import ast,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');Q=Path(__file__).resolve().parent
data=json.loads((Q/'actual-contract-excerpts.json').read_text(encoding='utf-8'))
for family,names in [('profile',{'_role_registry','_dispatches','_vector'}),('bridge',{'consume','roles'})]:
    for item in data[family]:
        if item.get('function')in names:print(family+' '+str(item['line'])+'\n'+item['source'])
bridge=(R/'execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-06/w09_root_bridge.source.py').read_text(encoding='utf-8')
for node in ast.parse(bridge).body:
    if isinstance(node,ast.FunctionDef)and node.name=='engine':print(ast.get_source_segment(bridge,node))
print('ROOT_PYTHON_EXIT=0')
