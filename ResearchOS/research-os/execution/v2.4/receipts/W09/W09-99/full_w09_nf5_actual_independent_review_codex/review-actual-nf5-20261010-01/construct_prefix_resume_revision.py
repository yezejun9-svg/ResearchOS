import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,data):
    p=Q/name
    with p.open('xb')as f:f.write(data if type(data)is bytes else(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    base=Q/'review_actual_nf5.v5.py';raw=base.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='c175af6f17fbc7e27bc8b50ccf4e57ab957a2575ea8c6a54b21368406f0f0ede'
    text=raw.decode('utf-8');nl='\r\n'if '\r\n'in text else '\n';edits=[]
    def change(before,after,count=1):
        nonlocal text
        before=before.replace('\n',nl);after=after.replace('\n',nl)
        assert text.count(before)==count,(before[:100],text.count(before))
        for _ in range(count):
            start=text.index(before);edits.append(dict(start=start,before=before,after=after))
            text=text[:start]+after+text[start+len(before):]
    change("    require(len(observed)==1,'EXACT_ONE_ACTUAL_HOST_RESULT')\n    observation=next(iter(observed.values()))",
           "    if b['schema']=='researchos.root-native-actual-host-pair.v1':\n        require(type(b['actual_host_chunk_id'])is str and b['actual_host_chunk_id']in observed,'EXACT_BOUND_HOST_CHUNK_PRESENT')\n        observation=observed[b['actual_host_chunk_id']]\n    else:\n        require(len(observed)==1,'EXACT_ONE_ACTUAL_HOST_RESULT');observation=next(iter(observed.values()))")
    call_run="    require('exec_command'in text and str(BASE/'run_full_w09.source.py')in text and c['selector_key']in text\n        and request_ref['path']in text and request_ref['sha256']in text\n        and re.search(r'\\b'+str(request_ref['bytes'])+r'\\b',text),'ACTUAL_REQUEST_AND_PRODUCER_CALL_ARGUMENTS')"
    change(call_run,"    verify_original_Root_command(text,c,request_ref,'run')")
    call_prepare="    require('exec_command'in text and str(BASE/'prepare_full_w09.source.py')in text and c['selector_key']in text\n        and request_ref['path']in text and request_ref['sha256']in text\n        and re.search(r'\\b'+str(request_ref['bytes'])+r'\\b',text),'ACTUAL_PREPARE_CALL_ARGUMENTS')"
    change(call_prepare,"    verify_original_Root_command(text,c,request_ref,'prepare')")
    body=text[text.index('def reviewed_runtime_closure('):text.index('def review_refused_c19(')]
    tail=body[body.index("    require(key(summary['compiler_inventory_ref'])"):body.index('    return dict(jobs=jobs,')]
    helpers=r'''def verify_original_Root_command(text,c,request_ref,stage):
    import shlex
    require('tools.exec_command('in text,'TRUE_ROOT_EXEC_COMMAND')
    raw=re.search(r'cmd\s*:\s*String\.raw`([^`]*)`',text,re.S)
    quoted=re.search(r'cmd\s*:\s*("(?:[^"\\]|\\.)*")',text,re.S)
    templated=re.search(r'cmd\s*:\s*`([^`]*)`',text,re.S)
    if raw is not None:
        command=raw.group(1);require('${'not in command,'NO_UNRESOLVED_RAW_COMMAND')
    elif quoted is not None:command=decode(quoted.group(1))
    else:
        require(stage=='prepare'and templated is not None,'ONLY_OBSERVED_PREPARE_TEMPLATE')
        base_match=re.search(r'const base=String\.raw`([^`]*)`;',text)
        py_match=re.search(r'const py=("(?:[^"\\]|\\.)*");',text)
        matrix_match=re.search(r'const pairs=(\[\[.*?\]\]);',text,re.S)
        require(base_match is not None and py_match is not None and matrix_match is not None,'EXACT_PREPARE_PUBLIC_CONSTANTS')
        matrix=decode(matrix_match.group(1))
        require(type(matrix)is list and len(matrix)==3 and {r[0]for r in matrix}=={'W09-G01','A06','C19'}
            and all(type(r)is list and len(r)==3 and type(r[0])is str and type(r[1])is str
                and re.fullmatch('[0-9a-f]{64}',r[1])and type(r[2])is int and r[2]>0 for r in matrix),'EXACT_PREPARE_REQUEST_MATRIX')
        chosen=[r for r in matrix if r[0]==c['selector_key']]
        require(len(chosen)==1 and chosen[0][1:]==[request_ref['sha256'],request_ref['bytes']],'EXACT_SELECTOR_REQUEST_SHA_BYTES')
        template=decode('"'+templated.group(1)+'"')
        values=dict(base=base_match.group(1),py=decode(py_match.group(1)),key=c['selector_key'],sha=chosen[0][1],size=str(chosen[0][2]))
        require(set(re.findall(r'\$\{([^}]+)\}',template))==set(values),'ONLY_FIVE_FIXED_TEMPLATE_VALUES')
        command=re.sub(r'\$\{([^}]+)\}',lambda m:values[m.group(1)],template)
    tokens=shlex.split(command.splitlines()[0],posix=True)
    require(len(tokens)==12 and tokens[0]=='&'and tokens[2:7]==['-I','-S','-B','-X','utf8']
        and tokens[8]==c['selector_key']and tokens[10]==request_ref['sha256']and tokens[11]==str(request_ref['bytes']),
        'EXACT_ACTUAL_ROOT_ARGV_TOKENS')
    same_path=lambda a,b:ntpath.normcase(str(Path(a).absolute()))==ntpath.normcase(str(Path(b).absolute()))
    require(same_path(tokens[1],c['tool_refs']['python']['path'])and same_path(tokens[7],BASE/(stage+'_full_w09.source.py'))
        and same_path(tokens[9],ref_shape(request_ref)),'SAME_PHYSICAL_ROOT_CLI_AND_REQUEST_PATHS')
    return dict(argv=tokens,source='REAL_ROOT_CAPTURE_ONLY',future_execution=False)

def reviewed_launcher_tail(closed,c,summary,jobs,guards,stable,inv,bp):
__TAIL__
    return dict(jobs=jobs,compiler_inventory_ref=summary['compiler_inventory_ref'],compiler_input_refs_held=len(stable),
        actual_compiler_packages=inv['package_count'],module_count=len(bp['module_go_mod_refs']),
        private_generated_inputs=len(inv['private_generated_input_refs']),private_export_inputs=len(inv['private_export_refs']),
        launcher_started_ref=started_ref,launcher_closed_ref=ended_ref,inner_Go_separate_OwnedJob_receipt=None,
        inner_Go_lifetime='INHERITS_EXCLUSIVE_OUTER_OWNED_PYTHON_JOB',unknown_individual_child_exits=None,all_original_guards_closed=True)

def resume_verified_G01_prefix(row,c,closure,profile_raw,bp):
    original_ref=pin(Q/'original1168.binding.json');origin=decode(read_ref(original_ref))
    require(origin['original_ordinal']==1168 and origin['actual_chunk_id']=='784193'and origin['actual_outer_exit']==origin['actual_Python_exit']==1
        and origin['source_thread_id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'and origin['guard_state']=='VERIFIED_CLOSED_0',
        'ACTUAL_PREVIOUS_PARTIAL_EXECUTION')
    code=read_ref(origin['failed_script_ref']);require(digest(code)=='c175af6f17fbc7e27bc8b50ccf4e57ab957a2575ea8c6a54b21368406f0f0ede',
        'EXACT_PREVIOUS_EXECUTED_SOURCE')
    io=decode(read_ref(origin['full_tool_IO_ref']));trace=io['result']['output']
    require(io['result']['chunk_id']=='784193'and io['result']['exit_code']==1 and 'line 425, in review_group'in trace
        and 'line 141, in root_pair'in trace and 'ValueError: EXACT_ONE_ACTUAL_HOST_RESULT'in trace
        and '2e4e45e9cc2e57aef0e431dd1a98d1308112837e2745b4683189fe6f5b2b8dcf'in io['request']['cmd'],'EXACT_OBSERVED_PREFIX_ENDPOINT')
    previous_guard=decode(read_ref(origin['guard_ref']));guard_receipt(previous_guard)
    ready=decode(read_ref(row['prepare_ref']));closed=decode(read_ref(row['producer_closed_ref']));summary=packet_artifacts(closed,c)
    report=decode(read_ref(summary['report_ref']));tool=decode(read_ref(summary['tool_run_ref']))
    # v5 trace reaches its captures assignment after every G01 native/owned/3905/19 check.
    # No previous variable values are invented: below only index pinned artifacts for new Mode/launcher/root-capture checks.
    native=dict(stdout=pin(R/report['raw_evidence_references'][0]),stderr=pin(R/report['raw_evidence_references'][1]),
        go=report['go_executable'],source_hashes=report['version_manifest']['source_sha256'])
    members={};events={}
    opaque=('http-request','http-response','file-body-','g02-junction-stdout')
    for claim in report['owned_export']['members']:
        path=ref_shape(claim);members[path]=claim;label=path.name.split('-',1)[1][:-4]
        if label.startswith(opaque)or label in closure.A06_MANIFEST_RAW_LABELS or re.fullmatch(r'simulated-opinion-(?:0[0-9]|1[0-9])',label):continue
        value=decode(read_ref(claim));events.setdefault(label,[]).append(dict(value=value,path=path,pin=claim,test=path.parent.name))
    owned=dict(members=members,events=events)
    stream_events=[decode(line)for line in read_ref(native['stdout']).splitlines()]
    clocks=[clock(event['Time'])for event in stream_events];intervals=[min(clocks).isoformat(),max(clocks).isoformat()]
    jobs=[]
    for observed in closed['invocation_observations']:
        record=observed['record'];result=record['result'];jobs.append(dict(label=observed['label'],ref=observed['ref'],actual_exit=result['actual_exit'],
            pid=result['owned_child_pid'],creation_time_100ns_decimal=record['creation_time_100ns_decimal'],owned_job_closed=True,unknown_individual_child_exit=None))
    guards={g['label']:{(ntpath.normcase(e['path']),e['sha256'],e['bytes'])for e in g['observation']['entries']}for g in closed['guard_cleanups']}
    stable={(ntpath.normcase(e['path']),e['sha256'],e['bytes'])for e in bp['stable_input_refs']};inv=decode(read_ref(summary['compiler_inventory_ref']))
    captures=[*root_prepare_pair(row['prepare_initial_Root_capture_ref'],row['prepare_completed_Root_capture_ref'],ready,c,closed['request_ref']),
        *root_run_pair(row['run_initial_Root_capture_ref'],row['run_completed_Root_capture_ref'],closed['invocation_observations'][-1]['ref'],c,closed['request_ref'])]
    return dict(selector=c['selector_key'],run_id=c['run_id'],report_ref=summary['report_ref'],tool_run_ref=summary['tool_run_ref'],
        actual_native_exit=0,assertions=c['expected_native_ids'],selected_tests=c['selected_tests'],owned_members=len(members),native_event_interval=intervals,
        jobs=jobs,Root_original_tool_pairs=captures,compiler_input_refs_held=len(stable),module_count=len(bp['module_go_mod_refs']),
        mode_predicate_facts=mode_facts(closure,owned,report,c,native),runtime_closure=reviewed_launcher_tail(closed,c,summary,jobs,guards,stable,inv,bp),
        reused_verified_prefix_ref=original_ref,reused_prefix_guard_ref=origin['guard_ref'],native_owned_3905_19_checks_repeated=False,
        formal_case_accepted_delta=0,formal_acceptance=False)

'''.replace('__TAIL__',tail.rstrip('\r\n').replace('\r\n','\n'))
    change('def collect_actual_refs(packet,choices):',helpers+'def collect_actual_refs(packet,choices):')
    change('        formal_case_accepted_delta=0,formal_acceptance=False)\n\ndef execute_review(args):',
           "        runtime_closure=reviewed_launcher_tail(closed,c,summary,jobs,guards,stable,inv,bp),\n        formal_case_accepted_delta=0,formal_acceptance=False)\n\ndef execute_review(args):")
    change("            facts=review_group(packet['groups'][name],choices[name],closure,profile_raw,bp)",
           "            facts=(resume_verified_G01_prefix if name=='W09-G01'else review_group)(packet['groups'][name],choices[name],closure,profile_raw,bp)")
    change("                runtime_closure=reviewed_runtime_closure(closed,ready,choices[name],packet_artifacts(closed,choices[name]),bp),\n",'')
    change("        pin(R/'execution/toolchains/locked.json'),*collect_actual_refs(packet,choices)]",
           "        pin(R/'execution/toolchains/locked.json'),pin(Path(__file__)),pin(Q/'original1168.binding.json'),\n        pin(Q/'original1168.full-tool-IO.json'),pin(Q/'original1168.actual.raw.jsonl'),pin(Q/'original1168.failed-script.py'),\n        pin(Q/'actual-review-v5-guard.closed.json'),*collect_actual_refs(packet,choices)]")
    change('actual-review-v5-guard.closed.json','actual-review-v6-guard.closed.json',3)
    # Keep the two references to the genuinely completed previous guard, not the new guard.
    change("pin(Q/'actual-review-v6-guard.closed.json'),*collect_actual_refs", "pin(Q/'actual-review-v5-guard.closed.json'),*collect_actual_refs")
    ast.parse(text);restored=text
    for e in reversed(edits):
        assert restored[e['start']:e['start']+len(e['after'])]==e['after']
        restored=restored[:e['start']]+e['before']+restored[e['start']+len(e['after']):]
    assert restored.encode('utf-8')==raw
    candidate=write('review_actual_nf5.v6.py',text.encode('utf-8'))
    inverse=write('prefix-resume-revision.inverse.json',dict(schema='researchos.readonly-review-source-exact-inverse.v1',base_ref=pin(base),candidate_ref=candidate,
        edits=edits,exact_inverse_byte_equal=True,Root_actual_batch_host_selection=True,original_G01_prefix_reused=True,
        previous_3905_and_19_not_repeated=True,unperformed_Mode_launcher_Root_checks_only=True,Native_runs=0,Go_runs=0,formal_acceptance=False))
    contract=json.loads((Q/'input-contract.v6.json').read_text(encoding='utf-8'));contract['reviewer_program_ref']=candidate
    contract['future_argv'][6]=candidate['path'];contract['previous_contract_ref']=pin(Q/'input-contract.v6.json');contract['inverse_ref']=inverse
    contract['Root_command_observation']='Parse exact actual quoted/raw/finite observed prepare-template argv; normalize only physical path spelling. No arbitrary evaluation, new Root stage, or future capture.'
    contract['previous_G01_prefix_ref']=pin(Q/'original1168.binding.json');cref=write('input-contract.v7.json',contract)
    print(json.dumps(dict(program_ref=candidate,contract_ref=cref,inverse_ref=inverse,exact_inverse_pass=True),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
