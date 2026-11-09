from pathlib import Path
import ast,hashlib,json
O=Path(__file__).parent
old=O.parent.parent/'root_registration_r328_readonly_review_codex/f2c069b671aa486a9d12c6a9312f77df/audit.py'
s=old.read_text(encoding='utf-8')
changes=[
('cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec','cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4'),
('065c781ac7631c53c314b5e98538a7762f70135c63b5b80eb6e17b2fdfccbc53','1324e4a7d39dd9159d3786db8909e1385a64b9e0ae7f91db170294fc4864d631'),
('9273795bff52a46ba6a95cc75d5742766006dc0fb19f3cb011b9047622569d7c','eadf1441e39953749d9cf36780eaf75ce8a2bec45815a0543328c90d9aa9c2b6'),
('0c5b18a9c2e5eaf65ae7e073b7d5f08e44e3d371667a50a9341af014bf58b884','efcef49a86c812b42cd4dee045184c62c8a66bebcb7e427cddb187149f579eb5'),
('p[\'expected_before\']==b[\'before\']==[327,155,459] and p[\'expected_after\']==b[\'after\']==[328,156,469]',"p['expected_before']==b['before']==[328,156,469] and p['expected_after']==b['after']==[329,157,481]"),
("'complete459 prefix plus exact10',p['origins']==cut['origins'] and len(p['origins'])==10","'complete469 prefix plus exact12',p['origins']==cut['origins'] and len(p['origins'])==12"),
("'ZIP all raw wrappers '+str(i),container==x['original_container_payload'] and container['origins'][x['original_origin_index']]==x['original_origin_row'] and x['original_origin_row']['actual_native_exit'] is None","'mapped full original container and row '+str(i),container==x['original_container_payload'] and container['new_origins'][x['original_origin_index']]==x['original_origin_row']==x['original_payload']"),
("stdout.split(b'\\0')","stdout.splitlines()")]
applied=[]
for before,after in changes:
 count=s.count(before)
 if not count:raise RuntimeError('Own auditor derivation anchor missing: '+before)
 s=s.replace(before,after);applied.append({'before':before,'after':after,'occurrences':count})
ast.parse(s)
with (O/'audit.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
raw=old.read_bytes()
with (O/'audit-derivation.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'original_auditor_ref':{'path':old.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'changes':applied,'target_executed':False},f,indent=2,ensure_ascii=False);f.write('\n')
print('Own read-only auditor derived; candidate not imported or executed.')
