from pathlib import Path
import json
d=Path(__file__).resolve().parent
s=json.loads((d/'resource-survey.json').read_bytes())
choice=s['choice']
inventories={k:{'ref':v['inventory_ref'],'scalars':v['inventory_shape']['scalars'],'fields':{field:{'length':entry.get('length'),'first_two':entry.get('first_two')} for field,entry in v['inventory_field_shapes'].items() if entry.get('type')=='list'}} for k,v in s['actual_closed_resources'].items()}
blueprint={field:({'length':entry.get('length'),'first_two':entry.get('first_two')} if entry.get('type')=='list' else entry) for field,entry in s['blueprint_field_shapes'].items()}
print(json.dumps({'common':choice['common'],'selectors':choice['selectors'],'blueprint':blueprint,'inventories':inventories,'Main_adoption':s['Main_adoption']},ensure_ascii=False),flush=True)
