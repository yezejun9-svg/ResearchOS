import hashlib, json, pathlib, subprocess
out=pathlib.Path(__file__).resolve().parent
root=out.parents[6]
main=pathlib.Path('D:/作品集/ResearchOS/research-os')
scope=main/'execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-test-and-p12-resource-r276/test_scope_registration.json'
assert hashlib.sha256(scope.read_bytes()).hexdigest()=='f3f74be44cfe1a515a6c1f31c63f22aefb45cba04c42c0f055cd3125f3ed7338'
(out/'scope.original.json').write_bytes(scope.read_bytes())
p='internal/domain/backup_command_queue_test.go'
r=subprocess.run(['git','show','125ea34ca0878f18c4dce47f9259ab5e9e77c2eb:'+p],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert r.returncode==0 and hashlib.sha256(r.stdout).hexdigest()=='97746789f50114faf6917783f02d9e0cec49f7d4c2cfcc551217e2052c0e838d'
(out/'source.before.go.txt').write_bytes(r.stdout)
(out/'source.after.go.txt').write_bytes((root/p).read_bytes())
original=r.stdout.decode('utf8').replace('\r\n','\n')
current=(root/p).read_text('utf8')
prefix='func TestClientQueueFreshNumberedSchema'
suffix='func TestClientQueueBackupAllPhasesAndPendingControl'
assert original.split(prefix)[0]==current.split(prefix)[0]
assert original.split(suffix)[1]==current.split(suffix)[1]
changed=subprocess.run(['git','diff','--name-only'],cwd=root,stdout=subprocess.PIPE,check=True).stdout.decode().splitlines()
assert changed==[p], changed
checks=dict(source_path=p,before_sha256=hashlib.sha256(r.stdout).hexdigest(),after_sha256=hashlib.sha256((root/p).read_bytes()).hexdigest(),outside_allowed_functions_bytes_unchanged=True,only_changed_tracked_path=changed,production10_and_foundation5_frozen=True,prior_candidate='125ea34ca0878f18c4dce47f9259ab5e9e77c2eb')
(out/'preflight.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf8')
print(json.dumps(checks))
