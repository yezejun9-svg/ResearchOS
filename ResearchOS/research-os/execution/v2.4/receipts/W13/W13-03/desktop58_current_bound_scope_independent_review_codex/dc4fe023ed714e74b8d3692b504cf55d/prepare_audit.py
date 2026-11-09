from pathlib import Path
O=Path(__file__).parent
P=O.parent/'72ff32d0d24a42c4a8effd849d54f882'
s=(P/'audit.py').read_text(encoding='utf-8')
s=s.replace('desktop58-finite169-go3-r335-', 'desktop58-finite169-go3-r336-').replace('230f84674dfdce85f8e29b3a70bab8c8d0b5045ace1c6119c97c7474fa8a6e90','86d77dd84af6557c4f956d8c39e0aba3d2858de526bb6c1ff8aeb178c85469bc')
s=s.replace('q[\'before\']==[334,162,532]','q[\'before\']==[335,163,580]').replace('q[\'after\']==[335,163,580]','q[\'after\']==[336,164,603]')
s=s.replace("len(cut['origins'])==48","len(cut['origins'])==23").replace("'all48 unique',len(newsha)==48","'all23 unique',len(newsha)==23")
s=s.replace("ck('future lease not replacing active',prior is None or prior.get('state') not in ['REGISTERED_PENDING_ONCE_EXECUTION','RUNNING'])", "closed=doc(R/'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_independent_review_codex/4bcd6b1bf2f941efa63f31e7a6cc7e67/review.final.json');ck('prior lease closed by actual failed evidence; stale metadata pending is preserved',prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and closed['scope_uid']==prior['run_uuid'] and closed['decision']=='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' and closed['qualification'] is False)")
s=s.replace("len(resource['files'])==23867 and len(runtime['files'])==1296", "len(resource['files'])==23868 and len(runtime['files'])==1297")
s=s.replace("base+corr+q['metadata_code_refs']", "base+corr+[q['wldp_static_ref']]+q['metadata_code_refs']").replace("'runtime exact1242+40+8+6'", "'runtime exact1242+40+Wldp1+8+6'")
with (O/'audit.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
s=(P/'supplement.py').read_text(encoding='utf-8').replace('desktop58-finite169-go3-r335-','desktop58-finite169-go3-r336-')
s=s.replace("tool-observations.fourth-capture-binding.closed.original.json", "tool-observations.fifth-construction.closed.original.json").replace("obs['run_uuid']==O.name", "obs['scope_ref']['sha256']=='86d77dd84af6557c4f956d8c39e0aba3d2858de526bb6c1ff8aeb178c85469bc'")
with (O/'supplement.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
s=(P/'final_checks.py').read_text(encoding='utf-8').replace('desktop58-finite169-go3-r335-','desktop58-finite169-go3-r336-')
with (O/'final_checks.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('Created own pure-I/O audit programs; no target imported/executed.')
