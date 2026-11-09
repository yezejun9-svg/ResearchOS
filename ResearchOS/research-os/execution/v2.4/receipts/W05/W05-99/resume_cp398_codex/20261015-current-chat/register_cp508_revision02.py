import hashlib
from pathlib import Path
p=Path(__file__).with_name('register_cp508.py');source=p.read_text(encoding='utf8')
assert source.count("Anchorcan'toverride")==1
source=source.replace("Anchorcan'toverride",'Anchor cannot override')
point="assert cp['failure_counters'][:1591]==old and len(cp['failure_counters'])==1592"
assert source.count(point)==1
insert="""roots=[{'ordinal':1,'tool_chunk':'341c14','native_exit':1,'kind':'ROOT_REGISTRAR_STRING_SYNTAX_ERROR','outcome':'Unescaped apostrophe in scope text caused syntax error before script execution; no directory or sharedstate mutation. Original source retained. Tool output budget truncated long failing line; not claimed as complete original raw.'},{'ordinal':2,'tool_chunk':'30c6f6','native_exit':1,'kind':'TOKENIZER_UNTERMINATED_LITERAL_DIAGNOSTIC','outcome':'TokenError confirmed line24 column5695; subsequent bounded regex located the exact apostrophe.'},{'ordinal':3,'tool_chunk':'932292','native_exit':0,'kind':'POWERSHELL_SUBSTRING_RANGE_DIAGNOSTIC','outcome':'Bounded excerpt request exceeded short remaining line length; regex then located exact text with no source mutation.'}]
new(O/'root-registration-diagnostics.json',{'items':roots})
for x in roots:cp['failure_counters'].append({'origin_key':'20261015|root-cp508-diagnostic-'+str(x['ordinal']),'attempts':1,'status':'REGISTRATION_OR_READ_DIAGNOSTIC_PRESERVED','detail':x,'evidence_ref':ref(O/'root-registration-diagnostics.json'),'counter_reset':False})
assert cp['failure_counters'][:1591]==old and len(cp['failure_counters'])==1595"""
source=source.replace(point,insert).replace('failure_records_preserved=1592','failure_records_preserved=1595').replace('preservedrecords1592','preservedrecords1595').replace("'failure_records':1592","'failure_records':1595")
effective=p.with_name('register_cp508_revision02.effective.py')
with effective.open('x',encoding='utf8') as f:f.write(source)
print('effective_registrar_sha256='+hashlib.sha256(effective.read_bytes()).hexdigest())
exec(compile(source,str(effective),'exec'),{'__file__':str(effective),'__name__':'__main__'})
