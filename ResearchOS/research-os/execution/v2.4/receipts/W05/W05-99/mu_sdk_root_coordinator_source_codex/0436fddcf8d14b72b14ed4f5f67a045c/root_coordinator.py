"""Review candidate. Import has no I/O; only Root may call run_resident().

NO_PROVIDER validates existing bootstrap evidence only. MODEL_TRIAL prepares
the trusted Host before one shared 300-second admission/qualification/C7 window.
No automatic dispatch retry exists. A retained result requires the same Python
parent to remain alive. This module's Source status is not execution authority.
"""
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import threading
import time
import types
import uuid
from datetime import datetime, timezone, timedelta

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = 'adc460c2138528f163f7fdab5e8d81dde157b7fb'
ANCHOR = '_researchos_root_sdk_coordinator_v1'
AUTHORS = {'codex:/root', 'codex:/root/command_queue_impl'}
ENV_KEYS = {'SystemRoot', 'WINDIR', 'PATH', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'TEMP', 'TMP'}

def require(ok, text):
    if not ok:
        raise RuntimeError(text)

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def pinned(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}, 'exact pin required')
    require(type(ref['bytes']) is int and ref['bytes'] > 0, 'positive typed pin size required')
    path = Path(ref['path'])
    require(path.is_absolute(), 'absolute pin required')
    raw = path.read_bytes()
    require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'pin drift')
    return raw

def read_json(ref):
    return json.loads(pinned(ref))

def input_basis_hash(doc):
    basis = {k: v for k, v in doc.items() if k != 'root_execution_authority_ref'}
    return hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def put(path, value):
    with Path(path).open('xb') as target:
        target.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def load_module(ref, raw):
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'] and len(raw) == ref['bytes'], 'module buffer drift')
    module = types.ModuleType('root_sdk_' + Path(ref['path']).stem)
    module.__file__ = ref['path']
    exec(compile(raw, ref['path'], 'exec'), module.__dict__)
    return module

def utc_text(value):
    return value.strftime('%Y-%m-%dT%H:%M:%S') + ('.' + value.strftime('%f').rstrip('0') if value.microsecond else '') + 'Z'

def closed_environment(env):
    require(type(env) is dict and set(env) <= ENV_KEYS, 'closed public environment required')
    require(all(type(k) is str and type(v) is str and '\x00' not in k + v for k, v in env.items()), 'invalid environment')
    require(env.get('SystemRoot') == env.get('WINDIR') == 'C:/Windows', 'system directory mismatch')
    require(env.get('PATH') == 'C:/Windows/System32;C:/Windows', 'executable search path must be closed')
    return dict(env)

def native_closed(result):
    if type(result) is not dict or type(result.get('job_cleanup')) is not dict:
        return False
    c = result['job_cleanup']
    return c.get('errors') == [] and type(c.get('active_processes_last_observed')) is int and c['active_processes_last_observed'] == 0 and all(c.get(k) is True for k in ('unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'))

def matching_idle_proof(proof, identity, start, end):
    return (type(proof) is dict and type(identity) is dict and 0 <= end-start <= 2 and
        proof.get('schema') == 'researchos.held-job-cleanup-observation.v1' and
        type(proof.get('observed_monotonic')) in (int, float) and math.isfinite(proof['observed_monotonic']) and
        start <= proof['observed_monotonic'] <= end and
        all(type(proof.get(k)) is type(identity.get(k)) and proof.get(k) == identity.get(k) for k in ('run_uuid', 'owner_pid', 'runner_pid', 'creation_time_100ns', 'job_binding_id')) and
        all(proof.get(k) is True for k in ('captured_before_resume', 'held_job_handle', 'held_primary_handle', 'pid_match', 'creation_match', 'primary_exit_confirmed')) and
        type(proof.get('active_processes')) is int and proof['active_processes'] == 0 and proof.get('errors') == [])

