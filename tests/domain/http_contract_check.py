"""Independent real HTTP checks against frozen W03 contracts; synthetic local data only."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
IDS, TRACE = [], []


def main():
    if os.getenv('RESEARCHOS_TASK_ID', 'W03') != 'W03' or os.getenv('RESEARCHOS_CHECK_ID', '') not in ('', 'W03-G02') or os.getenv('RESEARCHOS_CASE_ID'):
        raise NotImplementedError('unbound task/check/case selection')
    binary = ROOT / '.local/bin/researchos-control.exe'
    assert binary.is_file(), 'Build the current control binary first'
    with tempfile.TemporaryDirectory(prefix='researchos-http-') as directory:
        data = Path(directory)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        env = os.environ.copy()
        env.update(RESEARCHOS_DATA_DIR=str(data / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'),
                   RESEARCHOS_LISTEN=f'127.0.0.1:{port}')
        credential = data / 'private/owner.json'
        credential.parent.mkdir()
        bootstrap = subprocess.run([str(binary), '-bootstrap-owner', '-credential-file', str(credential)],
                                   cwd=ROOT, env=env, capture_output=True, timeout=15)
        assert bootstrap.returncode == 0, 'Owner bootstrap failed'
        token = json.loads(credential.read_text(encoding='utf-8'))['token']
        owner_id = json.loads(credential.read_text(encoding='utf-8'))['principal_id']
        tokens = {'owner': token}
        assert token and token.encode() not in bootstrap.stdout + bootstrap.stderr, 'Bootstrap exposed token'
        process = None
        helper_built = False

        def start():
            proc = subprocess.Popen([str(binary)], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    assert proc.poll() is None, 'Control service exited during startup'
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/healthz', timeout=1) as response:
                            if response.status == 200:
                                return proc
                    except URLError:
                        time.sleep(.1)
                raise AssertionError('Health endpoint did not become ready')
            except BaseException:
                stop(proc)
                raise

        def stop(proc):
            proc.terminate()
            try:
                out, err = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err = proc.communicate(timeout=5)
            assert all(value.encode() not in out + err for value in tokens.values()), 'Service log exposed token'

        def request(method, path, body=None, *, key=None, match=None, auth=True, raw=None, principal='owner'):
            headers = {'Content-Type': 'application/json'}
            if auth:
                headers['Authorization'] = 'Bearer ' + tokens[principal]
            if key is not None:
                headers['Idempotency-Key'] = key
            if match is not None:
                headers['If-Match'] = match
            payload = raw if raw is not None else (json.dumps(body, ensure_ascii=False).encode() if body is not None else None)
            req = Request(f'http://127.0.0.1:{port}' + path, data=payload, headers=headers, method=method)
            try:
                response = urlopen(req, timeout=5)
            except HTTPError as exc:
                response = exc
            with response:
                code = response.status
                encoded = response.read()
                value = json.loads(encoded)
                etag = response.headers.get('ETag')
                replayed = response.headers.get('Idempotency-Replayed')
            assert all(value.encode() not in encoded for value in tokens.values()), 'Response exposed token'
            if code >= 400:
                assert set(value) == {'code', 'message', 'correlation_id', 'retryable', 'current_revision', 'details'}, 'Error contract shape'
            TRACE.append({'method': method, 'path': path, 'status': code, 'etag': etag,
                          'replayed': replayed, 'body': value})
            return code, value, etag, replayed

        def provision(action, principal_id, project_id=None, roles=None):
            nonlocal helper_built
            helper = data / 'researchos-domain-fixture.exe'
            if not helper_built:
                built = subprocess.run([os.environ['RESEARCHOS_GO'], 'build', '-o', str(helper), './tests/domain/harness'],
                                       cwd=ROOT, env=env, capture_output=True, timeout=120)
                assert built.returncode == 0, 'Offline fixture helper build failed'
                helper_built = True
            destination = credential.parent / (principal_id + '.json')
            config = dict(Action=action, DataDir=str(data / 'data'), PrincipalID=principal_id,
                          ProjectID=project_id, Roles=roles, CredentialFile=str(destination), Restricted=False)
            config_path = data / 'fixture-input.json'
            config_path.write_text(json.dumps(config), encoding='utf-8')
            result = subprocess.run([str(helper), str(config_path)], cwd=ROOT, env=env, capture_output=True, timeout=15)
            assert result.returncode == 0, 'Offline fixture provisioning failed'
            if action == 'provision':
                tokens[principal_id] = json.loads(destination.read_text(encoding='utf-8'))['token']
            assert all(value.encode() not in result.stdout + result.stderr for value in tokens.values()), 'Fixture helper exposed token'

        def create_project(name):
            body = {'name': name, 'intent': 'W03 isolated HTTP fixture', 'facts': [],
                    'accepted_scope': ['Synthetic domain verification'], 'constraints': [],
                    'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []}
            key = str(uuid.uuid4())
            result = request('POST', '/v1/projects', body, key=key)
            assert result[0] == 201, 'Project creation failed'
            replay = request('POST', '/v1/projects', body, key=key)
            assert replay[:3] == result[:3] and replay[3] == 'true', 'Project create replay changed response'
            return result[1]['project_id'], body

        try:
            process = start()
            assert request('GET', '/v1/projects', auth=False)[0] == 401
            IDS.append('W03-HTTP-AUTHENTICATION')
            project, project_body = create_project('同名隔离项目')
            other, _ = create_project('同名隔离项目')
            assert project != other
            IDS.append('W03-HTTP-PROJECT-IDENTITY-REPLAY')
            assert request('POST', '/v1/projects', project_body)[0] == 428
            short = request('POST', '/v1/projects', project_body, key='short')
            assert short[0] == 400 and short[1]['code'] == 'INVALID_REQUEST'
            long_key = request('POST', '/v1/projects', project_body, key='a' * 161)
            assert long_key[0] == 400 and long_key[1]['code'] == 'INVALID_REQUEST'
            IDS.append('W03-HTTP-IDEMPOTENCY-REQUIRED')
            unknown = dict(project_body, caller_role='OWNER')
            assert request('POST', '/v1/projects', unknown, key=str(uuid.uuid4()))[0] == 400
            duplicate = b'{"name":"duplicate",' + json.dumps(project_body, ensure_ascii=False).encode()[1:]
            assert request('POST', '/v1/projects', key=str(uuid.uuid4()), raw=duplicate)[0] == 400
            assert {item['project_id'] for item in request('GET', '/v1/projects')[1]['items']} == {project, other}, 'Rejected create left a project'
            IDS.append('W03-HTTP-STRICT-JSON')
            base = f'/v1/projects/{project}'
            state = request('GET', base + '/state')
            assert state[0] == 200 and state[2] == f'"r{state[1]["revision"]}"'
            before = state[1]
            requirement = {'requirement_key': 'HTTP-R1', 'text': 'Independent API behavior',
                           'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'Synthetic test',
                           'supersedes_id': None, 'acceptance_check_ids': []}
            path = base + '/requirements'
            assert request('POST', path, requirement, key=str(uuid.uuid4()))[0] == 428
            stale = request('POST', path, requirement, key=str(uuid.uuid4()), match='"r999999"')
            assert stale[0] == 412 and stale[2] == state[2] and stale[1]['current_revision'] == before['revision']
            assert request('GET', base + '/state')[1] == before, 'Rejected write mutated state'
            IDS.append('W03-HTTP-PRECONDITIONS-ATOMIC-FAILURE')
            creation_key = str(uuid.uuid4())
            created = request('POST', path, requirement, key=creation_key, match=state[2])
            assert created[0] == 201
            action = request('POST', path + '/' + created[1]['id'] + '/actions',
                             {'action': 'ACCEPT', 'reason': 'Owner accepts fixture requirement', 'source_validation_refs': []},
                             key=str(uuid.uuid4()), match=created[2])
            assert action[0] == 200 and action[1]['status'] == 'ACCEPTED'
            replay = request('POST', path, requirement, key=creation_key, match=state[2])
            assert replay[:3] == created[:3] and replay[3] == 'true', 'Replay re-executed after revision change'
            current = request('GET', base + '/state')
            assert request('POST', path, requirement, key=creation_key, match=current[2])[0] == 409
            IDS.append('W03-HTTP-REPLAY-BEFORE-REVISION')
            rejected = request('POST', path + '/' + created[1]['id'] + '/actions',
                               {'action': 'ACCEPT', 'reason': 'Repeat terminal transition', 'source_validation_refs': []},
                               key=str(uuid.uuid4()), match=action[2])
            assert rejected[0] == 409, 'Illegal state transition succeeded'
            IDS.append('W03-HTTP-STATE-REFUSAL')
            concurrent_state = request('GET', base + '/state')
            before_items = request('GET', path)[1]['items']

            def mutate(number):
                item = dict(requirement, requirement_key=f'HTTP-RACE-{number}', text=f'Concurrent writer {number}')
                return request('POST', path, item, key=str(uuid.uuid4()), match=concurrent_state[2])

            with ThreadPoolExecutor(max_workers=2) as pool:
                race = list(pool.map(mutate, [1, 2]))
            assert sorted(item[0] for item in race) == [201, 412], 'Concurrent stale update was not rejected'
            after_race = request('GET', base + '/state')[1]
            assert after_race['revision'] > concurrent_state[1]['revision']
            assert after_race['event_sequence'] > concurrent_state[1]['event_sequence']
            after_items = request('GET', path)[1]['items']
            assert len(after_items) == len(before_items) + 1, 'Rejected writer left a partial resource'
            events = request('GET', base + '/events?after_sequence=' + str(concurrent_state[1]['event_sequence']))
            assert events[0] == 200
            committed = events[1]['items']
            assert [item['sequence'] for item in committed] == list(range(concurrent_state[1]['event_sequence'] + 1, after_race['event_sequence'] + 1))
            assert len({item['id'] for item in committed}) == len(committed)
            winner = next(item[1]['id'] for item in race if item[0] == 201)
            assert any(item['aggregate_ref']['id'] in {winner, after_race['id']} for item in committed)
            IDS.append('W03-HTTP-CONCURRENT-REVISION-EVENT')
            assert request('GET', f'/v1/projects/{other}/requirements/{created[1]["id"]}')[0] == 404
            other_state = request('GET', f'/v1/projects/{other}/state')
            foreign = dict(requirement, source_refs=[{'entity_type': 'Requirement', 'id': created[1]['id'],
                                                    'revision': action[1]['revision'], 'content_hash': None}])
            cross = request('POST', f'/v1/projects/{other}/requirements', foreign,
                            key=str(uuid.uuid4()), match=other_state[2])
            assert cross[0] in (400, 404, 409, 422), 'Cross-project reference accepted'
            assert request('GET', f'/v1/projects/{other}/state')[1] == other_state[1]
            positive = dict(foreign, requirement_key='HTTP-SAME-PROJECT-REFERENCE')
            assert request('POST', path, positive, key=str(uuid.uuid4()), match=request('GET', base + '/state')[2])[0] == 201
            after_race = request('GET', base + '/state')[1]
            IDS.append('W03-HTTP-CROSS-PROJECT-REFERENCE')
            stop(process)
            process = None
            process = start()
            replay = request('POST', path, requirement, key=creation_key, match=state[2])
            assert replay[:3] == created[:3] and replay[3] == 'true'
            assert request('GET', base + '/state')[1]['event_sequence'] == after_race['event_sequence']
            IDS.append('W03-HTTP-PERSISTENT-IDEMPOTENCY')
            provision('provision', 'fixture-reader', project, ['READER'])
            visible = request('GET', '/v1/projects', principal='fixture-reader')
            assert visible[0] == 200 and {p['project_id'] for p in visible[1]['items']} == {project}
            assert request('GET', f'/v1/projects/{other}/profile', principal='fixture-reader')[0] == 404
            assert request('POST', path, requirement, key=str(uuid.uuid4()), match=current[2], principal='fixture-reader')[0] == 403
            IDS.append('W03-HTTP-CURRENT-GRANT-AND-ROLE')
            provision('revoke', owner_id)
            assert request('POST', path, requirement, key=creation_key, match=state[2])[0] == 401
            IDS.append('W03-HTTP-REVOKED-CACHED-REPLAY')
        finally:
            if process is not None:
                stop(process)


if __name__ == '__main__':
    try:
        main()
        status, error = 'PASS', None
    except Exception as exc:
        status, error = 'FAIL', f'{type(exc).__name__}: {exc}'
    print(json.dumps({'status': status, 'assertions': len(IDS), 'assertion_ids': IDS,
                      'scope': 'FIXTURE_REAL_LOCAL_HTTP', 'trace': TRACE, 'error': error}, ensure_ascii=False))
    raise SystemExit(0 if status == 'PASS' and IDS else 1)
