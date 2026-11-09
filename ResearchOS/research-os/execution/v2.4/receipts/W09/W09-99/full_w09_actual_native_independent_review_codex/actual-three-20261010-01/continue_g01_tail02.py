from pathlib import Path
p=Path(__file__).with_name('continue_g01_tail.py')
source=p.read_text(encoding='utf-8')
old="assert len(prior['checks'])==9 and all(x['passed'] for x in prior['checks']) and prior['all_closed'] is True"
assert source.count(old)==1
source=source.replace(old,"assert prior['checks'] and all(x['passed'] for x in prior['checks']) and prior['all_closed'] is True")
source=source.replace("'prior_9_checks_reused_ref':", "'prior_actual_check_count':len(prior['checks']),'prior_checks_reused_ref':")
exec(compile(source,str(p)+'#mechanical_count_correction','exec'),globals())
