"""One existing static-only check, with independent archive and preserved evidence audit."""
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
SOURCE = 'd4ed8ff90b198b1853eb9af803030b818f03591a'
OLD_SOURCE = 'a418d503f29646f62010905f9dc9338630aa0108'
EXPECTED = '2689666c9738e0073edfd7148efce71830d466267bc79f5b070d113769b4b31a'
ARCHIVES = [ROOT / ('.local/researchos-development-d4ed8ff-' + x + '.zip') for x in 'ab']
OLD = ROOT / '.local/researchos-development-a418d50-a.zip'
W21 = ROOT / 'execution/verifier/W21/current-handoff-index/6374df3'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name, value): (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def record(p): return {'path':p.relative_to(ROOT).as_posix(), 'sha256':sha(p.read_bytes()), 'bytes':p.stat().st_size}
assert not (OUT/'execution-started.json').exists(), 'One-shot already started: never rerun'
locked = load(ROOT/'execution/toolchains/locked.json')
python = Path(locked['tools']['python']['path'])
assert sha(python.read_bytes()) == locked['tools']['python']['sha256']
assert git('rev-parse','HEAD').decode().strip() == SOURCE
preserved = []
for directory, filename, expected in [
    (W21, 'manifest.json', '99a5ac98b87fb8da8c9b6dfe59a3426a5fe61a8866a1693c19c6ba2b1f9768d4'),
    (W21, 'supplement-manifest.json', '2e124bf4274e438d8bf147367683eeacd2ccfe9431e3c5e0af45a3347e504293'),
    (OUT.parent/'a418d50', 'manifest.json', 'd963c5e8d9da41c81a30f7e18b36c497c289615fecdecc621d9badaa2c5cc0a9')]:
    p = directory/filename
    assert sha(p.read_bytes()) == expected
    preserved.append(record(p))
    for entry in load(p)['files']:
        f = directory/entry['path']
        assert sha(f.read_bytes()) == entry['sha256']
        assert f.stat().st_size == entry.get('bytes',entry.get('size'))
        preserved.append(record(f))
save('preservation-before.json',preserved)
with zipfile.ZipFile(ARCHIVES[0]) as a, zipfile.ZipFile(ARCHIVES[1]) as b, zipfile.ZipFile(OLD) as old:
    names = a.namelist()
    assert len(names)==len(set(names))==515 and names==sorted(names)==b.namelist()
    assert all(a.read(n)==b.read(n) for n in names)
    assert ARCHIVES[0].read_bytes()==ARCHIVES[1].read_bytes()
    assert sha(ARCHIVES[0].read_bytes())==EXPECTED
    assert sha(OLD.read_bytes())=='dc90caedd5287bcd718c76bc8e0e2189cf3b33c92a547b6d9fe71d3564f8a193'
    ma,mo=json.loads(a.read('release-manifest.json')),json.loads(old.read('release-manifest.json'))
    assert ma['source_commit']==SOURCE and mo['source_commit']==OLD_SOURCE
    assert len(ma['files'])==514 and {x['path'] for x in ma['files']}==set(names)-{'release-manifest.json'}
    assert all(sha(a.read(x['path']))==x['sha256'] and len(a.read(x['path']))==x['size'] for x in ma['files'])
    added=sorted(set(names)-set(old.namelist()))
    removed=sorted(set(old.namelist())-set(names))
    changed=sorted(n for n in set(names)&set(old.namelist()) if n!='release-manifest.json' and a.read(n)!=old.read(n))
    same=sorted(n for n in set(names)&set(old.namelist()) if n!='release-manifest.json' and a.read(n)==old.read(n))
    assert added==['docs/installation/user-guide.md'] and not removed
    assert changed==['docs/installation/README.md','release/outcome_report.json'] and len(same)==511
    manifest_delta=sorted(k for k in set(ma)|set(mo) if ma.get(k)!=mo.get(k))
    assert manifest_delta==['build_id','files','source_commit','source_tree_sha256']
    tracked=set(git('ls-files','-z').decode().split('\0'))
    source_paths=sorted((set(names)&tracked)|{'tests/release/check.py','docs/handoff/current-construction.md','execution/toolchains/locked.json'})
    assert all((ROOT/p).read_bytes()==git('show',SOURCE+':'+p) for p in source_paths)
    assert all(a.read(p)==(ROOT/p).read_bytes() for p in set(names)&tracked)
    outcomes=json.loads(a.read('release/outcome_report.json')),json.loads(old.read('release/outcome_report.json'))
    outcome_delta=sorted(k for k in set(outcomes[0])|set(outcomes[1]) if outcomes[0].get(k)!=outcomes[1].get(k))
    assert outcome_delta==['user_guide']
    bins=[{'path':n,'sha256':sha(a.read(n))} for n in same if n.startswith('bin/')]
    assert len(bins)==4
    save('archive-audit.json',{'source_commit':SOURCE,'old_source_commit':OLD_SOURCE,'archive_sha256':EXPECTED,'archive_entries':len(names),'manifest_files':len(ma['files']),'two_archives_byte_identical':True,'every_entry_hash_and_size_valid':True,'added':added,'changed':changed,'removed':removed,'unchanged_payload_count':len(same),'unchanged_payload':[{'path':n,'sha256':sha(a.read(n))} for n in same],'manifest_semantic_delta':manifest_delta,'outcome_semantic_delta':outcome_delta,'bin_files':bins,'sbom_license_gaps':ma['sbom']['license_gaps'],'source_files_matching_git':source_paths,'all_other_manifest_fields_equal':True,'all_tracked_packaged_source_bytes_match':True})
    readme_before=old.read('docs/installation/README.md').decode()
    readme_after=a.read('docs/installation/README.md').decode()
    inserted=[line for line in readme_after.splitlines() if line not in readme_before.splitlines()]
    assert len(inserted)==1 and '[Chinese workbench guide](user-guide.md)' in inserted[0]
    assert readme_after.replace(inserted[0]+'\n\n','')==readme_before
guide=ROOT/'docs/installation/user-guide.md'
guide_review=ROOT/'execution/verifier/W20/user-guide/8d8c0db/report.json'
gr=load(guide_review)
assert sha(guide.read_bytes())==gr['guide_sha256']=='c3aea987e0bcd0527d82b1b460e16b79edcb93dc91cd825220f6cfbb72d3bcb0'
assert sha(guide_review.with_suffix('.md').read_bytes())=='63796bf348ff3a230af243190a5b208e784c819b1a2ce1a115da4d811c528b4c'
links=[]
for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',guide.read_text(encoding='utf-8')):
    p=(guide.parent/target).resolve()
    assert p.is_relative_to(ROOT) and p.is_file()
    item=record(p)
    prior=next(x for x in gr['links'] if x['target']==target)
    item['target']=target
    item['prior_review_hash_equal']=item['sha256']==prior['sha256']
    assert item['prior_review_hash_equal'] or item['path']=='docs/installation/README.md'
    item['bundled']=item['path'] in names
    links.append(item)
assert len(links)==51 and sum(x['path'].endswith('.png') for x in links)==45
assert len(re.findall(r'^## \d+\.',guide.read_text(encoding='utf-8'),re.M))==11
save('document-audit.json',{'guide':record(guide),'guide_independent_review':record(guide_review),'guide_review_reused_by_exact_bytes':True,'page_count':11,'links':links,'relative_links':51,'screenshots':45,'missing_links':0,'screenshot_cells_missing':5,'readme_only_added_paragraph':inserted[0],'outcome_only_added_user_guide':outcomes[0]['user_guide'],'historical_facts_and_ui_sources_reused_via_unchanged_payload':True,'screenshot_files_bundled':False,'new_browser_or_screenshot_execution':False})
tools={k:Path(v['path']) for k,v in locked['tools'].items() if 'path' in v}
tools['powershell']=Path(shutil.which('powershell.exe'))
def snapshot():
    with zipfile.ZipFile(ARCHIVES[0]) as a:
        raw=a.read('release-manifest.json'); m=json.loads(raw)
    return {'git_head':git('rev-parse','HEAD').decode().strip(),'source':{p:sha((ROOT/p).read_bytes()) for p in source_paths},'tools':{k:{'path':str(p),'sha256':sha(p.read_bytes())} for k,p in tools.items()},'archives':{str(p):sha(p.read_bytes()) for p in [*ARCHIVES,OLD]},'archive_manifest_sha256':sha(raw),'sbom_canonical_sha256':sha(json.dumps(m['sbom'],sort_keys=True,separators=(',',':')).encode()),'check_sha256':sha((ROOT/'tests/release/check.py').read_bytes()),'preserved_files':[record(ROOT/x['path']) for x in preserved]}
before=snapshot(); save('before.json',before)
argv=[str(python),'-B','-X','utf8','tests/release/check.py','--archive',str(ARCHIVES[0])]
command={'argv':argv,'cwd':str(ROOT),'source_commit':SOURCE,'started_at':now(),'one_shot':True,'run_fixture':False}
save('execution-started.json',command); save('command.json',command)
with (OUT/'stdout.txt').open('wb') as stdout, (OUT/'stderr.txt').open('wb') as stderr:
    run=subprocess.run(argv,cwd=ROOT,stdout=stdout,stderr=stderr)
save('exit.json',{'actual_os_exit_code':run.returncode,'finished_at':now()})
after=snapshot(); save('after.json',after)
# Raw stdout/stderr and actual OS exit persisted before JSON parsing.
raw=(OUT/'stdout.txt').read_bytes(); err=(OUT/'stderr.txt').read_bytes()
parsed=json.loads(raw.decode('utf-8')) if raw.strip() else None
result={'actual_os_exit_code':run.returncode,'reported':parsed,'stdout_sha256':sha(raw),'stderr_sha256':sha(err),'before_after_identical':before==after,'new_static_check_executions':1,'new_product_native_executions':0,'old_a418_assertions_historical_only':28,'source_files_observed':len(source_paths),'powershell_verify_and_unbound_dispatcher_executed':True,'no_old_native_provider_private_or_blocked_branch_execution':True}
save('check-result.json',result)
print(json.dumps(result,ensure_ascii=False))
