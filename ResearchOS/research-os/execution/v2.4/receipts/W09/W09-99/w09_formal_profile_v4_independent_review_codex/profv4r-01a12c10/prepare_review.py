import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
S=N.parents[1]/'w09_formal_profile_v3_independent_review_codex/profv3r2-01a12c09'
m=json.loads((S/'MF.json').read_bytes());r=next(v for v in m['members'] if Path(v['path'])==S/'review.py');raw=(S/'review.py').read_bytes()
assert hashlib.sha256(raw).hexdigest()==r['sha256'] and len(raw)==r['bytes']
text=raw.decode()
replacements=[
 ('w09_formal_profile_v3_source_codex/profv3-01a12c09','w09_formal_profile_v4_source_codex/profv4-01a12c10'),
 ("'ea70b9e94ee38403a374b7f9586ce0373ca708c48e51a841f6a6d98de5c80962',2678","'e27b1ec5b48f19f23271ea7604d0f3bec04dcfe443191af2891f49dac2ba908a',2980"),
 ("'9dfac1c2966af3aefaeb645ed0edc19d81233db346dcbd5abc1b11e9ec2128eb',9043","'e9fc7ae240d30d2ad1c6706d8e4aa783ace22623e372e2595e72e062e220792e',11007"),
 ("for ref in mf['v2_independent_review'].values():read(ref['path'],ref)","for ref in [*mf['v3_review_refs'].values(),*mf['native_mr2_refs'].values()]:read(ref['path'],ref)\nterminal_case=json.loads(read(mf['v3_review_refs']['counterexample']['path'],mf['v3_review_refs']['counterexample']))\nread(R/'execution/v2.4/formal_case_index.py',dict(mf['complete_byte_inverse'],path=str(R/'execution/v2.4/formal_case_index.py')))"),
 ("early_package=[ev('start','00'),ev('pass','01'),ev('run','02','TestW09Synthetic'),ev('pass','03','TestW09Synthetic')]","early_package=terminal_case['raw_jsonl_events']\n ck('F2_exact_counterexample_pins',mf['v3_review_refs']['counterexample']['sha256']=='42f0b4fca7852be62f87454e4a62cf69a34b32541958d1645e583f7ead9a867c' and mf['v3_review_refs']['counterexample']['bytes']==2283)"),
 ("try:pro._native_event_interval(api,enc(early_package),report,['TestW09Synthetic'],'synthetic')","try:pro._native_event_interval(api,enc(early_package),terminal_case['report'],terminal_case['selected_tests'],'synthetic')"),
 ("ck('F2_package_terminal_causal_probe_completed',True,{'package_pass_before_selected_test_run_accepted':early_accepted,'events':early_package})","ck('F2_exact_v3r2_terminal_counterexample_rejected',early_accepted is False,{'counterexample_ref':mf['v3_review_refs']['counterexample'],'accepted':early_accepted})"),
]
for old,new in replacements:
 assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new,1)
text=text.replace('w09v3_review','w09v4_review')
needle=" ck('new_CAS_API_wired',api._profile_api()._owned_inventory is api._owned_inventory and api._profile_api()._audit_range is api._audit_range)"
extra='''
 previous=guard.get_buffer(str(C/'formal_profile_w09.previous_proposal.py'))
 previous_tree=ast.parse(previous)
 old_funcs={x.name:x for x in previous_tree.body if isinstance(x,ast.FunctionDef)}
 new_funcs={x.name:x for x in pt.body if isinstance(x,ast.FunctionDef)}
 ck('v4_only_terminal_function_AST_changed',set(old_funcs)==set(new_funcs) and {k for k in old_funcs if ast.dump(old_funcs[k])!=ast.dump(new_funcs[k])}=={'_native_event_interval'})
 of,nf=old_funcs['_native_event_interval'],new_funcs['_native_event_interval']
 ol,nl=previous.splitlines(keepends=True),profile.splitlines(keepends=True)
 ck('v4_surrounding_profile_bytes_exact',b''.join(ol[:of.lineno-1]+ol[of.end_lineno:])==b''.join(nl[:nf.lineno-1]+nl[nf.end_lineno:]))
 pl=previous.decode().splitlines(keepends=True);pn=profile.decode().splitlines(keepends=True)
 ck('profile_forward_diff_exact',''.join(difflib.unified_diff(pl,pn,fromfile='formal_profile_w09.previous_proposal.py',tofile='formal_profile_w09.after.py')).encode()==(C/'formal_profile_w09.forward.diff').read_bytes())
 ck('profile_inverse_diff_exact',''.join(difflib.unified_diff(pn,pl,fromfile='formal_profile_w09.after.py',tofile='formal_profile_w09.previous_proposal.py')).encode()==(C/'formal_profile_w09.inverse.diff').read_bytes())
 ck('Main_index_full_byte_inverse_matches',guard.get_buffer(str(R/'execution/v2.4/formal_case_index.py'))==before)
 ck('Main_profile_remains_absent',not (R/'execution/v2.4/formal_profile_w09.py').exists())
'''
assert text.count(needle)==1;text=text.replace(needle,needle+extra,1)
needle=" outputs={route:{'native_started_at':report['started_at']"
pos=text.index(needle)
extra='''
 # Legal cross-package interleaving with a backwards global timestamp.
 def pe(package,action,second,test=None):
  value={'Package':package,'Action':action,'Time':'2026-10-01T00:00:'+second+'Z'}
  if test:value['Test']=test
  return value
 parallel=[pe('a','start','00'),pe('b','start','00.500000'),pe('a','run','02','TestA'),pe('b','run','01','TestB'),pe('b','pass','03','TestB'),pe('a','pass','04','TestA'),pe('a','pass','05'),pe('b','pass','06')]
 parallel_report={'started_at':'2026-10-01T00:00:00Z','ended_at':'2026-10-01T00:00:07Z'}
 parallel_result=pro._native_event_interval(api,enc(parallel),parallel_report,['TestA','TestB'],'parallel')
 ck('F2_legal_parallel_packages_with_global_clock_reversal_accept',parallel_result==('2026-10-01T00:00:00+00:00','2026-10-01T00:00:06+00:00'))
 for label,rows in (
  ('duplicate_package_pass',events+[ev('pass','04')]),
  ('conflicting_package_terminal',events+[ev('fail','04')]),
  ('duplicate_start',[events[0],copy.deepcopy(events[0]),*events[1:]]),
  ('test_output_after_pass',[*events[:3],dict(ev('output','02.500000','TestW09Synthetic'),Output='late'),events[3]]),
  ('event_after_package_pass',events+[dict(ev('output','04'),Output='late')]),
  ('unmatched_package',events+[pe('foreign','start','00'),pe('foreign','pass','03')]),
  ('cross_package_test_owner',[events[0],dict(events[1],Package='else'),*events[2:]])
 ):
  reject('F2_'+label,lambda rows=rows:pro._native_event_interval(api,enc(rows),report,['TestW09Synthetic'],'synthetic'),'GO_EVENT_TERMINAL')
'''
text=text[:pos]+extra+text[pos:]
with (N/'review.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('Independent v4 reviewer created from exact pinned v3r2 checker; no Source proposal changed.')
