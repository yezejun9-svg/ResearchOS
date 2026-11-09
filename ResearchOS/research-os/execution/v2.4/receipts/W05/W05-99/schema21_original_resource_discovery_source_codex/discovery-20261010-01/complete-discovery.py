import hashlib, json, re
from pathlib import Path
N=Path(__file__).resolve().parent
ROOT=Path(r'D:/作品集/ResearchOS/research-os')
SELF=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-49-27-01a11e22-ecb2-7720-80d2-af63727d414d.jsonl')
def digest(b): return hashlib.sha256(b).hexdigest()
def ref(p):
    p=Path(p); b=p.read_bytes(); return dict(path=p.as_posix(),sha256=digest(b),bytes=len(b))
def save(name,obj):
    p=N/name; p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return ref(p)
catalog=json.loads((N/'source-object-inventory.json').read_bytes())
io=json.loads((N/'git-commands.actual.json').read_bytes())
all_data={}
for candidate,record in zip(catalog,[x for x in io if '--batch' in x['argv']]):
    raw=Path(record['stdout']['path']).read_bytes(); pos=0; data={}
    for ent in candidate['source_objects']:
        end=raw.index(b'\n',pos); header=raw[pos:end].decode().split(); size=int(header[2]); pos=end+1
        data[ent['git_path']]=raw[pos:pos+size];pos+=size+1
        assert digest(data[ent['git_path']])==ent['sha256']
    assert pos==len(raw); all_data[candidate['commit']]=data
recommended=catalog[1]; old22=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/frozen_source'
runtime_comparisons=[]
for c in catalog:
    data=all_data[c['commit']]; comparisons=[]
    for p in c['runtime_paths']:
        r=ref(old22/p); comparisons.append({'git_path':p,'candidate_sha256':digest(data[p]),'existing_old22_ref':r,'bytes_equal':r['sha256']==digest(data[p])})
    runtime_comparisons.append({'commit':c['commit'],'runtime_file_comparisons':comparisons,'all_equal':all(x['bytes_equal'] for x in comparisons)})
save('old22-shared-runtime-source-comparison.json',runtime_comparisons)

# Per-entrypoint static transitive package superset. No Go parser/compiler claim.
per=[]; data=all_data[recommended['commit']]
for entry in ['apps/control','ops/backup','apps/cli']:
    pkgs={entry}; seen=set(); changed=True; embeds=set()
    while changed:
        changed=False
        for p,b in data.items():
            if not p.endswith('.go') or p.endswith('_test.go') or Path(p).parent.as_posix() not in pkgs: continue
            seen.add(p); s=b.decode()
            for block in re.findall(r'(?m)^import\s*(\([^)]*\)|[^\n]+)',s):
                for imp in re.findall(r'"([^"\n]+)"',block):
                    pre='researchos.local/research-os/'
                    if imp.startswith(pre) and imp[len(pre):] not in pkgs:pkgs.add(imp[len(pre):]);changed=True
            for line in re.findall(r'(?m)^//go:embed\s+(.+)$',s):
                for pat in line.split():embeds.add((Path(p).parent/pat).as_posix())
    paths=sorted(seen|embeds|{'go.mod','go.sum'}); index={e['git_path']:e for e in recommended['source_objects']}
    per.append({'entrypoint':'./'+entry,'role':'required' if entry!='apps/cli' else 'optional host-client protocol CLI; not needed for owner bootstrap or backup','packages':sorted(pkgs),'files':[index[p] for p in paths],'bytes':sum(len(data[p]) for p in paths)})
minpaths=sorted(set(e['git_path'] for c in per[:2] for e in c['files'])|set(recommended['runtime_paths']))
index={e['git_path']:e for e in recommended['source_objects']}
save('root-build-input-scope.json',{'source_commit':recommended['commit'],'source_tree':recommended['tree'],'entrypoints':per,'control_backup_and_runtime_union':[index[p] for p in minpaths],'total_files':len(minpaths),'total_bytes':sum(len(data[p]) for p in minpaths),'extraction':'Root may extract these exact git blobs into one new isolated source root, verifying blob ID, sha256 and byte length. Preserve original Go/SQL/contracts; no truncation of current main or old22 roots. Do not copy toolchain/module/build caches.','status':'STATIC_BUILD_INPUT_SUPERSET_PENDING_REAL_GO_LIST_AND_INDEPENDENT_BUILD','os_tag_note':'All non-test OS/tag variants within transitively referenced local packages are retained. No vendor closure inferred. Compiler-selected dependencies still need real Go list.'})

