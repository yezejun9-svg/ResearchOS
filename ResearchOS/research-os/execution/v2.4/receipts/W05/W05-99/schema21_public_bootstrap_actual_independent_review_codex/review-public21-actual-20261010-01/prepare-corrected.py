from pathlib import Path
p=Path(__file__).parent
s=(p/'audit.py').read_text(encoding='utf-8')
s=s.replace("for r in ctx['current_canonical_refs']:read(r)","""for i,r in enumerate(ctx['current_canonical_refs']):
 archive=Path(ctx['registration_result_ref']['path']).parent/(str(i)+'.after.proposed.json') if i<2 else Path(reg['full_before_archive_refs'][i]['path'])
 archived=dict(r,path=str(archive));read(archived)
 details.setdefault('execution_current4_archive_refs',[]).append(archived)
transaction=Path(reg['transaction']['transaction_journal'])
doc(ref(transaction/'committed.json'));doc(ref(transaction/'intent.json'))""")
(p/'audit.corrected.py').write_text(s,encoding='utf-8')

