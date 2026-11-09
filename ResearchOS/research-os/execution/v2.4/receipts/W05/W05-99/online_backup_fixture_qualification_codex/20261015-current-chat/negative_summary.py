import hashlib
import json
from pathlib import Path

e = Path(__file__).resolve().parent
task = Path('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp')
before = json.loads((e/'q02-package-before-refusal.stdout.raw').read_text(encoding='utf-8'))
after = json.loads((e/'q02-package-after-refusal.stdout.raw').read_text(encoding='utf-8'))
def exit_code(name):
    return json.loads((e/(name+'.exit.json')).read_text(encoding='utf-8'))['native_exit']
def stderr(name):
    return (e/(name+'.stderr.raw')).read_text(encoding='utf-8').strip()
out = {'existing_destination_refused':exit_code('q02-refuse-existing-dest') == 1 and 'DESTINATION_EXISTS' in stderr('q02-refuse-existing-dest'),
       'original_package_files_unchanged':before['entries'] == after['entries'],
       'wrong_key_refused':exit_code('q02-wrong-key-restore') == 1 and 'BACKUP_MANIFEST_INVALID' in stderr('q02-wrong-key-restore'),
       'wrong_key_published_root_absent':not (task/'fixture/Q02/wrong-key-restored').exists(),
       'changed_root_identity_refused':exit_code('q02-refuse-changed-workspace') == 1 and 'BACKUP_WORKSPACE_PIN_CHANGED' in stderr('q02-refuse-changed-workspace'),
       'changed_identity_package_absent':not (task/'fixture/Q02/invalid-identity-backup').exists()}
for prefix in ('q01-r2','q02'):
    b = (e/(prefix+'-acl-before.stdout.raw')).read_bytes()
    a = (e/(prefix+'-acl-after.stdout.raw')).read_bytes()
    out[prefix+'_native_acl_snapshot_equal'] = b == a
    out[prefix+'_native_acl_before_sha256'] = hashlib.sha256(b).hexdigest()
    out[prefix+'_native_acl_after_sha256'] = hashlib.sha256(a).hexdigest()
print(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':')))
