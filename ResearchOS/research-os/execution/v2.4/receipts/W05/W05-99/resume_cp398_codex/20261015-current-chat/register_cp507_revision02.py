import hashlib
from pathlib import Path
source_path=Path(__file__).with_name('register_cp507.py')
source=source_path.read_text(encoding='utf8')
wrong='2a43ef48c86466a5c86ea1cd76f3f53ededbf78d6291f120756cd712e7a0cf93'
correct='2a43ef48c86466a5c86ea1cd76f3f53edebdf78d6291f120756cd712e7a0cf93'
assert source.count(wrong)==1
source=source.replace(wrong,correct)
point="assert cp['failure_counters'][:1583]==old and len(cp['failure_counters'])==1589"
assert source.count(point)==1
insert="""roots=[{'ordinal':1,'tool_chunk':'969826','native_exit':1,'kind':'SOURCE_INDEX_HASH_TEXT_TRANSCRIPTION_MISMATCH','reported_sha256':'2a43ef48c86466a5c86ea1cd76f3f53ededbf78d6291f120756cd712e7a0cf93','actual_sha256':'2a43ef48c86466a5c86ea1cd76f3f53edebdf78d6291f120756cd712e7a0cf93','outcome':'Strict precondition failed before O creation or sharedstate mutation; fresh file hash matches actual index and final candidate manifest unchanged. Failed original registrar retained.'},{'ordinal':2,'tool_chunk':'870bda','native_exit':0,'kind':'POWERSHELL_MIXED_OBJECT_FORMATTING','outcome':'Mixed GetItem/GetFileHash objects hid hash columns. Recovered exact two hashes with ConvertTo-Json in chunk83a1e2; no evidence inferred from hidden output.'}]
new(O/'root-registration-diagnostics.json',{'items':roots})
for x in roots:cp['failure_counters'].append({'origin_key':'20261015|root-cp507-diagnostic-'+str(x['ordinal']),'attempts':1,'status':'REGISTRATION_OR_READ_DIAGNOSTIC_PRESERVED','detail':x,'evidence_ref':ref(O/'root-registration-diagnostics.json'),'counter_reset':False})
assert cp['failure_counters'][:1583]==old and len(cp['failure_counters'])==1591"""
source=source.replace(point,insert)
source=source.replace('failure_records_preserved=1589','failure_records_preserved=1591').replace('preservedrecords1589','preservedrecords1591').replace("'failure_records':1589","'failure_records':1591")
effective=source_path.with_name('register_cp507_revision02.effective.py')
with effective.open('x',encoding='utf8') as f:f.write(source)
print('effective_registrar_sha256='+hashlib.sha256(effective.read_bytes()).hexdigest())
exec(compile(source,str(effective),'exec'),{'__file__':str(effective),'__name__':'__main__'})