# Independently check selected metadata hashes against their existing MF without traversing dependencies.
prior=json.loads((N/'existing-qualification-refs.json').read_bytes()); checks=[]
for entry in prior['refs']:
    r=entry['ref']; p=Path(r['path']); assert ref(p)==r
    if p.name in ('HDF.json','MF.json'): continue
    mf=p.parent/'MF.json'
    if not mf.is_file():checks.append({'ref':r,'mf_membership':'NO_MF_IN_SAME_DIRECTORY_METADATA_ONLY'});continue
    m=json.loads(mf.read_bytes()); matches=[]
    def walk(x):
        if isinstance(x,dict):
            if set(('path','sha256')).issubset(x):
                q=Path(x['path']);q=q if q.is_absolute() else p.parent/q
                if q.resolve()==p.resolve():matches.append(x)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(m)
    ok=any(x.get('sha256')==r['sha256'] and x.get('bytes',x.get('size'))==r['bytes'] for x in matches)
    checks.append({'ref':r,'mf_ref':ref(mf),'mf_membership':'MATCH' if ok else 'NOT_TYPED_MEMBER_RECHECK_ONLY'})
save('selected-prior-metadata-checks.json',checks)

# Capture actual host log call/output bytes for this task's discovery steps.
chunks=['74d9b9','e47424','141490','4eb584','04c629','21ded7','010878','d5aa26','93ddcf','90bb27','c539ef','1f9fe0','325a80','021c46','050b2f']
size=SELF.stat().st_size
with SELF.open('rb') as f:
    first=f.readline(); start=max(len(first),size-16000000); f.seek(start)
    if start>len(first):f.readline()
    offset=f.tell();tail=f.read(size-offset)
calls={}; pairs={}
for line in tail.splitlines(keepends=True):
    try:item=json.loads(line)
    except (ValueError,UnicodeDecodeError):offset+=len(line);continue
    p=item.get('payload',{}); kind=p.get('type'); cid=p.get('call_id')
    if kind in ('function_call','custom_tool_call') and cid:calls[cid]=(offset,line,item)
    if kind in ('function_call_output','custom_tool_call_output') and cid in calls:
        for chunk in chunks:
            if chunk in str(p.get('output','')) and chunk not in pairs:pairs[chunk]=(calls[cid],(offset,line,item))
    offset+=len(line)
assert set(pairs)==set(chunks), {'missing_captures':sorted(set(chunks)-set(pairs))}
captures=[]
for chunk in chunks:
    call,result=pairs[chunk];p=N/f'actual-discovery-{chunk}.raw.jsonl';p.write_bytes(first+call[1]+result[1])
    binding=save(f'actual-discovery-{chunk}.binding.json',dict(source_audit_path=SELF.as_posix(),source_prefix_size_observed=size,source_line_offsets=[0,call[0],result[0]],source_line_lengths=[len(first),len(call[1]),len(result[1])],source_line_sha256=[digest(first),digest(call[1]),digest(result[1])],original_capture_ref=ref(p),original_call_id=call[2]['payload']['call_id'],chunk_id=chunk))
    captures.append({'chunk_id':chunk,'raw_ref':ref(p),'binding_ref':binding})
save('actual-discovery-capture-index.json',{'captures':captures,'discovery_script_chunk':'1f9fe0','discovery_script_outer_exit':0,'discovery_script_python_exit':0,'mechanical_failures':[],'rg_nomatch_outer1_chunk':'e47424','rg_nomatch_qualification':'Normal no-match exit, no stderr exception, not a mechanical failure.','truncated_console_outputs_preserved_as_actual':True,'no_claim_of_full_console_when_truncated':True})
summary={'recommended_commit':recommended['commit'],'tree':recommended['tree'],'numbered_schema_max':21,'public_startup_session_install':True,'static_minimum_control_backup_runtime_files':len(minpaths),'static_minimum_bytes':sum(len(data[p]) for p in minpaths),'all24_runtime_inputs_equal_existing_qualified_old22_root':runtime_comparisons[1]['all_equal'],'per_entrypoints':[{'entrypoint':x['entrypoint'],'files':len(x['files']),'bytes':x['bytes']} for x in per],'captures':len(captures),'prior_metadata_checks':len(checks)}
save('discovery-summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
