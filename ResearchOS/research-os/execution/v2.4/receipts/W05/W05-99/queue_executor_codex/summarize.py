from pathlib import Path
import json,hashlib,re
root=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runs=[]
for directory in sorted(p for p in root.iterdir() if p.is_dir()):
    if not (directory/'result.json').exists():continue
    result=read(directory/'result.json')
    raw=directory/'stdout.raw'
    if not raw.exists():raw=directory/'stdout.jsonl'
    if not raw.exists():continue
    text=raw.read_text(encoding='utf-8-sig')
    events=[]
    for line in text.splitlines():
        try:
            event=json.loads(line)
            if isinstance(event,dict) and 'Action' in event:events.append(event)
        except ValueError:pass
    errors=[]
    for e in events:
        if e.get('OutputType')=='error' or e.get('Action')=='build-output':
            message=e.get('Output','')
            locations=re.findall(r'([\w-]+\.go):(\d+)',message)
            errors.append({'test':e.get('Test'),'source_line_at_run':locations,'raw_output':message})
    def tests(action):return [e['Test'] for e in events if e.get('Action')==action and e.get('Test')]
    node={k:int(m.group(1)) for k in ['tests','pass','fail','skipped'] if (m:=re.search(r'ℹ '+k+r' (\d+)',text))}
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in directory.iterdir() if p.is_file()}
    entry={'run':directory.name,'result':result,'command':read(directory/'command.json'),'files':files,
           'pass_events':tests('pass'),'fail_events':tests('fail'),'skip_events':tests('skip'),
           'node_counts':node,'errors':errors,
           'input_manifest_before':(directory/'inputs.json').exists(),'input_manifest_after':(directory/'inputs-after.json').exists()}
    if (directory/'inputs-after.json').exists():
        before={p['path']:p['sha256'] for p in read(directory/'inputs.json')}
        after={p['path']:p['sha256'] for p in read(directory/'inputs-after.json')}
        entry['full_input_vector_equal']=before==after
    expected=result.get('stdout_sha256')
    if expected:assert expected.lower()==sha(raw),directory
    expected=result.get('stderr_sha256')
    if expected:assert expected.lower()==sha(directory/'stderr.raw'),directory
    runs.append(entry)
(root/'run_index.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'run':r['run'],'exit':r['result'].get('exit_code'),'pass_events':len(r['pass_events']),'fail_events':len(r['fail_events']),'skips':len(r['skip_events']),'node':r['node_counts']} for r in runs],ensure_ascii=False,indent=2))
