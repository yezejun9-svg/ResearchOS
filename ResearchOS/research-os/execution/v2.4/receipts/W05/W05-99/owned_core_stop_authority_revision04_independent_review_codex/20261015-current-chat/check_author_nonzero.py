import pathlib,json,hashlib
E=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_source_codex/20261015-current-chat'
ledger=json.loads((A/'candidate-ab308912-final2/failure-ledger.json').read_text(encoding='utf-8'))
rows=[]
for item in ledger['failures']:
 p=pathlib.Path(item['directory']);err=(p/'stderr.bin').read_bytes();out=(p/'stdout.bin').read_bytes()
 print(p.name,'EXIT',item['native_exit'],'AUTHOR',item['classification'],'STDERR',err.decode('utf-8',errors='replace')[:1000],'STDOUT',out.decode('utf-8',errors='replace')[-600:])
 expected=item['classification']=='EXPECTED_NEGATIVE_CLI'
 verified=expected and b'STOP_GRANT_ACTION_DENIED' in err
 rows.append({**item,'reviewer_classification':'EXPECTED_CROSS_PHASE_DENIAL' if verified else 'RETAINED_AUTHOR_DIAGNOSTIC','stderr_sha256':hashlib.sha256(err).hexdigest(),'stdout_sha256':hashlib.sha256(out).hexdigest(),'expected_denial_verified':verified})
assert sum(x['expected_denial_verified'] for x in rows)==4
(E/'author-nonzero-review.json').write_text(json.dumps({'command_nonzeros':20,'reviewer_confirmed_expected_cross_phase':4,'retained_diagnostic_commands':16,'root_existing_mixed_record_total':22,'scope_capture_deviations':'Initial adjacent receipt root and early unapproved C root retained separately by Root; not counted again here. Author later allowed C data/operation exists but amendment wording is ambiguous; this reviewer kept all SQLite data and operation output on own D TMP.','records':rows},ensure_ascii=False,indent=2),encoding='utf-8')
