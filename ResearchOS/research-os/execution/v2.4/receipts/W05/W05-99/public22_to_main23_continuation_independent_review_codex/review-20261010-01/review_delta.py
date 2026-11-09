import ast, copy, hashlib, importlib.util, json, ntpath, sys, time, traceback
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
Q = Path(__file__).resolve().parent
C = R / 'execution/v2.4/receipts/W05/W05-99/public22_to_main23_continuation_caller_source_codex/continue-20261010-01'
G = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def pin(p):
    b = Path(p).read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))

def save(name, value):
    p = Q / name
    with p.open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(p)

def shape(v):
    return type(v) is dict and set(v) == {'path', 'sha256', 'bytes'} and type(v['bytes']) is int

def norm(p):
    return ntpath.normcase(ntpath.normpath(str(p)))

def main():
    h = json.loads((C / 'HDF.json').read_bytes())
    i = json.loads(Path(h['source_inputs_ref']['path']).read_bytes())
    runtime = json.loads(Path(i['runtime_resources_ref']['path']).read_bytes())
    resource_lists = {k: len(v) for k, v in runtime.items() if type(v) is list}
    forbidden = [norm(R / 'ops/ci/retrieval.py'), norm(R / 'execution/v2.4/checkpoint.json'),
                 norm(R / 'execution/v2.4/path_ownership.json'), norm(R / 'execution/v2.4/step_state.json'),
                 norm(R / 'execution/v2.4/commands.json')]
    excluded = []
    source_refs = i['source_resource_refs']
    for r in source_refs:
        if not shape(r):
            raise ValueError('SOURCE_RESOURCE_REF_SHAPE')
        p = norm(r['path'])
        reason = None
        if p in forbidden:
            reason = 'LIVE_CANON_OR_NON_W05_RECENT_MAIN_ADOPTION_TARGET_NOT_ACQUIRED'
        if any(x in p for x in ('\\.codex\\sessions\\', '\\private\\')) or p.endswith(('.key', 'owner.token')):
            reason = 'PRIVATE_OR_LIVE_AUDIT_NOT_ACQUIRED'
        if reason:
            excluded.append(dict(ref=r, reason=reason))
    src_ref = h['caller_ref']
    direct = [pin(C / 'HDF.json'), pin(C / 'MF.json'), src_ref, h['source_inputs_ref'], h['calling_contract_ref'],
              i['owned_job_ref'], i['runtime_resources_ref'], i['toolchain_lock_ref'], i['main23_bound_ref'],
              i['existing22_decision_ref'], i['existing22_hdf_ref'], i['existing22_mf_ref'],
              i['main_recovery_source_ref'], pin(G)]
    spec = importlib.util.spec_from_file_location('p22c_review_guard_only', G)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    guard = mod.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    result = dict(schema='researchos.public22-continuation-independent-delta-controls.v1',
                  source_ref=src_ref, source_resource_count=len(source_refs), runtime_list_shapes=resource_lists,
                  excluded_metadata_only_refs=excluded, original_source_controls_replayed=False,
                  actual_product_calls=0, Go=None, Native=None, SQL=None, model=None, TP=None, controls=[])
    primary = None
    try:
        guard.acquire(direct)
        src = guard.get_buffer(src_ref['path'])
        tree = ast.parse(src.decode('utf-8'))
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        execute = funcs['execute']
        matches = []
        for n in ast.walk(execute):
            if isinstance(n, ast.For):
                for k, stmt in enumerate(n.body):
                    if isinstance(stmt, ast.With) and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                            and isinstance(x.func.value, ast.Name) and x.func.value.id == 'job' and x.func.attr == 'run_owned'
                            for x in ast.walk(stmt)):
                        matches.append((stmt, n.body[k + 1]))
        if len(matches) != 1:
            raise ValueError('UNIQUE_ACTUAL_RUN_OWNED_FRAGMENT_REQUIRED')
        with_node, next_node = matches[0]
        if not (isinstance(next_node, ast.Expr) and isinstance(next_node.value, ast.Call)
                and isinstance(next_node.value.func, ast.Name) and next_node.value.func.id == 'record_observation'):
            raise ValueError('ACTUAL_POST_CONTEXT_RECORD_STATEMENT_REQUIRED')
        fragment = ast.Module(body=[copy.deepcopy(with_node), copy.deepcopy(next_node)], type_ignores=[])
        fragment_code = compile(ast.fix_missing_locations(fragment), str(src_ref['path']), 'exec')
        recorder_code = compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(funcs['record_observation'])], type_ignores=[])),
                                str(src_ref['path']), 'exec')
        records = []
        for fail_on in (None, 'stdout', 'stderr'):
            observed = dict(actual_exit=0, pid=1234, creation_time_100ns=134360000000000001,
                            cleanup=dict(closed=True, job_closed=True, process_closed=True,
                                         thread_closed=True, job_idle=True, idle_active_processes=0, errors=[]))
            calls = []
            class Output:
                def __init__(self, label): self.label = label
                def open(self, mode):
                    if mode != 'xb': raise AssertionError('UNCHANGED_EXCLUSIVE_OUTPUT_MODE')
                    return self
                def __enter__(self): return self
                def __exit__(self, typ, value, tb):
                    if self.label == fail_on: raise OSError('SYNTHETIC_OUTPUT_CONTEXT_CLOSE_FAILURE')
                    return False
            class Job:
                def run_owned(self, *args, **kwargs):
                    calls.append(dict(timeout=args[5], creation_flags=kwargs['creation_flags']))
                    return copy.deepcopy(observed)
            invocation = dict(observation=None, actual_exit=None)
            env = dict(job=Job(), state=dict(new_native_children_attempted=0), invocation=invocation,
                       phase=dict(argv=['SYNTHETIC_NOT_EXECUTED'], cwd='SYNTHETIC'), env={},
                       outpath=Output('stdout'), errpath=Output('stderr'), time=time,
                       pin=lambda p: dict(path=p.label, sha256='0' * 64, bytes=0))
            exec(recorder_code, env)
            error = None
            try: exec(fragment_code, env)
            except OSError as exc: error = str(exc)
            if calls != [dict(timeout=90, creation_flags=0x08000000)] or env['observed'] != observed:
                raise AssertionError('EXACT_RETURNED_OBSERVATION_NOT_REACHED')
            if fail_on is None:
                ok = invocation['actual_exit'] == 0 and invocation['observation'] == observed and error is None
            else:
                ok = error == 'SYNTHETIC_OUTPUT_CONTEXT_CLOSE_FAILURE' and invocation['actual_exit'] is None and invocation['observation'] is None
            if not ok: raise AssertionError('SOURCE_COUNTEREXAMPLE_UNEXPECTED')
            records.append(dict(case='normal-close' if fail_on is None else fail_on + '-close-failure',
                                passed=True, source_behavior='RETURNED_OBSERVATION_RETAINED' if fail_on is None else 'KNOWN_RETURNED_OBSERVATION_LOST',
                                invocation=invocation, returned_observed=env['observed'], synthetic_error=error,
                                execution_authority=False, product_process_created=False))
        result['controls'] = records
        result['finding'] = dict(id='P22C-OBSERVATION-CLOSE-001', priority='P2', source_lines=[with_node.lineno, with_node.end_lineno, next_node.lineno],
                                 conclusion='Both output context-close exceptions discard already-returned actual exit and OwnedJob cleanup before recording.',
                                 minimal_revision='Persist known observation, actual_exit and end time immediately after run_owned returns, inside the with block; preserve separate output pin failures and unknown NULL.')
        result['source_contract_selected_fields'] = json.loads(guard.get_buffer(h['calling_contract_ref']['path']))
        result['main23_qualification_fields'] = json.loads(guard.get_buffer(i['main23_bound_ref']['path']))
        result['existing22_decision_fields'] = json.loads(guard.get_buffer(i['existing22_decision_ref']['path']))
    except BaseException as exc:
        primary = dict(type=type(exc).__name__, message=str(exc))
        traceback.print_exc()
    finally:
        result['guard_cleanup'] = guard.close()
        result['primary_error'] = primary
        close_ref = save('delta-sourceguard.closed.json', result['guard_cleanup'])
        result['guard_cleanup_ref'] = close_ref
        result_ref = save('delta-review-result.json', result)
        print(json.dumps(dict(result_ref=result_ref, guard_cleanup_ref=close_ref, finding=result.get('finding'),
                              controls=len(result['controls']), primary_error=primary,
                              excluded_refs=excluded, runtime_list_shapes=resource_lists), ensure_ascii=False))
    if primary is not None: return 1
    if result['guard_cleanup']['closed'] is not True or result['guard_cleanup']['errors']: return 1
    return 0

if __name__ == '__main__':
    rc = 1
    try: rc = main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT=' + str(rc))
    sys.exit(rc)
