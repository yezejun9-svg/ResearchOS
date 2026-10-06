from pathlib import Path
import json,hashlib,re,datetime
ROOT=Path('D:/作品集/ResearchOS/research-os');D=Path(__file__).resolve().parent;P=ROOT/'execution/v2.4/receipts/W05/W05-99/provider_resource_intake_codex/20261006-opencode-go';F=P/'thinking-disabled-repair'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in P.rglob('*') if p.is_file()];manifest=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
sus=[]
for p in files:
 raw=p.read_bytes()
 for label,pattern in [('literal_api_token',rb'\bsk[-_][A-Za-z0-9_-]{16,}'),('literal_bearer',rb'Bearer [A-Za-z0-9._~-]{16,}'),('private_key',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]:
  if re.search(pattern,raw):sus.append({'path':str(p.relative_to(ROOT)),'detector':label})
checks=[]
for where in [P,F]:
 before=json.loads((where/'source-before.json').read_bytes());after=json.loads((where/'source-after.json').read_bytes());current={}
 for name,want in before.items():
  path=Path(name);lower=path.as_posix().lower()
  assert '/.local/resources/' not in lower and '/credentials/' not in lower and path.suffix.lower() not in ['.sqlite','.db','.key','.pem'], 'private input path refused'
  current[name]=sha(path)
 inv=json.loads((where/'intake.invocation.json').read_bytes());build=json.loads((where/'build.json').read_bytes());binary=Path(build['binary'])
 rows={'directory':str(where.relative_to(ROOT)),'count':len(before),'before_after_equal':before==after,'current_drift':[{'path':k,'expected':v,'actual':current[k]} for k,v in before.items() if current[k]!=v],'binary_matches':sha(binary)==build['binary_sha256']==inv['binary_sha256'],'input_source_current_copy':sha(where/'intake/main.go'),'actual_exit':inv['actual_exit'],'stdout_hash_matches':sha(where/'intake.stdout.raw')==inv['stdout_sha256'],'stderr_hash_matches':sha(where/'intake.stderr.raw')==inv['stderr_sha256'],'invocation_sha256':sha(where/'intake.invocation.json')}
 checks.append(rows)
original=json.loads((P/'probe.response.json').read_bytes());new=json.loads((F/'probe.response.json').read_bytes());request=json.loads((F/'probe.request.json').read_bytes());oldrequest=json.loads((P/'probe.request.json').read_bytes());status=json.loads((F/'result.json').read_bytes());catalog=json.loads((F/'models.response.json').read_bytes())
subinv=[]
for f in P.rglob('*.invocation.json'):
 inv=json.loads(f.read_bytes());name=f.name.removesuffix('.invocation.json');row={'path':str(f.relative_to(ROOT)),'actual_exit':inv.get('actual_exit'),'sha256':sha(f)}
 for stream in ['stdout','stderr']:
  raw=f.parent/(name+'.'+stream+'.raw')
  if stream+'_sha256' in inv: row[stream+'_matches']=raw.is_file() and sha(raw)==inv[stream+'_sha256']
 subinv.append(row)
a={'schema':'researchos.provider-resource.read-audit.v1','reviewer_id':'codex:/root/w05_merge_review','read_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'namespace_files':manifest,'file_count':len(files),'credential_scan':{'detectors':['literal_api_token','literal_bearer','private_key'],'suspect_paths_only':sus,'limitation':'No vault/secret read. Exact-key echo prevention independently checked in executed source; namespace scan and structural review rather than recovery of secret material.'},'executions':checks,'all_invocations':subinv,'original':{'request_max_tokens':oldrequest['max_tokens'],'finish_reason':original['choices'][0]['finish_reason'],'visible_content_nonempty':bool(original['choices'][0]['message'].get('content','').strip()),'usage':original['usage']},'repair':{'request_max_tokens':request['max_tokens'],'thinking':request['thinking'],'response_model':new['model'],'finish_reason':new['choices'][0]['finish_reason'],'visible_content_nonempty':bool(new['choices'][0]['message']['content'].strip()),'usage':new['usage'],'catalog_actual_count':len(catalog['data']),'catalog_model_listed':any(x['id']=='deepseek-v4.1-flash' for x in catalog['data'])},'no_new_provider_requests':True,'no_vault_or_database_read':True}
(D/'audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not sus and all(x['before_after_equal'] and x['binary_matches'] and x['stdout_hash_matches'] and x['stderr_hash_matches'] for x in checks)
assert not checks[1]['current_drift'] and checks[1]['count']==2194 and checks[0]['actual_exit']==1 and checks[1]['actual_exit']==0
assert all(v for x in subinv for k,v in x.items() if k.endswith('_matches'))
assert not a['original']['visible_content_nonempty'] and a['repair']['visible_content_nonempty'] and new['model']==status['actual_response_model']=='deepseek-v4.1-flash' and status['catalog_http_status']==status['probe_http_status']==200
assert request['thinking']=={'type':'disabled'} and request['stream']==False and request['max_tokens']==256
print(json.dumps({'audit_sha256':sha(D/'audit.json'),'file_count':len(files),'original_drift':checks[0]['current_drift'],'repair_drift':checks[1]['current_drift'],'secret_detectors':len(sus)}))
