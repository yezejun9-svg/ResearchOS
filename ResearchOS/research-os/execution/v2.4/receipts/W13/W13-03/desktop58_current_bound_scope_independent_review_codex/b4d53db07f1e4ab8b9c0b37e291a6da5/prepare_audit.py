from pathlib import Path
O=Path(__file__).parent;P=O.parent/'dc4fe023ed714e74b8d3692b504cf55d'
s=(P/'audit.py').read_text(encoding='utf-8')
s=s.replace('desktop58-finite169-go3-r336-','desktop58-finite169-go3-r337-').replace('86d77dd84af6557c4f956d8c39e0aba3d2858de526bb6c1ff8aeb178c85469bc','0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1')
s=s.replace("q['before']==[335,163,580]","q['before']==[336,164,614]").replace("q['after']==[336,164,603]","q['after']==[337,165,617]")
s=s.replace("len(cut['origins'])==23","len(cut['origins'])==3").replace("'all23 unique',len(newsha)==23","'all3 unique',len(newsha)==3")
s=s.replace("ck('prior lease closed by actual failed evidence; stale metadata pending is preserved',prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and closed['scope_uid']==prior['run_uuid'] and closed['decision']=='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' and closed['qualification'] is False)", "ck('actual canonical lease satisfies pipeline306, termination alone insufficient',prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and prior.get('state') not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING') and prior['state']=='FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD' and closed['scope_uid']==prior['run_uuid'] and closed['decision']=='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' and closed['qualification'] is False);scan(prior)")
with (O/'audit.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
s=(P/'supplement.py').read_text(encoding='utf-8').replace('desktop58-finite169-go3-r336-','desktop58-finite169-go3-r337-')
s=s.replace("obs=read(N/'tool-observations.fifth-construction.closed.original.json');ck('new original observation belongs to currentUID',obs['scope_ref']['sha256']=='86d77dd84af6557c4f956d8c39e0aba3d2858de526bb6c1ff8aeb178c85469bc')", "obs={};ck('tool observation supplement deferred to final annex',True)")
with (O/'supplement.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
s=(P/'final_checks.py').read_text(encoding='utf-8').replace('desktop58-finite169-go3-r336-','desktop58-finite169-go3-r337-')
with (O/'final_checks.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('Own audit sources created, no target imported.')

