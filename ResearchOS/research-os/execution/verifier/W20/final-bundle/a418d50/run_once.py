"""Run the existing bounded release fixture once; persist raw/OS exit before parsing."""
import datetime
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
SOURCE = 'a418d503f29646f62010905f9dc9338630aa0108'
EXPECTED_ZIP = 'dc90caedd5287bcd718c76bc8e0e2189cf3b33c92a547b6d9fe71d3564f8a193'
ARCHIVES = [ROOT / ('.local/researchos-development-a418d50-' + x + '.zip') for x in 'ab']
def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
if (OUT / 'execution-started.json').exists():
    raise RuntimeError('One-shot fixture already started; only postprocess saved output, never rerun')
locked = load(ROOT / 'execution/toolchains/locked.json')
python = Path(locked['tools']['python']['path'])
assert sha(python.read_bytes()) == locked['tools']['python']['sha256']
tracked = set(git('ls-files', '-z').decode().split('\0'))
with zipfile.ZipFile(ARCHIVES[0]) as za, zipfile.ZipFile(ARCHIVES[1]) as zb:
    ma, mb = json.loads(za.read('release-manifest.json')), json.loads(zb.read('release-manifest.json'))
    assert ma == mb and ma['source_commit'] == SOURCE
    names = za.namelist()
    assert names == zb.namelist() and len(names) == 514
    assert all(za.read(n) == zb.read(n) for n in names)
    assert all(sha(za.read(x['path'])) == x['sha256'] and len(za.read(x['path'])) == x['size'] for x in ma['files'])
    source_paths = sorted((set(names) & tracked) | {'tests/release/check.py','docs/handoff/current-construction.md','execution/toolchains/locked.json'})
    source_commit_matches = {p: (ROOT / p).read_bytes() == git('show', SOURCE + ':' + p) for p in source_paths}
    assert all(source_commit_matches.values())
    outcome_matches = za.read('release/outcome_report.json') == (ROOT / 'release/outcome_report.json').read_bytes()
    assert outcome_matches
    zip_review = {'source_commit':SOURCE,'archive_entries':len(names),'manifest_files':len(ma['files']),
                  'identical_archive_bytes':ARCHIVES[0].read_bytes()==ARCHIVES[1].read_bytes(),
                  'every_entry_identical':True,'all_manifest_file_hashes_valid':True,
                  'packaged_outcome_matches_source':outcome_matches,
                  'handoff_document_bundled':'docs/handoff/current-construction.md' in names,
                  'sbom_license_gaps':ma['sbom']['license_gaps'],
                  'bin_control_sha256':sha(za.read('bin/control.exe')),
                  'source_commit_matches':source_commit_matches}
save('archive-audit.json', zip_review)
integration = load(ROOT / 'execution/receipts/W08/manual-disposition-root/57ef089/root-integration.json')
c05 = []
for x in integration['files']:
    raw = (ROOT / x['path']).read_bytes()
    source = not x['path'].startswith('execution/')
    c05.append({'path':x['path'],'expected_sha256':x['sha256'],'actual_sha256':sha(raw),
                'size_matches':len(raw)==x['bytes'],'is_source':source,
                'package_source_commit_match':raw==git('show', SOURCE+':'+x['path']) if source else None})
assert all(x['actual_sha256']==x['expected_sha256'] and x['size_matches'] and
           (not x['is_source'] or x['package_source_commit_match']) for x in c05)
review_path = ROOT / integration['independent_review']
assert sha(review_path.read_bytes()) == '84f6c7532d14e22923be37b45c3442fae07b6d3dad416661cff5b6560e5bc5a0'
save('c05-package-binding.json',{'source_commit':SOURCE,'source_files':12,'raw_files':9,'all_match':True,'files':c05,
     'independent_review':integration['independent_review'],'review_sha256':sha(review_path.read_bytes()),
     'limits':integration['limits'],'new_c05_test_execution':False})
tools = {k:Path(v['path']) for k,v in locked['tools'].items() if 'path' in v}
tools['powershell'] = Path(shutil.which('powershell.exe'))
def snapshot():
    with zipfile.ZipFile(ARCHIVES[0]) as z:
        manifest_raw=z.read('release-manifest.json')
        current_manifest=json.loads(manifest_raw)
    return {'git_head':git('rev-parse','HEAD').decode().strip(),
            'source':{p:sha((ROOT/p).read_bytes()) for p in source_paths},
            'tools':{k:{'path':str(p),'sha256':sha(p.read_bytes())} for k,p in tools.items()},
            'archives':{str(p):sha(p.read_bytes()) for p in ARCHIVES},
            'archive_manifest_sha256':sha(manifest_raw),
            'sbom_canonical_sha256':sha(json.dumps(current_manifest['sbom'],sort_keys=True,separators=(',',':')).encode()),
            'check_sha256':sha((ROOT/'tests/release/check.py').read_bytes())}
before=snapshot()
assert before['git_head']==SOURCE and set(before['archives'].values())=={EXPECTED_ZIP}
save('before.json',before)
argv=[str(python),'-B','-X','utf8','tests/release/check.py','--archive',str(ARCHIVES[0]),'--run-fixture']
command={'argv':argv,'cwd':str(ROOT),'source_commit':SOURCE,'started_at':now(),'one_shot':True}
save('execution-started.json',command)
save('command.json',command)
with (OUT/'stdout.txt').open('wb') as stdout, (OUT/'stderr.txt').open('wb') as stderr:
    run=subprocess.run(argv,cwd=ROOT,stdout=stdout,stderr=stderr)
command.update({'exit_code':run.returncode,'finished_at':now()})
save('exit.json',{'actual_os_exit_code':run.returncode,'finished_at':command['finished_at']})
save('command.json',command)
after=snapshot()
save('after.json',after)
# Raw files and real OS exit are durable before any JSON parsing.
raw=(OUT/'stdout.txt').read_bytes()
err=(OUT/'stderr.txt').read_bytes()
report=json.loads(raw.decode('utf-8')) if raw.strip() else None
save('check-result.json',{'actual_os_exit_code':run.returncode,'reported':report,
     'stdout_sha256':sha(raw),'stderr_sha256':sha(err),'source_tools_archives_sbom_unchanged':before==after,
     'source_files_observed':len(source_paths),'new_check_executions':1,
     'no_old_provider_private_or_blocked_branch_execution':True})
print(json.dumps({'actual_os_exit_code':run.returncode,'report':report,'unchanged':before==after},ensure_ascii=False))
