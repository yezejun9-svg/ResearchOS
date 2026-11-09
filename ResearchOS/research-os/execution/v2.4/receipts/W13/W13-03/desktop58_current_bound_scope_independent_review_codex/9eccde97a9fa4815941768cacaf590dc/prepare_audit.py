from pathlib import Path
import json,hashlib
O=Path(__file__).parent
P=O.parent/"b4d53db07f1e4ab8b9c0b37e291a6da5"/"audit.py"
s=P.read_text(encoding="utf8")
s=s.replace("import ast,copy,hashlib,json,os,time,traceback","import ast,copy,hashlib,json,os,time,traceback,sys")
s=s.replace("desktop58-finite169-go3-r337-","desktop58-finite169-go3-r339-")
s=s.replace("ref(N/'scope_registration.json')['sha256']=='0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1'","ref(N/'scope_registration.json')['sha256']==sys.argv[1]")
s=s.replace("[336,164,614]","[338,166,635]").replace("[337,165,617]","[339,167,645]")
s=s.replace("len(cut['origins'])==3","len(cut['origins'])==10").replace("'fixed cut transition21'","'fixed cut transition10'").replace("'all3 unique',len(newsha)==3","'all10 unique',len(newsha)==10")
old=''' prior=ow['card_path_bindings']['W13-03']['subtasks'].get('desktop58_finite_validation');closed=doc(R/'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_independent_review_codex/4bcd6b1bf2f941efa63f31e7a6cc7e67/review.final.json');ck('actual canonical lease satisfies pipeline306, termination alone insufficient',prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and prior.get('state') not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING') and prior['state']=='FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD' and closed['scope_uid']==prior['run_uuid'] and closed['decision']=='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' and closed['qualification'] is False);scan(prior)'''
new=''' prior=ow['card_path_bindings']['W13-03']['subtasks'].get('desktop58_finite_validation');closed=doc(prior['failed_closure_review_ref']['path']);ck('actual canonical lease satisfies pipeline306, termination alone insufficient',prior['run_uuid']=='b4d53db07f1e4ab8b9c0b37e291a6da5' and prior.get('state') not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING') and prior['state']=='FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD' and closed['scope_ref']==prior['scope_ref'] and closed['decision']=='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' and closed['qualification'] is False and prior['execution_grant'] is False);scan(prior)'''
assert old in s;s=s.replace(old,new)
s=s.replace("len(resource['files'])==23868 and len(runtime['files'])==1297 and len(compiler['files'])==22138 and len(resource['images'])==16","len(resource['files'])==23874 and len(runtime['files'])==1303 and len(compiler['files'])==22138 and len(resource['images'])==17")
old="runtimewanted={canonical_row(x)['path']:canonical_row(x) for x in base+corr+[q['wldp_static_ref']]+q['metadata_code_refs']+[s[k] for k in codekeys]}"
new="delta=doc(q['conhost_resource_delta_ref']['path']);scan(delta);runtimewanted={canonical_row(x)['path']:canonical_row(x) for x in base+corr+[q['wldp_static_ref']]+q['metadata_code_refs']+[s[k] for k in codekeys]+delta['additions_to_catalog_and_runtime']}"
assert old in s;s=s.replace(old,new).replace("'runtime exact1242+40+Wldp1+8+6'","'runtime exact1242+40+Wldp1+8+6code+6conhost'")
s=s.replace("ck('resource tools5',set(resource['tools'])=={'python','go','node','electron','git'})","ck('resource tools5',set(resource['tools'])=={'python','go','node','electron','git'});ck('staticimages exact Root q',resource['images']==q['static_image_refs'])")
with (O/"audit.py").open("xb") as f:f.write(s.encode())
print(json.dumps({"audit_sha256":hashlib.sha256(s.encode()).hexdigest(),"bytes":len(s.encode()),"source_algorithm":str(P),"candidate_executed":False,"audit_not_run":True}))