def validate_bootstrap(result, lifecycle, guard_cleanup):
    require(result.get('stage') == 'BOOTSTRAP_ONLY' and result.get('actor_id') == 'codex:/root', 'actual Root bootstrap required')
    require(type(result.get('provider_requests')) is int and result['provider_requests'] == 0 and result.get('qualification') is None and result.get('formal_acceptance') is None, 'bootstrap is not runtime qualification')
    require(lifecycle.get('all_owned_jobs_cleanup_confirmed') is True and lifecycle.get('error') is None and lifecycle.get('provider_requests') == 0, 'bootstrap lifecycle incomplete')
    jobs = lifecycle.get('jobs')
    require(type(jobs) is list and {j.get('label') for j in jobs} == {'normal-host', 'cli-init', 'cli-goal'} and len(jobs) == 3 and all(j.get('closed') is True for j in jobs), 'exact bootstrap cleanup set required')
    require(guard_cleanup.get('closed') is True and guard_cleanup.get('retained_handles_count') == 0 and guard_cleanup.get('errors') == [], 'bootstrap Source guard cleanup incomplete')
    require(result.get('db_counts') and all(type(n) is int and n == 0 for n in result['db_counts'].values()), 'bootstrap database was not provider-free')
    require(set(result['db_counts']) == {'Task', 'Run', 'BudgetLedgerEntry', 'resource_effects'}, 'bootstrap zero-count scope mismatch')
    for key in ('project_id', 'goal_id', 'workspace_ref', 'workspace_witness'):
        require(type(result.get(key)) is str and result[key], 'bootstrap identity missing')
    data = Path(result['data_root'])
    require(data.is_absolute() and ROOT / '.local' in data.parents and Path(result['workspace']) == data / 'workspace', 'bootstrap isolation layout')
    for key in ('discovery_file', 'cli_config_file'):
        require(data in Path(result[key]).parents, 'bootstrap consumed path outside data root')

