import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
Q=Path(__file__).parent
data=json.loads((Q/'actual-inspection.json').read_text(encoding='utf-8'))
for row in data['parents']:
 print(row['parent'], 'reporter_exit=',row['child-result.json']['actual_runner_exit'],'verdict=',row['child-event-verdict.json']['error'])
 for event in row['events']:
  e=event['event']
  if 'typed command session.attach:' in e.get('Output',''):
   response=json.loads(e['Output'].split('typed command session.attach:',1)[1].strip())
   print('  leaf=',e['Test'],'line=',event['line'],'status=',response['status'],'revision=',response['revision'],'operation=',response['result']['operation_id'])
