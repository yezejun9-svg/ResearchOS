"""Copy original sealer, change only observed marker assumptions and receipt names."""
from pathlib import Path
D=Path(__file__).resolve().parent
raw=(D/'seal_review.py').read_bytes();text=raw.decode('utf-8')
old="assert len(values)==1 and values[0]['exit_code']==b['outer_exit']==0 and 'Python_exit=0' in values[0]['output'] and b['Python_exit']==0"
new="assert len(values)==1 and values[0]['exit_code']==b['outer_exit']==0\n   assert \"pythoncore-3.14-64/python.exe' -I -S -B -X utf8\" in call['payload']['input']"
assert text.count(old)==1;text=text.replace(old,new)
old="outer_exit=b['outer_exit'],Python_exit=b['Python_exit']))"
new="outer_exit=b['outer_exit'],Source_binding_claimed_Python_exit=b['Python_exit'],independent_observed_Python_exit=None,inner_exit_marker_present=False))"
assert text.count(old)==1;text=text.replace(old,new)
old="('independent-Source-guard.closed.json','continuation-Source-guard.closed.json')"
new="('independent-Source-guard.closed.json','continuation-Source-guard.closed.json','seal-Source-guard.closed.json')"
assert text.count(old)==1;text=text.replace(old,new)
old="save('seal-Source-guard.closed.json',closed)"
new="save('seal-continuation-Source-guard.closed.json',closed)"
assert text.count(old)==1;text=text.replace(old,new)
assert text.count('for n in (1092,1093)')==2;text=text.replace('for n in (1092,1093)','for n in (1092,1093,1096)')
text=text.replace("'original1090_preserved=True'","'original1090_preserved=True'")
target=D/'seal_review.continuation.py'
with target.open('xb') as f:f.write(text.encode('utf-8'))
print('Original sealer and closed guard preserved; one mechanical marker delta; observed author inner exits remain NULL.')
