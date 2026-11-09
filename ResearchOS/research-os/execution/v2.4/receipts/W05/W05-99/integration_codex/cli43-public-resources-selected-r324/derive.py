"""Select installed compiler/input trees from a closed fresh public inventory.
No historic compile graph, product executable, native call or resource byte read.
The eventual controller must independently check current full selected membership
and reject every actual graph input not present before any case is permitted.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
PARENT = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-public-resources-15ccd02e325b4d0e9384d66bb2a9d924'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def verified(ref):
    b = Path(ref['path']).read_bytes()
    need(len(b) == ref['bytes'] and hashlib.sha256(b).hexdigest() == ref['sha256'], 'Sealed document changed')
    return b

def pin(p):
    p = Path(p).absolute()
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def save(name, obj):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
mf_ref = pin(PARENT / 'manifest.json')
need(mf_ref['sha256'] == '421a6f850e2a1ce6a5b85210c74329775eaa373732bfda081f1e2770a07ee00a', 'Parent manifest SHA')
mf = json.loads(verified(mf_ref))
def member(name):
    matches = [r for r in mf['entries'] if Path(r['path']).name == name]
    need(len(matches) == 1, 'Exact sealed member missing')
    r = matches[0]
    return {**r, 'path': str(ROOT / r['path'])}
old_ref = member('compiler-resources.json')
old = json.loads(verified(old_ref))
audit_ref = member('audit.json')
audit = json.loads(verified(audit_ref))
need(old['source_commit'] == audit['source_commit'] == 'a510dbef4a7e08fb5c428df44c39b133f3ffa856', 'Current source identity')
for r in audit['before_refs'][:4]:
    need(pin(r['path']) == r, 'Canonical changed before resource selection')
rows = old['files']
go, mods, git = [Path(r['path']) for r in old['complete_public_roots']]
selected = {}
roots = []
directories = [go / n for n in ['src', 'bin', 'pkg', 'lib']]
module_tops = sorted({Path(r['path']).relative_to(mods).parts[0] for r in rows
                     if Path(r['path']).is_relative_to(mods) and len(Path(r['path']).relative_to(mods).parts) > 1
                     and Path(r['path']).relative_to(mods).parts[0] != 'cache'})
directories += [mods / n for n in module_tops]
directories += [git / n for n in ['cmd', 'mingw64/bin', 'mingw64/libexec/git-core', 'usr/bin', 'usr/share/locale']]
omitted_empty_directories = []
for directory in directories:
    members = [r for r in rows if Path(r['path']).is_relative_to(directory)]
    if not members:
        omitted_empty_directories.append(str(directory))
        continue
    members.sort(key=lambda r: r['path'].casefold())
    roots.append({'path': str(directory), 'files': members})
    selected.update({r['path']: r for r in members})
explicit = []
for r in rows:
    p = Path(r['path'])
    is_root_metadata = p.parent in [go, mods, git]
    is_download_metadata = p.is_relative_to(mods / 'cache') and p.suffix.lower() != '.zip'
    if is_root_metadata or is_download_metadata:
        selected[r['path']] = r
        explicit.append(r)
new = {**old, 'schema': 'researchos.current43-selected-public-compiler-resources.v1',
    'files': [selected[p] for p in sorted(selected)], 'complete_public_roots': roots,
    'closed_full_inventory_ref': old_ref, 'closed_full_inventory_manifest_ref': mf_ref,
    'explicit_metadata_files': explicit,
    'selection_basis': 'Full current installed Go src/bin/pkg/lib, all installed extracted public module trees, all module download metadata except zip payloads, Git execution/library/locale trees. Documentation, Go regression distribution and unused download zip payloads are omitted.',
    'membership_remeasured_in_this_derivation': False,
    'required_future_check': 'Before Go, actual selected recursive root membership must equal this closed snapshot. The fresh -compiled -deps -test graph must include only preapproved files/new owned WORK before either case starts. Unknown input is a stop, never a graph repair or automatic retry.',
    'no_historical_compile_graph_used': True,
    'no_prior_product_executable_or_cache_used': True}
save('compiler-resources.json', new)
save('selection-audit.json', {'actor': 'codex:/root', 'current': [324, 152, 430],
    'source_commit': old['source_commit'], 'parent_manifest_ref': mf_ref, 'parent_inventory_ref': old_ref,
    'compiler_resources_ref': pin(OUT / 'compiler-resources.json'),
    'full_files': len(rows), 'selected_files': len(selected),
    'full_bytes': sum(r['bytes'] for r in rows), 'selected_bytes': sum(r['bytes'] for r in selected.values()),
    'root_counts': [{'path': r['path'], 'count': len(r['files'])} for r in roots],
    'explicit_metadata_count': len(explicit), 'omitted_no_member_candidates': omitted_empty_directories,
    'no_current_resource_membership_claim': True, 'future_timeout_limits_unchanged': True,
    'source_or_canonical_writes': 0, 'resource_bytes_read_here': 0, 'Go_SQL_HTTP_MODEL_calls': 0,
    'execution_authorized': False, 'actual_compile_graph': None, 'actual_cases': 'NOT_RUN', 'formal_increment': 0})
members = [pin(p) for p in sorted(OUT.iterdir(), key=lambda p: p.name) if p.is_file()]
save('manifest.json', {'actor': 'codex:/root', 'entries': members, 'count': len(members), 'self_excluded': True,
    'product_execution': False, 'formal_increment': 0})
print(json.dumps({'audit_ref': pin(OUT / 'selection-audit.json'), 'manifest_ref': pin(OUT / 'manifest.json'),
    'selected_files': len(selected), 'selected_bytes': sum(r['bytes'] for r in selected.values())}, ensure_ascii=False))