class RootResidentCoordinator:
    """One coordinator per parent, anchored before any native invocation."""
    def __init__(self, input_ref, review_ref):
        require(getattr(sys, ANCHOR, None) is None, 'previous coordinator requires reconciliation; no retry')
        self.owner_pid = os.getpid()
        self.state = 'PREFLIGHT'
        self.error = None
        self.guards = []
        self.jobs = {}
        self.lock = threading.RLock()
        self.host_thread = None
        self.pipe_read = self.pipe_write = None
        self.controller = self.c7_owner = None
        self.c7_run_uuid = None
        self.go_sent = False
        self.started = self.deadline = self.started_utc = None
        self.done = threading.Event()
        setattr(sys, ANCHOR, self)
        self.input_ref, self.review_ref = input_ref, review_ref

    def _guard(self, refs):
        guard = self.guard_module.SourceReadGuard(per_file_cap=128*1024*1024, total_cap=512*1024*1024)
        self.guards.append(guard)  # own it before acquisition can partially fail
        guard.acquire(refs)
        return guard

    def _module(self, key):
        ref = self.fixed[key]
        return load_module(ref, self.source_guard.get_buffer(ref['path']))

    def open(self):
        doc = read_json(self.input_ref)
        review = read_json(self.review_ref)
        require(doc.get('schema') == 'researchos.root-sdk-coordinator-input.v1' and doc.get('mode') in ('NO_PROVIDER', 'MODEL_TRIAL'), 'coordinator input schema/mode')
        require(review.get('schema') == 'researchos.root-sdk-coordinator-source-review.v1' and review.get('decision') == 'READY_SOURCE_ONLY' and review.get('actor_id') not in AUTHORS | {'', None}, 'independent coordinator Source review required')
        require(review.get('formal_acceptance') is False and review.get('source_ref') == doc['coordinator_source_ref'] and review.get('fixed_pins_ref') == doc['fixed_pins_ref'], 'reviewed coordinator tuple differs')
        require(Path(doc['coordinator_source_ref']['path']) == Path(__file__).resolve(), 'coordinator source location differs')
        pinned(doc['coordinator_source_ref'])
        self.fixed = read_json(doc['fixed_pins_ref'])
        self.input = doc
        self.bootstrap = read_json(doc['bootstrap_result_ref'])
        validate_bootstrap(self.bootstrap, read_json(doc['bootstrap_lifecycle_ref']), read_json(doc['bootstrap_guard_cleanup_ref']))
        self.env = closed_environment(doc['public_environment'])
        self.output = Path(doc['output_dir'])
        require(self.output.is_absolute() and not self.output.exists() and self.output.parent.is_dir() and ROOT / 'execution/v2.4/receipts/W05/W05-99' in self.output.parents, 'fresh owned output directory required')
        self.output.mkdir()
        if doc['mode'] == 'NO_PROVIDER':
            self.state = 'BOOTSTRAP_VERIFIED'
            put(self.output / 'bootstrap-consumption.json', {'mode': 'NO_PROVIDER', 'bootstrap_result_ref': doc['bootstrap_result_ref'], 'bootstrap_lifecycle_ref': doc['bootstrap_lifecycle_ref'], 'candidate_native_processes': 0, 'provider_requests': 0, 'C7_actual_lifecycle_proven': False, 'runtime_qualification': False, 'formal_acceptance': False})
            return self
        for ref in self.fixed.values():
            pinned(ref)
        require(Path(sys.executable) == Path(self.fixed['python_binary']['path']), 'Root parent interpreter differs from fixed Python')
        self.guard_module = load_module(self.fixed['source_guard'], pinned(self.fixed['source_guard']))
        refs = list(self.fixed.values()) + [self.input_ref, self.review_ref, doc['coordinator_source_ref'], doc['fixed_pins_ref'], doc['bootstrap_result_ref'], doc['bootstrap_lifecycle_ref'], doc['bootstrap_guard_cleanup_ref']]
        self.source_guard = self._guard(refs)
        self.input = json.loads(self.source_guard.get_buffer(self.input_ref['path']))
        self.bootstrap = json.loads(self.source_guard.get_buffer(doc['bootstrap_result_ref']['path']))
        validate_bootstrap(self.bootstrap, json.loads(self.source_guard.get_buffer(doc['bootstrap_lifecycle_ref']['path'])), json.loads(self.source_guard.get_buffer(doc['bootstrap_guard_cleanup_ref']['path'])))
        self.controller = self._module('controller')
        self.c7_owner = self.controller.get_resident_source_owner()
        self.hooks = self._module('hooks')
        self.producer_module = self._module('cleanup_producer')
        self.watchdog_module = self._module('job_watchdog')
        self.engine = self._module('runner')
        self.state = 'BOOTSTRAP_VERIFIED'
        put(self.output / 'bootstrap-consumption.json', {'mode': doc['mode'], 'bootstrap_result_ref': doc['bootstrap_result_ref'], 'bootstrap_lifecycle_ref': doc['bootstrap_lifecycle_ref'], 'provider_requests_by_this_coordinator': 0, 'C7_actual_lifecycle_proven': False, 'runtime_qualification': False, 'formal_acceptance': False})
        return self

    def _invoke(self, label, argv, deadline, stdin=None, host=False):
        with self.lock:
            require(label not in self.jobs, 'native operation already attempted; no retry')
            rec = {'label': label, 'native_invoked': False, 'result': None, 'producer': None, 'watchdog': None, 'identity': None, 'error': None, 'cleanup': None}
            self.jobs[label] = rec
        def before(actual):
            require(actual['assigned_before_resume'] is True and actual['kill_on_job_close_configured'] is True and actual['resumed'] is False and actual['absolute_deadline_monotonic'] <= deadline, 'owned process deadline/pre-resume mismatch')
            rec['producer'] = self.producer_module.HeldJobCleanupProducer(self.run_uuid + ':' + label, self.owner_pid)
            rec['identity'] = rec['producer'].capture_before_resume(actual)
            rec['watchdog'] = self.watchdog_module.JobDeadlineWatchdog(actual['job_handle'], actual['absolute_deadline_monotonic'])
            rec['watchdog'].start()
            if host:
                api = ctypes.WinDLL('kernel32', use_last_error=True)
                check = api.IsProcessInJob
                check.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
                check.restype = ctypes.c_int
                yes = ctypes.c_int()
                require(bool(check(actual['process_handle'], actual['job_handle'], ctypes.byref(yes))) and yes.value != 0, 'actual Host exact Job membership failed')
                binding = rec['identity']['job_binding_id']
                self.host_contract_ref = put(self.output / 'host-job.contract.json', {'schema': 'researchos.mu-trial-host-job.v1', 'host_pid': actual['runner_pid'], 'root_job_id': binding, 'root_pid': self.owner_pid, 'deadline_utc': self.deadline_utc, 'deadline_monotonic': self.deadline, 'actual_owned_deadline_monotonic': actual['absolute_deadline_monotonic'], 'held_identity': rec['identity']})
                self.host_probe_ref = put(self.output / 'host-job.probe.json', {'schema': 'researchos.mu-trial-host-job-probe.v1', 'host_pid': actual['runner_pid'], 'root_job_id': binding, 'root_pid': self.owner_pid, 'in_job': True, 'descendant_of_root': True, 'direct_CreateProcess_from_root': True, 'actual_IsProcessInJob_return': True, 'observed_monotonic': time.monotonic(), 'captured_before_resume': True, 'held_identity': rec['identity']})
        try:
            with (self.output / (label + '.stdout.raw')).open('xb') as out, (self.output / (label + '.stderr.raw')).open('xb') as err:
                timeout = deadline-time.monotonic()-0.25
                require(timeout > 0, 'native deadline exhausted')
                rec['native_invoked'] = True
                rec['result'] = self.hooks.run_owned_hooked(argv, str(ROOT), self.env, out, err, timeout, before, stdin=stdin, creation_flags=0x08000000)
            require(native_closed(rec['result']), 'owned native cleanup incomplete')
            require(rec['result']['error'] is None and rec['result']['actual_exit'] == 0 and rec['result']['timed_out'] is False, 'native execution failed')
            return rec['result']
        except BaseException as exc:
            rec['error'] = type(exc).__name__ + ': ' + str(exc)
            raise
        finally:
            put(self.output / (label + '.invocation.json'), {'argv': argv, 'cwd': str(ROOT), 'environment': self.env, 'result': rec['result'], 'error': rec['error'], 'native_exit': rec['result'].get('actual_exit') if rec['result'] else None, 'python_exit': None, 'stdout_ref': pin(self.output / (label + '.stdout.raw')) if (self.output / (label + '.stdout.raw')).is_file() else None, 'stderr_ref': pin(self.output / (label + '.stderr.raw')) if (self.output / (label + '.stderr.raw')).is_file() else None, 'formal_acceptance': False})

    def _host_phase(self, phase, receipt, deadline, extras=(), stdin=None):
        return self._invoke('host-' + phase, [self.fixed['trusted_host_binary']['path'], '-phase', phase, '-seed', self.host_seed_ref['path'], '-receipt', str(receipt), *extras], deadline, stdin=stdin, host=phase == 'execute-admitted')

    def _read_db(self):
        db = sqlite3.connect((Path(self.bootstrap['data_root']) / 'researchos.sqlite').as_uri() + '?mode=ro', uri=True, timeout=1)
        db.execute('PRAGMA query_only=ON')
        return db

    def prepare(self):
        require(self.state == 'BOOTSTRAP_VERIFIED' and self.input['mode'] == 'MODEL_TRIAL', 'prepare phase order/mode')
        # External caller authority is distinct from the independently reviewed Source.
        auth = read_json(self.input['root_execution_authority_ref'])
        require(auth.get('schema') == 'researchos.root-sdk-coordinator-execution-authority.v1' and auth.get('actor_id') == 'codex:/root' and auth.get('approved') is True and auth.get('mode') == 'MODEL_TRIAL' and auth.get('coordinator_source_ref') == self.input['coordinator_source_ref'] and auth.get('input_basis_sha256') == input_basis_hash(self.input) and auth.get('maximum_provider_requests') == 3 and auth.get('requested_output_tokens_total') == 8192 and auth.get('total_wall_seconds') == 300, 'exact Root execution authority required')
        self._guard([self.input['root_execution_authority_ref'], self.input['host_seed_ref'], self.input['intake_review_ref'], self.input['public_route_manifest_ref']])
        seed = read_json(self.input['host_seed_ref'])
        pairs = {'project_id': 'project_id', 'draft_goal_id': 'goal_id', 'workspace_ref': 'workspace_ref', 'workspace_dir': 'workspace', 'data_root': 'data_root', 'discovery_file': 'discovery_file', 'cli_config_file': 'cli_config_file'}
        path_keys = {'workspace_dir', 'data_root', 'discovery_file', 'cli_config_file'}
        require(all((Path(seed[k]) == Path(self.bootstrap[v])) if k in path_keys else (type(seed[k]) is type(self.bootstrap[v]) and seed[k] == self.bootstrap[v]) for k, v in pairs.items()), 'Host seed is not the consumed bootstrap')
        require(Path(seed['repo_root']) == ROOT and seed['witness_sha256'] == self.bootstrap['workspace_witness_ref']['sha256'] and type(seed['witness_bytes']) is int and seed['witness_bytes'] == self.bootstrap['workspace_witness_ref']['bytes'], 'Host seed workspace evidence differs')
        for key, pathkey, hashkey in (('node_binary', 'node_executable', 'node_sha256'), ('mu_bundle', 'bundle_file', 'bundle_sha256')):
            require(Path(seed[pathkey]) == Path(self.fixed[key]['path']) and seed[hashkey] == self.fixed[key]['sha256'], 'Host executable Source differs')
        self._guard([self.bootstrap['workspace_witness_ref'], pin(seed['profile_file'])])
        require(pin(seed['profile_file'])['sha256'] == seed['profile_sha256'], 'profile seed changed')
        self.host_seed_ref = self.input['host_seed_ref']
        self.state = 'PREPARE_ATTEMPTED'
        receipt = self.output / 'host.prepare.json'
        self._host_phase('prepare', receipt, time.monotonic()+90)
        self.prepared = read_json(pin(receipt))
        require(self.prepared.get('status') == 'PREPARED' and self.prepared.get('provider_requests') == 0 and self.prepared['project_id'] == self.bootstrap['project_id'], 'Host preparation result mismatch')
        # Export the exact sealed uploaded_content bytes. A profile template is insufficient.
        with self._read_db() as db:
            rows = db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", (self.bootstrap['project_id'], self.prepared['profile_artifact_id'])).fetchall()
            require(len(rows) == 1, 'sealed profile Artifact missing')
            artifact = json.loads(rows[0][0])
            require(artifact['content_hash'] == self.prepared['profile_hash'] and artifact.get('sealed_at') is not None and artifact.get('validity') == 'CURRENT', 'profile Artifact seal differs')
            content = db.execute('SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1', (self.bootstrap['project_id'], artifact['storage_key'])).fetchall()
            require(len(content) == 1, 'sealed profile bytes missing')
            raw = content[0][0]
            require('sha256:' + hashlib.sha256(raw).hexdigest() == self.prepared['profile_hash'], 'sealed profile hash differs')
            self.profile_entity_ref = self.engine.exact_artifact_ref(db, self.bootstrap['project_id'], artifact['id'])
        profile = self.output / 'runtime-profile.actual-sealed.json'
        with profile.open('xb') as target:
            target.write(raw)
        self.profile_ref = pin(profile)
        self._guard([self.profile_ref, pin(receipt)])
        self.state = 'PREPARED'

    def _wait_receipt(self, path):
        while time.monotonic() < self.deadline:
            if Path(path).exists():
                raw = Path(path).read_bytes()
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass  # one writer may still be completing this exclusive file
            require(self.host_thread is not None and self.host_thread.is_alive(), 'Host ended before required receipt')
            self.done.wait(0.025)
        raise RuntimeError('whole trial deadline expired waiting for Host')

    def start_trial(self):
        require(self.state == 'PREPARED', 'trial already attempted or not prepared')
        self.state = 'ADMISSION_ATTEMPTED'
        self.started = time.monotonic()
        start_utc = datetime.now(timezone.utc)
        self.started_utc = utc_text(start_utc)
        self.deadline_utc = utc_text(start_utc + timedelta(seconds=300))
        self.deadline = self.started + 300
        put(self.output / 'whole-trial-clock.json', {'started_monotonic': self.started, 'absolute_deadline_monotonic': self.deadline, 'started_utc': self.started_utc, 'deadline_utc': self.deadline_utc, 'clock_reset_permitted': False})
        admitted_path = self.output / 'host.admitted.json'
        self._host_phase('admit-only', admitted_path, self.deadline, ('-started-utc', self.started_utc))
        self.admitted = read_json(pin(admitted_path))
        require(self.admitted.get('status') == 'ADMITTED_NOT_DISPATCHED' and self.admitted.get('provider_requests') == 0 and self.admitted.get('root_started_utc') == self.started_utc and self.admitted['project_id'] == self.bootstrap['project_id'] and self.admitted['runtime_id'] == self.prepared['runtime_id'] and self.admitted['profile_hash'] == self.prepared['profile_hash'], 'admission tuple differs')
        self._guard([pin(admitted_path)])
        ready_path = self.output / 'host.ready.json'
        rd, wr = os.pipe()
        self.pipe_read = os.fdopen(rd, 'rb', buffering=0)
        self.pipe_write = os.fdopen(wr, 'wb', buffering=0)
        def host_main():
            try:
                self._host_phase('execute-admitted', self.output / 'host.terminal.json', self.deadline, ('-ready-receipt', str(ready_path)), self.pipe_read)
            except BaseException as exc:
                self.error = self.error or type(exc).__name__ + ': ' + str(exc)
        self.host_thread = threading.Thread(target=host_main, name='root-owned-trusted-host', daemon=False)
        self.host_thread.start()
        self.ready = self._wait_receipt(ready_path)
        require(self.ready.get('status') == 'READY_ADMISSION_PENDING' and self.ready.get('provider_requests') == 0 and self.ready['root_started_utc'] == self.started_utc, 'Host READY not provider-free current admission')
        for key in ('project_id', 'runtime_id', 'qualification_task_id', 'qualification_run_id', 'qualification_epoch', 'profile_hash', 'host_instance_id'):
            require(type(self.ready[key]) is type(self.admitted[key]) and self.ready[key] == self.admitted[key], 'Host READY admission identity differs')
        require(self.ready['host_pid'] == self.jobs['host-execute-admitted']['identity']['runner_pid'], 'actual Host PID differs')
        self.ready_ref = pin(ready_path)
        self.state = 'READY_ADMISSION_PENDING'

    def issue_go(self):
        require(self.state == 'READY_ADMISSION_PENDING' and not self.go_sent, 'GO already attempted')
        self.state = 'GO_ATTEMPTED'
        discovery_ref = pin(self.bootstrap['discovery_file'])
        discovery = read_json(discovery_ref)
        require(discovery.get('pid') == self.ready['host_pid'] and discovery.get('url') == self.ready['host_url'] and discovery.get('host_instance_id') == self.ready['host_instance_id'] and Path(discovery['data_dir']) == Path(self.bootstrap['data_root']), 'actual discovery does not bind READY Host')
        grant_ref = put(self.output / 'root-host-go.json', {'schema': 'researchos.mu-trial-root-go.v1', 'actor_id': 'codex:/root', 'approved': True, 'qualification_run_id': self.admitted['qualification_run_id'], 'started_utc': self.started_utc, 'execution_authority_ref': self.input['root_execution_authority_ref'], 'coordinator_source_ref': self.input['coordinator_source_ref'], 'maximum_provider_requests': 3, 'requested_output_tokens_total': 8192})
        once_ref = put(self.output / 'host-go.once.json', {'schema': 'researchos.mu-trial-once.v1', 'qualification_run_id': self.admitted['qualification_run_id'], 'state': 'CONSUMED_FOR_HOST_GO', 'owner_pid': self.owner_pid})
        a = {'schema': 'researchos.trusted-qualification-go.v1', 'started_utc': self.started_utc, 'draft_goal_id': self.bootstrap['goal_id'], 'maximum_provider_requests': 3, 'qualification_requests': 1, 'ordinary_requests': 2}
        for key in ('project_id', 'runtime_id', 'qualification_task_id', 'qualification_run_id', 'qualification_epoch', 'profile_hash', 'host_instance_id', 'host_pid', 'host_url'):
            a[key] = self.ready[key]
        a.update({'ready_receipt': self.ready_ref, 'discovery': discovery_ref, 'private_coordinator': self.ready['private_coordinator'], 'root_grant': grant_ref, 'once_marker': once_ref, 'outer_job_contract': self.host_contract_ref, 'host_job_probe': self.host_probe_ref})
        self._guard([a[k] for k in ('ready_receipt', 'discovery', 'private_coordinator', 'root_grant', 'once_marker', 'outer_job_contract', 'host_job_probe')])
        authority_ref = put(self.output / 'host-go.authority.json', a)
        self._guard([authority_ref])
        require(time.monotonic() < self.deadline and self.host_thread.is_alive(), 'Host GO deadline or liveness failed')
        frame = (json.dumps({'go': True, 'authority_file': authority_ref['path']})+'\n').encode()
        self.go_sent = True  # ambiguous pipe writes never permit another GO
        require(self.pipe_write.write(frame) == len(frame), 'incomplete Host GO write')
        self.pipe_write.flush()  # retained until C7 and Host cleanup
        ordinary = self._wait_receipt(self.output / 'host.ready.ordinary.json')
        require(ordinary.get('status') == 'READY_FOR_ORDINARY' and ordinary.get('qualification_run_id') == self.admitted['qualification_run_id'] and ordinary.get('host_pid') == self.ready['host_pid'] and ordinary.get('project_id') == self.bootstrap['project_id'] and ordinary.get('runtime_id') == self.prepared['runtime_id'] and ordinary.get('root_started_utc') == self.started_utc, 'actual qualification/ordinary readiness mismatch')
        self.state = 'READY_FOR_ORDINARY'

    def execute_c7(self):
        require(self.state == 'READY_FOR_ORDINARY', 'C7 cannot start before actual qualification')
        self.state = 'C7_ATTEMPTED'
        with self._read_db() as db:
            marker = db.execute('SELECT owner_root FROM runtime_qualification_runs WHERE project=? AND run=?', (self.bootstrap['project_id'], self.admitted['qualification_run_id'])).fetchall()
            require(len(marker) == 1 and marker[0][0], 'qualification owner marker unavailable')
        doc = {'schema': 'researchos.mu-sdk-trial.executable-input.v1', 'source_commit': SOURCE_COMMIT, 'phase': 'execute', 'run_uuid': self.run_uuid, 'maximum_provider_requests': 3, 'qualification_requests': 1, 'ordinary_requests': 2, 'requested_output_tokens_total': 8192, 'total_wall_seconds': 300, 'cli_binary': self.fixed['cli_binary'], 'intake_review': self.input['intake_review_ref'], 'public_route_manifest': self.input['public_route_manifest_ref'], 'runtime_profile': self.profile_ref, 'cancel_fixture_receipt': self.fixed['cancel_receipt'], 'bootstrap_receipt': self.input['bootstrap_result_ref'], 'credential_revision': self.engine.CREDENTIAL_REF, 'repository_root': str(ROOT), 'outcome_dir': str(self.output / 'c7-outcomes'), 'once_path': str(self.output / 'c7-execute.once.json'), 'root_registration_started_at_utc': self.started_utc, 'runtime_id': self.admitted['runtime_id'], 'qualification_task_id': self.admitted['qualification_task_id'], 'qualification_run_id': self.admitted['qualification_run_id'], 'qualification_epoch': self.admitted['qualification_epoch'], 'qualification_owner_root': marker[0][0], 'qualification_profile_hash': self.admitted['profile_hash'], 'profile_entity_ref': self.profile_entity_ref, 'prompt': self.input['ordinary_prompt']}
        for key in ('data_root', 'workspace', 'discovery_file', 'cli_config_file', 'project_id', 'goal_id', 'config_revision', 'workspace_witness'):
            doc[key] = self.bootstrap[key]
        discovery, config = self.engine.current_consumed_states(doc)
        doc['initial_discovery_state'], doc['initial_config_state'] = discovery[0], config[0]
        seed = {'phase_ready_for_execution': True, 'input_doc': doc, 'phase_dir': str(self.output / 'c7-phase'), 'started_monotonic': self.started, 'absolute_deadline_monotonic': self.deadline, 'runner_source': self.fixed['runner'], 'observer_source': self.fixed['observer'], 'python_binary': self.fixed['python_binary'], 'controller_source_review': self.fixed['controller_review'], 'public_environment': self.env, 'parent_checkpoint': self.input['parent_checkpoint_ref'], 'parent_ownership': self.input['parent_ownership_ref']}
        self.c7_run_uuid = self.run_uuid
        self.c7_result_ref = self.controller.launch_reviewed_phase(seed, self.c7_owner)
        self.state = 'C7_RETURNED'

    def finalize(self):
        # Close stdin first: Host EOF cancels any pending native/provider work.
        if self.pipe_write is not None and not self.pipe_write.closed:
            self.pipe_write.close()
        if self.host_thread is not None and self.host_thread.ident is not None:
            self.host_thread.join(5)
            if self.host_thread.is_alive():
                record = self.jobs.get('host-execute-admitted', {})
                watchdog = record.get('watchdog')
                if watchdog is not None and watchdog.handle is not None:
                    ok = bool(watchdog.terminate(watchdog.handle, 0xE0000509))
                    record['root_teardown'] = {'TerminateJobObject_return': ok, 'at_monotonic': time.monotonic()}
                self.host_thread.join(5)
        safe = self.host_thread is None or not self.host_thread.is_alive()
        if self.pipe_read is not None and safe and not self.pipe_read.closed:
            self.pipe_read.close()
        if self.controller is not None and self.c7_run_uuid is not None:
            safe = safe and self.controller.source_retention_status(self.c7_run_uuid, self.c7_owner) is None
        for record in self.jobs.values():
            if not record['native_invoked']:
                continue
            closed = native_closed(record['result'])
            proof = None
            if record['producer'] is not None:
                start = time.monotonic()
                try:
                    proof = record['producer'].observe_current()
                except BaseException as exc:
                    proof = {'errors': [type(exc).__name__]}
                closed = closed and matching_idle_proof(proof, record['identity'], start, time.monotonic())
            else:
                closed = False
            wd = pc = None
            if closed and record['watchdog'] is not None:
                wd = record['watchdog'].stop_and_close()
                closed = wd.get('duplicate_handle_closed') is True and wd.get('errors') == []
            if closed:
                pc = record['producer'].close()
                closed = pc.get('closed') is True and pc.get('errors') == []
            record['cleanup'] = {'proof': proof, 'watchdog': wd, 'producer': pc, 'closed': closed}
            safe = safe and closed
        guard_cleanup = []
        if safe:
            for guard in reversed(self.guards):
                obs = guard.close()
                guard_cleanup.append(obs)
                safe = safe and obs.get('closed') is True and obs.get('retained_handles_count') == 0 and obs.get('errors') == []
        self.state = ('CLOSED_PENDING_INDEPENDENT_REVIEW' if self.error is None else 'FAILED_EXECUTION_CLOSED') if safe else 'RETAINED_UNCONFIRMED'
        report = {'state': self.state, 'actual_parent_pid': self.owner_pid, 'error': self.error, 'go_sent': self.go_sent, 'jobs': [{'label': r['label'], 'cleanup': r['cleanup'], 'root_teardown': r.get('root_teardown')} for r in self.jobs.values()], 'source_guard_cleanup': guard_cleanup, 'automatic_retry': False, 'provider_requests': 0 if not self.go_sent else None, 'provider_count_requires_v9_original_evidence': self.go_sent, 'C7_actual_lifecycle_proven': False, 'formal_acceptance': False, 'same_parent_must_remain_alive': not safe}
        if hasattr(self, 'output') and self.output.is_dir():
            put(self.output / 'root-coordinator.lifecycle.json', report)
        self.result = report
        if safe:
            setattr(sys, ANCHOR, None)
        return report

    def run(self):
        self.run_uuid = uuid.uuid4().hex
        try:
            self.open()
            if self.input['mode'] == 'MODEL_TRIAL':
                self.prepare()
                self.start_trial()
                self.issue_go()
                self.execute_c7()
        except BaseException as exc:
            self.error = type(exc).__name__ + ': ' + str(exc)
        try:
            return self.finalize()
        except BaseException as exc:
            self.state = 'RETAINED_UNCONFIRMED'
            self.error = self.error or type(exc).__name__ + ': ' + str(exc)
            self.result = {'state': self.state, 'actual_parent_pid': self.owner_pid, 'error': self.error, 'same_parent_must_remain_alive': True, 'automatic_retry': False, 'formal_acceptance': False}
            return self.result

    def retain_parent(self):
        """Explicit residency loop only after uncertain cleanup; no dispatch retries."""
        require(os.getpid() == self.owner_pid and getattr(sys, ANCHOR, None) is self and self.state == 'RETAINED_UNCONFIRMED', 'same retained parent required')
        while self.state == 'RETAINED_UNCONFIRMED':
            self.done.wait(1)

def run_resident(input_ref, independent_source_review_ref):
    coordinator = RootResidentCoordinator(input_ref, independent_source_review_ref)
    result = coordinator.run()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if result['state'] == 'RETAINED_UNCONFIRMED':
        coordinator.retain_parent()
    return result
