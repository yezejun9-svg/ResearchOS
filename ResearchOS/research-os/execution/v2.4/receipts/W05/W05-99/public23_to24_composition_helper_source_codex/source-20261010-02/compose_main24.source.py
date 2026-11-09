"""Root-only Main24 composition; prepare metadata, then explicitly authorized apply.
No import-time writes, child processes, Go, SQL, model, network, or Canon mutation.
"""
from __future__ import annotations
import argparse, ast, ctypes, hashlib, json, math, os, re, sys, types, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

REPO = Path(r'D:/作品集/ResearchOS/research-os')
PROJECT = 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
BASE = REPO / 'execution/v2.4/receipts/W05/W05-99'
RUN_PARENT = BASE / 'integration_codex'
MERGE = BASE / 'public23_to24_main_merge_preparation_codex/prepare-20261010-01/file-merge-map.json'
MERGE_SHA = '44471d2f2fcb80ee96b8fd2515ea3decba7e258433c4ba3993c619676a7cb61c'
GUARD = BASE / 'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GUARD_SHA = 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
NATIVE = 'b1599aaf259c435db5a0a5313ab0ea65'
PATHS = (
 'internal/domain/store.go',
 'internal/domain/runtime_coordinator_windows.go',
 'internal/domain/backup_migration.go',
 'internal/domain/prepared_run_abandonment.go',
 'internal/domain/prepared_run_abandonment_windows_test.go',
 'migrations/sqlite/0024_prepared_run_abandonment.sql',
 'apps/control/main.go',
 'apps/control/prepared_recovery_other.go',
 'apps/control/prepared_recovery_windows.go',
 'internal/domain/prepared_abandonment_authority.go',
 'internal/domain/prepared_abandonment_authority_test.go',
 'internal/recoveryauthority/authority_test.go',
 'internal/recoveryauthority/enrollment_windows.go',
 'internal/recoveryauthority/history.go',
 'internal/recoveryauthority/history_test.go',
 'internal/recoveryauthority/migration.go',
 'internal/recoveryauthority/migration_windows.go',
 'internal/recoveryauthority/native_other.go',
 'internal/recoveryauthority/native_windows.go',
 'internal/recoveryauthority/native_windows_test.go',
 'internal/recoveryauthority/root_windows.go',
 'internal/recoveryauthority/transport_windows.go',
 'internal/recoveryauthority/types.go',
 'ops/supervisor/recovery_enrollment/main_windows.go',
 'ops/supervisor/recovery_root/main_windows.go',
 'internal/domain/backup.go',
 'internal/domain/backup_configuration_upgrade_test.go',
 'internal/domain/backup_historical14_resume_test.go',
 'internal/domain/backup_host_configuration.go',
 'internal/domain/backup_prepared_abandonment_upgrade.go',
 'internal/domain/backup_prepared_abandonment_upgrade_other.go',
 'internal/domain/backup_prepared_abandonment_upgrade_test.go',
 'internal/domain/backup_prepared_abandonment_upgrade_windows.go',
 'internal/domain/backup_prepared_abandonment_upgrade_windows_test.go',
 'internal/domain/backup_upgrade.go',
 'internal/domain/backup_upgrade_test.go',
 'internal/domain/contracts/prepared_run_abandonment.sql',
 'ops/backup/main.go',
 'internal/domain/backup_prepared_abandonment_handoff.go',
 'internal/domain/backup_prepared_abandonment_handoff_test.go',
)
HEX = re.compile(r'[0-9a-f]{64}\Z')
RUN_NAME = re.compile(r'main24-compose-[0-9a-f]{32}\Z')

class Refusal(RuntimeError):
    pass

def need(ok, code):
    if not ok:
        raise Refusal(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def bad(value):
        raise Refusal('NONFINITE_JSON')
    def number(value):
        result = float(value)
        need(math.isfinite(result), 'NONFINITE_JSON')
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad, parse_float=number)

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def path_key(path):
    return os.path.normcase(str(path))

def safe_path(path, exists=False):
    path = Path(path)
    need(path.is_absolute() and path.drive.lower() == REPO.drive.lower(), 'ABSOLUTE_LOCAL_REPO_PATH')
    parts = str(path).replace('\\', '/').split('/')[1:]
    need(all(x not in ('', '.', '..') and ':' not in x and not x.endswith((' ', '.')) for x in parts), 'REGULAR_PATH')
    need(path.is_relative_to(REPO), 'REPO_SCOPE')
    cursor = path
    while True:
        need(not cursor.is_symlink() and not cursor.is_junction(), 'PATH_LINK')
        if cursor == REPO:
            break
        cursor = cursor.parent
    need(path.resolve().is_relative_to(REPO.resolve()) and REPO.resolve() == REPO, 'RESOLVED_REPO_SCOPE')
    if exists:
        need(path.is_file() and path.stat().st_nlink == 1, 'REGULAR_SINGLE_LINK_FILE')
    return path

def target(relative):
    need(relative in PATHS and not PureWindowsPath(relative).drive and '..' not in Path(relative).parts, 'TARGET40_ONLY')
    return safe_path(REPO / relative)

def pin(path, raw=None):
    raw = path.read_bytes() if raw is None else raw
    return dict(path=str(path), sha256=sha(raw), bytes=len(raw))

def checked(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}, 'EXACT_REF3')
    need(type(ref['sha256']) is str and HEX.fullmatch(ref['sha256']) is not None, 'SHA256')
    need(type(ref['bytes']) is int and 0 <= ref['bytes'] <= 256*1024*1024, 'SIZE')
    path = safe_path(ref['path'], True)
    raw = path.read_bytes()
    need(len(raw) == ref['bytes'] and sha(raw) == ref['sha256'], 'PIN_DRIFT:' + str(path))
    return path, raw

def save(path, raw):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_path(path.parent)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    need(path.read_bytes() == raw, 'ARTIFACT_READBACK')
    return pin(path, raw)

def document(path, value):
    return save(path, encoded(value))

def add_ref(refs, ref):
    path, raw = checked(ref)
    key = path_key(path)
    need(key not in refs or refs[key] == ref, 'CONFLICTING_PIN')
    refs[key] = dict(ref)
    return raw

def identity(ref):
    path, raw = checked(ref)
    need(path == REPO / 'execution/project_identity.json', 'IDENTITY_PATH')
    value = decode(raw)
    need(value['project_id'] == PROJECT and Path(value['repository_root']) == REPO, 'PROJECT_IDENTITY')
    return value

def apply_edits(original, edit):
    """Pure byte-edit function. No filesystem writes."""
    need(sha(original) == edit['required_current_ref']['sha256'] and len(original) == edit['required_current_ref']['bytes'], 'EDIT_BASE')
    actions = edit['edits']
    need(type(actions) is list and bool(actions), 'NONEMPTY_EDITS')
    prior = 0
    output = []
    inverse = []
    new_offset = 0
    for action in actions:
        start, end = action['old_start_byte'], action['old_end_byte']
        need(type(start) is int and type(end) is int and prior <= start <= end <= len(original), 'EDIT_RANGES')
        old = action['old_utf8'].encode('utf-8')
        new = action['replacement_utf8'].encode('utf-8')
        need(original[start:end] == old and len(old) == action['old_bytes'] and sha(old) == action['old_sha256'], 'OLD_SLICE_PIN')
        need(len(new) == action['new_bytes'] and sha(new) == action['new_sha256'], 'NEW_SLICE_PIN')
        unchanged = original[prior:start]
        output.extend((unchanged, new))
        new_offset += len(unchanged)
        inverse.append(dict(start=new_offset, end=new_offset+len(new), expected_sha256=sha(new), replacement_utf8=old.decode('utf-8')))
        new_offset += len(new)
        prior = end
    output.append(original[prior:])
    desired = b''.join(output)
    need(sha(desired) == edit['expected_result_ref']['sha256'] and len(desired) == edit['expected_result_ref']['bytes'], 'EDIT_RESULT_PIN')
    restored = desired
    for action in reversed(inverse):
        start, end = action['start'], action['end']
        need(sha(restored[start:end]) == action['expected_sha256'], 'INVERSE_SLICE_PIN')
        restored = restored[:start] + action['replacement_utf8'].encode('utf-8') + restored[end:]
    need(restored == original, 'COMPLETE_BYTE_INVERSE')
    return desired, inverse


# V2 gates: read-only Git baseline and actual independent/Root authority.
AUTHOR = 'codex:/root/attach_restore_independent_review'
ROOT_ACTOR = 'codex:/root'
BASE_HELPER = BASE/'public23_to24_composition_helper_source_codex/source-20261010-01/compose_main24.source.py'
BASE_HELPER_SHA = 'e2e70ce36c9bfd473bb24c5d23aa18e2e9da238cab77f5b98a26e4970854e373'
AUDIT_RUNTIME = REPO/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py'
AUDIT_RUNTIME_SHA = '1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08'
ROOT_THREAD_ID = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT_AUDIT = r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'

def parse_git_index(raw):
    import struct
    need(len(raw)>=32 and len(raw)<=16*1024*1024, 'GIT_INDEX_SIZE')
    need(raw[:4]==b'DIRC', 'GIT_INDEX_MAGIC')
    version,count=struct.unpack('>II',raw[4:12])
    need(version in (2,3) and count<=100000, 'GIT_INDEX_SUPPORTED_VERSION_COUNT')
    need(hashlib.sha1(raw[:-20]).digest()==raw[-20:], 'GIT_INDEX_CHECKSUM_SHA1')
    cursor=12;entries=[];seen=set()
    for _ in range(count):
        start=cursor
        need(cursor+62<=len(raw)-20, 'GIT_INDEX_ENTRY_TRUNCATED')
        mode=int.from_bytes(raw[cursor+24:cursor+28],'big')
        flags=int.from_bytes(raw[cursor+60:cursor+62],'big')
        oid=raw[cursor+40:cursor+60].hex()
        need(flags&0x3000==0 and flags&0x8000==0, 'GIT_INDEX_STAGE_ASSUME_UNCHANGED_UNSUPPORTED')
        cursor+=62
        if flags&0x4000:
            need(version==3 and cursor+2<=len(raw)-20, 'GIT_INDEX_EXTENDED_FLAGS')
            extended=int.from_bytes(raw[cursor:cursor+2],'big');cursor+=2
            need(extended==0, 'GIT_INDEX_SKIP_WORKTREE_INTENT_UNSUPPORTED')
        end=raw.find(b'\0',cursor,len(raw)-20)
        need(end>=cursor, 'GIT_INDEX_PATH_TERMINATOR')
        pathname=raw[cursor:end]
        need((flags&0xFFF)==min(len(pathname),0xFFF), 'GIT_INDEX_NAME_LENGTH')
        rel=pathname.decode('utf-8','strict')
        need(rel and '\\' not in rel and ':' not in rel and not rel.startswith('/')
            and all(x not in ('','.','..') and not x.endswith((' ','.')) for x in rel.split('/')), 'GIT_INDEX_SAFE_TRACKED_PATH')
        need(rel.casefold() not in seen, 'GIT_INDEX_DUPLICATE_OR_CASE_ALIAS')
        seen.add(rel.casefold())
        need(mode in (0o100644,0o100755), 'GIT_INDEX_ONLY_REGULAR_TRACKED_FILES')
        cursor=start+((end+1-start+7)//8)*8
        need(cursor<=len(raw)-20 and not any(raw[end:cursor]), 'GIT_INDEX_PADDING')
        entries.append(dict(path=rel,index_oid=oid,mode=mode))
    extensions=[]
    while cursor<len(raw)-20:
        need(cursor+8<=len(raw)-20, 'GIT_INDEX_EXTENSION_HEADER')
        signature=raw[cursor:cursor+4]
        length=int.from_bytes(raw[cursor+4:cursor+8],'big');cursor+=8
        need(signature==b'TREE' and not extensions, 'GIT_INDEX_EXTENSION_UNSUPPORTED')
        need(cursor+length<=len(raw)-20, 'GIT_INDEX_EXTENSION_SIZE')
        extensions.append('TREE');cursor+=length
    need(cursor==len(raw)-20, 'GIT_INDEX_TRAILING_BYTES')
    return dict(version=version,entries=entries,extensions=extensions)

def parse_git_head(raw):
    need(len(raw)<=4096 and raw.endswith(b'\n'), 'GIT_HEAD_BOUNDED_LINE')
    value=raw.decode('ascii','strict').strip()
    if value.startswith('ref: '):
        branch=value[5:]
        need(branch.startswith('refs/heads/') and all(x not in ('','.','..') for x in branch.split('/'))
            and re.fullmatch(r'[A-Za-z0-9_./-]+',branch) is not None, 'GIT_HEAD_SAFE_BRANCH')
        return dict(kind='symbolic',ref=branch)
    need(re.fullmatch('[0-9a-f]{40}',value) is not None, 'GIT_HEAD_SHA1_ONLY')
    return dict(kind='detached',commit=value)

def validate_git_config(raw):
    import configparser
    need(len(raw)<=1024*1024,'GIT_CONFIG_CAP')
    config=configparser.RawConfigParser(strict=True,interpolation=None)
    try:config.read_string(raw.decode('utf-8','strict'))
    except (ValueError,UnicodeError,configparser.Error):raise Refusal('GIT_CONFIG_UNSUPPORTED_SYNTAX') from None
    need('core' in config and config['core'].get('bare','false').lower()=='false','GIT_NONBARE_REPO')
    need('worktree' not in config['core'],'GIT_CONFIG_WORKTREE_OVERRIDE')
    need(not any(s.lower()=='extensions' or s.lower()=='include' or s.lower().startswith('includeif') for s in config.sections()),'GIT_CONFIG_EXTENSIONS_INCLUDES_UNSUPPORTED')

def git_snapshot():
    # No git subprocess, config content output, untracked recursion or external worktree.
    need(not any(os.environ.get(k) for k in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE','GIT_CONFIG','GIT_CONFIG_COUNT')),'GIT_ENV_REDIRECTION')
    gd=safe_path(REPO/'.git')
    need(gd.is_dir() and not gd.is_symlink() and not gd.is_junction(),'GIT_FIXED_DIRECTORY')
    absent=[]
    for name in ('commondir','gitdir','config.worktree','index.lock','HEAD.lock','config.lock','shallow'):
        p=safe_path(gd/name);need(not p.exists(),'GIT_UNSUPPORTED_WORKTREE_OR_ACTIVE_LOCK');absent.append(str(p))
    metadata=[];total=0
    def read_meta(path,cap):
        nonlocal total
        p=safe_path(path,True)
        need(p.stat().st_size<=cap,'GIT_METADATA_CAP')
        with p.open('rb') as f:raw=f.read(cap+1)
        need(len(raw)<=cap,'GIT_METADATA_CAP')
        total+=len(raw);need(total<=32*1024*1024,'GIT_METADATA_TOTAL_CAP')
        metadata.append(pin(p,raw));return raw
    config=read_meta(gd/'config',1024*1024);validate_git_config(config)
    head=read_meta(gd/'HEAD',4096);head_value=parse_git_head(head)
    if head_value['kind']=='symbolic':
        refpath=safe_path(gd/head_value['ref'])
        if refpath.exists():
            refraw=read_meta(refpath,4096)
            need(re.fullmatch(rb'[0-9a-f]{40}\n',refraw) is not None,'GIT_LOOSE_REF_SHA1')
            head_value['commit']=refraw.decode().strip()
        else:
            absent.append(str(refpath))
            packed=read_meta(gd/'packed-refs',8*1024*1024)
            matches=[]
            for line in packed.splitlines():
                if not line or line.startswith((b'#',b'^')):continue
                parts=line.split(b' ')
                need(len(parts)==2 and re.fullmatch(rb'[0-9a-f]{40}',parts[0]) is not None,'GIT_PACKED_REF_SYNTAX')
                if parts[1].decode('ascii','strict')==head_value['ref']:matches.append(parts[0].decode())
            need(len(matches)==1,'GIT_PACKED_HEAD_UNIQUE')
            head_value['commit']=matches[0]
    index=read_meta(gd/'index',16*1024*1024);parsed=parse_git_index(index)
    tracked=[];tracked_total=0
    for entry in parsed['entries']:
        p=safe_path(REPO/entry['path'])
        if p.exists():
            safe_path(p,True);need(p.stat().st_size<=32*1024*1024,'GIT_TRACKED_FILE_CAP')
            with p.open('rb') as f:raw=f.read(32*1024*1024+1)
            need(len(raw)<=32*1024*1024,'GIT_TRACKED_FILE_CAP')
            tracked_total+=len(raw);need(tracked_total<=2*1024*1024*1024,'GIT_TRACKED_TOTAL_CAP')
            observed=pin(p,raw)
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            tracked.append(dict(**entry,worktree_ref=observed,absent=False,raw_differs_from_index_blob=blob!=entry['index_oid']))
        else:tracked.append(dict(**entry,worktree_ref=None,absent=True,raw_differs_from_index_blob=True))
    return dict(schema='researchos.main24-git-baseline.v1',repo_root=str(REPO),
        git_dir=str(gd),common_dir=str(gd),worktree_root=str(REPO),dotgit_kind='directory',
        head=head_value,metadata_refs=metadata,required_absent_paths=absent,
        index_version=parsed['version'],index_extensions=parsed['extensions'],
        tracked=tracked,tracked_count=len(tracked),untracked_enumerated=False,
        dirty_semantics='Raw byte comparison against index blob; no Git clean filters or status process.')

def verify_git_baseline(req,refs=None):
    _,raw=checked(req['git_baseline_ref']);expected=decode(raw)
    observed=git_snapshot()
    need(observed==expected,'EXACT_GIT_IDENTITY_HEAD_CONFIG_INDEX_TRACKED_BASELINE')
    if refs is not None:
        add_ref(refs,req['git_baseline_ref'])
        for ref in expected['metadata_refs']:add_ref(refs,ref)
        targets={path_key(target(rel)) for rel in PATHS}
        for row in expected['tracked']:
            ref=row['worktree_ref']
            if ref is not None and path_key(Path(ref['path'])) not in targets:add_ref(refs,ref)
    return observed

def actual_audit_gate(ref,actor,digest,refs):
    raw=AUDIT_RUNTIME.read_bytes()
    need(sha(raw)==AUDIT_RUNTIME_SHA,'CANONICAL_ACTUAL_AUDIT_SOURCE_PIN')
    add_ref(refs,pin(AUDIT_RUNTIME,raw))
    names={'require','decode','exact_path','raw_pin','read_ref','exact_host_peer_author','actual_audit'}
    tree=ast.parse(raw)
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    need(len(body)==len(names),'CANONICAL_ACTUAL_AUDIT_DEFINITIONS')
    env=dict(Path=Path,json=json,re=re,hashlib=hashlib,MAX=256*1024*1024,
        ROOT_ACTOR=ROOT_ACTOR,ROOT_THREAD_ID=ROOT_THREAD_ID,ROOT_AUDIT=ROOT_AUDIT)
    exec(compile(ast.Module(body=body,type_ignores=[]),str(AUDIT_RUNTIME),'exec'),env)
    returned=env['actual_audit'](ref,actor,digest)
    need(type(returned) is list and len(returned)==2,'ACTUAL_AUDIT_RETURNS_TWO_REFS')
    for item in returned:add_ref(refs,item)
    return returned

def finite_lease(issued_at,expires_at):
    issued=parse_stamp(issued_at);expires=parse_stamp(expires_at);now=datetime.now(timezone.utc)
    need(issued<=now<expires and 0<(expires-issued).total_seconds()<=3600,'ACTUAL_AUTHORITY_FINITE_LEASE')

def prepare_scope_expected(req,scope):
    return dict(schema='researchos.root-main24-prepare-scope.v1',
        status='ROOT_AUTHORIZED_MAIN24_METADATA_PREPARE',issued_by=ROOT_ACTOR,
        issued_at=scope['issued_at'],expires_at=scope['expires_at'],
        request_body={k:v for k,v in req.items() if k not in ('prepare_scope_ref','prepare_audit_ref')},
        target_paths=list(PATHS),Main_writes=False,Canon_writes=False,product_execution=False)

def verify_prepare_authority(req,refs):
    scope=decode(add_ref(refs,req['prepare_scope_ref']))
    need(scope==prepare_scope_expected(req,scope),'PREPARE_ROOT_SCOPE_BINDING')
    finite_lease(scope['issued_at'],scope['expires_at'])
    verified_root_observation(req['prepare_audit_ref'],req['prepare_scope_ref'],scope,refs)
    base=BASE_HELPER.read_bytes();need(sha(base)==BASE_HELPER_SHA,'V1_HELPER_FROZEN')
    add_ref(refs,pin(BASE_HELPER,base))

def validate_source_review(review,helper_ref):
    need(review.get('schema')=='researchos.main24-composition-helper-independent-source-decision.v1'
        and review.get('verdict')=='ACCEPTED_SOURCE_ONLY','INDEPENDENT_SOURCE_ACCEPTED_VERDICT')
    actor=review.get('review_author')
    need(type(actor) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*',actor) is not None
        and actor!=AUTHOR and review.get('source_author')==AUTHOR
        and review.get('review_author_backend')==actor.removeprefix('codex:')
        and review.get('independent_non_author') is True,'NON_AUTHOR_REVIEW_ACTOR')
    need(review.get('source_ref')==helper_ref,'REVIEW_EXACT_V2_SOURCE')
    need(review.get('all_guards_closed') is True and review.get('retained_handles_count')==0
        and review.get('blocking_codes')==[] and review.get('execution_grant') is False
        and review.get('formal_acceptance') is False,'REVIEW_CLOSED_SOURCE_ONLY')
    return actor

def apply_scope_expected(grant,req,prepared,prepared_ref):
    return dict(schema='researchos.root-main24-apply-scope.v2',
        status='ROOT_AUTHORIZED_MAIN24_COMPOSITION',issued_by=ROOT_ACTOR,executor=ROOT_ACTOR,
        project_id=PROJECT,lease_id=grant['operation_id'],exclusive_main_writer=True,
        issued_at=grant['issued_at'],expires_at=grant['expires_at'],
        source_helper_ref=req['source_helper_ref'],prepared_ref=prepared_ref,
        source_package_hdf_ref=req['source_package_hdf_ref'],source_package_mf_ref=req['source_package_mf_ref'],
        source_contract_ref=req['source_contract_ref'],repo_root=str(REPO),Root_thread_id=ROOT_THREAD_ID,
        project_identity_ref=req['project_identity_ref'],
        request_ref=prepared['request_ref'],git_baseline_ref=req['git_baseline_ref'],
        merge_map_ref=req['merge_map_ref'],native_revision=NATIVE,target_paths=list(PATHS),
        prepared_files_sha256=sha(encoded(prepared['files'])),
        independent_source_review_ref=grant['independent_source_review_ref'],
        independent_source_review_hdf_ref=grant['independent_source_review_hdf_ref'],
        independent_source_review_mf_ref=grant['independent_source_review_mf_ref'],
        existing_increment_targets=10,new_absent_only_targets=30,
        Canon_writes=False,product_execution=False,automatic_retry=False,automatic_rollback=False)

def verify_apply_authority(grant,req,prepared,prepared_ref,refs):
    review=decode(add_ref(refs,grant['independent_source_review_ref']))
    actor=validate_source_review(review,req['source_helper_ref'])
    validate_review_package(grant,req,review,refs)
    actual_audit_gate(grant['source_review_audit_ref'],actor,grant['independent_source_review_ref']['sha256'],refs)
    scope=decode(add_ref(refs,grant['root_authorization_observation_ref']))
    need(scope==apply_scope_expected(grant,req,prepared,prepared_ref),'ROOT_APPLY_SCOPE_FULL_BINDING')
    finite_lease(grant['issued_at'],grant['expires_at'])
    verified_root_observation(grant['root_authorization_audit_ref'],grant['root_authorization_observation_ref'],scope,refs)



def validate_source_package(req,refs):
    h=decode(add_ref(refs,req['source_package_hdf_ref']))
    m=decode(add_ref(refs,req['source_package_mf_ref']))
    add_ref(refs,req['source_contract_ref'])
    need(h.get('source_helper_ref')==req['source_helper_ref']
        and h.get('contract_ref')==req['source_contract_ref'],'OWN_SOURCE_PACKAGE_BINDING')
    need(m.get('HDF_ref')==req['source_package_hdf_ref'],'OWN_MANIFEST_HDF_BINDING')
    members=m.get('files')
    need(type(members) is list and req['source_helper_ref'] in members
        and req['source_contract_ref'] in members and req['source_package_hdf_ref'] in members,'OWN_PACKAGE_REQUIRED_MEMBERS')
    home=Path(req['source_helper_ref']['path']).parent
    for ref in members:
        need(Path(ref['path']).is_relative_to(home),'OWN_PACKAGE_LOCAL_MEMBER')
        add_ref(refs,ref)

def validate_review_package(grant,req,review,refs):
    h=decode(add_ref(refs,grant['independent_source_review_hdf_ref']))
    m=decode(add_ref(refs,grant['independent_source_review_mf_ref']))
    need(h.get('decision_ref')==grant['independent_source_review_ref']
        and h.get('manifest_ref')==grant['independent_source_review_mf_ref'],'REVIEW_TRIPLET_BINDING')
    bindings=dict(source_handoff_ref=req['source_package_hdf_ref'],source_manifest_ref=req['source_package_mf_ref'],
        source_ref=req['source_helper_ref'],calling_contract_ref=req['source_contract_ref'],
        review_author=review['review_author'],source_author=AUTHOR,independent_non_author=True,verdict='ACCEPTED_SOURCE_ONLY')
    need(all(h.get(k)==v and review.get(k)==v for k,v in bindings.items()),'REVIEW_PACKAGE_CURRENT_SOURCE')
    members=m.get('members')
    need(type(members) is list and grant['independent_source_review_ref'] in members,'REVIEW_DECISION_MANIFEST_MEMBER')
    home=Path(grant['independent_source_review_ref']['path']).parent
    for ref in members:
        need(Path(ref['path']).is_relative_to(home),'REVIEW_LOCAL_MEMBER')
        add_ref(refs,ref)

def root_observation_candidates(result):
    output=result.get('payload',{}).get('output')
    texts=[]
    if type(output) is str:texts=[output]
    elif type(output) is list:
        need(all(type(item) is dict and item.get('type')=='input_text' and type(item.get('text')) is str for item in output),'ROOT_OUTPUT_TEXT_BLOCKS')
        texts=[item['text'] for item in output]
    else:raise Refusal('ROOT_OUTPUT_SHAPE')
    found=[]
    def inspect(value):
        if type(value) is not dict:return
        if value.get('schema')=='researchos.main24-authority-observation.v1':found.append(value);return
        if 'chunk_id' in value:
            need(value.get('exit_code')==0 and type(value.get('output')) is str,'ROOT_OBSERVATION_TOOL_SUCCESS')
            for line in value['output'].splitlines():
                if line.strip().startswith('{'):inspect(decode(line))
    for text in texts:
        stripped=text.strip()
        if stripped.startswith('{'):inspect(decode(stripped))
        elif stripped.startswith('Script completed\n'):
            body=stripped.partition('Output:\n')[2]
            if body.strip().startswith('{'):inspect(decode(body.strip()))
        else:need(not stripped.startswith('Script failed'),'ROOT_OBSERVATION_OUTER_FAILED')
    return found

def validate_root_observation(records,payload_ref,payload):
    need(type(records) is list and len(records)==3,'ROOT_OBSERVATION_THREE_RECORDS')
    _,call,result=records
    found=root_observation_candidates(result)
    need(len(found)==1,'ROOT_TYPED_OBSERVATION_UNIQUE')
    observed=found[0]
    need(set(observed)=={'schema','actor_id','Root_thread_id','payload_ref','payload','observed_at'},'ROOT_TYPED_OBSERVATION_FIELDS')
    need(observed['actor_id']==ROOT_ACTOR and observed['Root_thread_id']==ROOT_THREAD_ID
        and observed['payload_ref']==payload_ref and observed['payload']==payload,'ROOT_TYPED_FULL_PAYLOAD_BINDING')
    called=parse_stamp(call['timestamp']);seen=parse_stamp(observed['observed_at']);returned=parse_stamp(result['timestamp'])
    issued=parse_stamp(payload['issued_at']);expires=parse_stamp(payload['expires_at'])
    need(issued<=called<=seen<=returned<expires and returned<=datetime.now(timezone.utc),'ROOT_ACTUAL_CAUSAL_LEASE_ORDER')
    return observed

def verified_root_observation(audit_ref,payload_ref,payload,refs):
    actual=actual_audit_gate(audit_ref,ROOT_ACTOR,payload_ref['sha256'],refs)
    records=[decode(line) for line in checked(actual[1])[1].splitlines()]
    return validate_root_observation(records,payload_ref,payload)



def input_bundle(request_ref):
    refs = {}
    request_raw = add_ref(refs, request_ref)
    req = decode(request_raw)
    need(set(req) == {'schema','actor_id','repo_root','project_identity_ref','source_helper_ref','merge_map_ref','native_revision','output_directory','git_baseline_ref','prepare_scope_ref','prepare_audit_ref','source_package_hdf_ref','source_package_mf_ref','source_contract_ref'}, 'REQUEST_FIELDS')
    need(req['schema'] == 'researchos.main24-compose-request.v2' and req['actor_id'] == 'codex:/root', 'ROOT_REQUEST')
    need(Path(req['repo_root']) == REPO and req['native_revision'] == NATIVE, 'EXACT_REPO_NATIVE')
    identity(req['project_identity_ref'])
    add_ref(refs, req['project_identity_ref'])
    own = safe_path(Path(__file__).resolve(), True)
    need(Path(req['source_helper_ref']['path']) == own, 'HELPER_SOURCE_PATH')
    add_ref(refs, req['source_helper_ref'])
    need(Path(req['merge_map_ref']['path']) == MERGE and req['merge_map_ref']['sha256'] == MERGE_SHA, 'FIXED_MERGE_MAP')
    mapping = decode(add_ref(refs, req['merge_map_ref']))
    need(mapping['selected_native_revision'] == NATIVE, 'MAP_NATIVE')
    rows = mapping['files']
    need(len(rows) == 40 and tuple(row['repo_relative_path'] for row in rows) == PATHS, 'EXACT_ORDERED40')
    need(sum(row['current_ref'] is not None for row in rows) == 10, 'TEN_OLD_THIRTY_NEW')
    composition = decode(add_ref(refs, mapping['composition_ref']))
    for layer in composition['tiers']:
        add_ref(refs, layer['HDF_ref']); add_ref(refs, layer['MF_ref'])
        for item in layer['files']:
            add_ref(refs, item['source_ref'])
    for item in composition['handoff_targets']:
        add_ref(refs, item['candidate_ref'])
    edits = {}
    for row in rows:
        rel = row['repo_relative_path']
        need(composition['proposed_final_files'][rel]['source_ref'] == row['expected_composed_ref'], 'FINAL_LAYER_BINDING')
        add_ref(refs, row['expected_composed_ref'])
        if row['current_ref'] is not None:
            need(Path(row['current_ref']['path']) == target(rel) and row['action'] == 'APPLY_PINNED_INCREMENT', 'OLD_TARGET_BINDING')
            ed = decode(add_ref(refs, row['byte_edit_suggestion_ref']))
            need(ed['repo_relative_path'] == rel and ed['required_current_ref'] == row['current_ref'] and ed['expected_result_ref'] == row['expected_composed_ref'], 'EXACT_EDIT_BINDING')
            edits[rel] = ed
            add_ref(refs, row['source_ancestor_evidence']['evidence_ref'])
        else:
            need(row['action'] == 'ADD_ONLY_IF_STILL_ABSENT', 'NEW_ONLY')
    out = safe_path(req['output_directory'])
    need(out.parent == RUN_PARENT and RUN_NAME.fullmatch(out.name) is not None, 'OUTPUT_SCOPE')
    need(sha(GUARD.read_bytes()) == GUARD_SHA, 'SOURCE_GUARD_PIN')
    add_ref(refs, pin(GUARD))
    validate_source_package(req,refs)
    verify_prepare_authority(req,refs)
    verify_git_baseline(req,refs)
    return req, rows, edits, refs, out

def preflight(rows, edits, locked=None):
    originals, desired, inverse = {}, {}, {}
    for row in rows:
        rel = row['repo_relative_path']; path = target(rel)
        _, source = checked(row['expected_composed_ref'])
        if row['current_ref'] is None:
            need(not path.exists(), 'NEW_PATH_EXISTS:' + rel)
            desired[rel] = source
            inverse[rel] = dict(kind='REMOVE_ONLY_AFTER_SEPARATE_ROOT_AUTHORIZATION',required_current_sha256=sha(source),automatic=False)
        else:
            safe_path(path, True)
            old = locked[rel].read() if locked is not None else path.read_bytes()
            need(pin(path, old) == row['current_ref'], 'MAIN_BASE_DRIFT:' + rel)
            new, back = apply_edits(old, edits[rel])
            need(new == source, 'EDIT_NOT_FINAL_SOURCE')
            originals[rel], desired[rel] = old, new
            inverse[rel] = dict(kind='RESTORE_OLD_ONLY_AFTER_SEPARATE_ROOT_AUTHORIZATION',required_current_sha256=sha(new),inverse_byte_edits=back,original_sha256=sha(old),automatic=False)
    return originals, desired, inverse

def prepare(request_ref):
    req, rows, edits, refs, out = input_bundle(request_ref)
    need(not out.exists(), 'PREPARE_OUTPUT_EXISTS')
    originals, desired, inverse = preflight(rows, edits)
    # Preparation writes only its new evidence output namespace, never target files.
    out.mkdir()
    manifest_rows = []
    for number, row in enumerate(rows):
        rel = row['repo_relative_path']; stem = str(number).zfill(2)
        oldref = save(out/'before'/ (stem+'.raw'), originals[rel]) if rel in originals else None
        newref = save(out/'desired'/ (stem+'.raw'), desired[rel])
        manifest_rows.append(dict(repo_relative_path=rel,current_ref=row['current_ref'],old_archive_ref=oldref,
            desired_archive_ref=newref,expected_composed_ref=row['expected_composed_ref'],inverse=inverse[rel]))
    inverse_ref = document(out/'inverse.json',dict(schema='researchos.main24-complete-inverse.v1',
        operations=[dict(repo_relative_path=r['repo_relative_path'],**r['inverse'],old_archive_ref=r['old_archive_ref']) for r in manifest_rows],
        automatic_rollback=False,not_an_execution_grant=True))
    # Recheck all sources and the whole forty-target preflight after archival.
    for ref in refs.values():
        checked(ref)
    preflight(rows, edits)
    verify_prepare_authority(req,refs)
    verify_git_baseline(req)
    prepared = dict(schema='researchos.main24-composition-prepared.v1',status='PREPARED_NOT_APPLIED',
        request_ref=request_ref,source_helper_ref=req['source_helper_ref'],project_id=PROJECT,repo_root=str(REPO),
        merge_map_ref=req['merge_map_ref'],source_refs=list(refs.values()),files=manifest_rows,inverse_ref=inverse_ref,
        grant_ref=None,TargetProgram=None,build_result_ref=None,test_result_ref=None,Main_applied=False)
    prepared_ref = document(out/'prepared.json',prepared)
    document(out/'prepare-journal.json',dict(status='PREPARED_ONLY',prepared_ref=prepared_ref,
        old_backups=10,desired_files=40,all_old_bytes_archived=True,automatic_rollback=False,automatic_retry=False))
    return dict(status='PREPARED_NOT_APPLIED',prepared_ref=prepared_ref,Main_writes=0)

class WriteHandle:
    """Windows deny-other-write/delete existing handle; CREATE_NEW is xb semantics.
    Class definition/import performs no IO. Instances open handles only in Root apply.
    """
    def __init__(self, path, create=False):
        from ctypes import wintypes
        import msvcrt
        need(os.name == 'nt', 'WINDOWS_ONLY')
        self.path = safe_path(path)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create_file = kernel.CreateFileW
        create_file.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        create_file.restype = wintypes.HANDLE
        close = kernel.CloseHandle; close.argtypes=[wintypes.HANDLE];close.restype=wintypes.BOOL
        final = kernel.GetFinalPathNameByHandleW
        final.argtypes=[wintypes.HANDLE,wintypes.LPWSTR,wintypes.DWORD,wintypes.DWORD];final.restype=wintypes.DWORD
        handle = create_file(str(path),0x80000000|0x40000000,1,None,1 if create else 3,0x80,None)
        if handle in (None,ctypes.c_void_p(-1).value):
            raise OSError(ctypes.get_last_error(),'CreateFileW CREATE_NEW' if create else 'CreateFileW OPEN_EXISTING')
        fd = None
        try:
            buf=ctypes.create_unicode_buffer(32768);size=final(handle,buf,len(buf),0)
            need(0<size<len(buf),'HANDLE_FINAL_PATH')
            value=buf.value
            if value.startswith('\\\\?\\'):
                value=value[4:]
            need(path_key(Path(value))==path_key(path),'HANDLE_PATH_MISMATCH')
            fd=msvcrt.open_osfhandle(int(handle),os.O_RDWR|os.O_BINARY);handle=None
            self.stream=os.fdopen(fd,'r+b',buffering=0);fd=None
            need(os.fstat(self.stream.fileno()).st_nlink==1,'HANDLE_SINGLE_LINK')
        except BaseException:
            if fd is not None:os.close(fd)
            if handle is not None:close(handle)
            if getattr(self,'stream',None) is not None:self.stream.close()
            raise
    def read(self):
        self.stream.seek(0);return self.stream.read()
    def write(self, raw):
        self.stream.seek(0)
        view=memoryview(raw)
        while view:
            n=self.stream.write(view)
            need(n is not None and n>0,'SHORT_WRITE')
            view=view[n:]
        self.stream.truncate(len(raw));self.stream.flush();os.fsync(self.stream.fileno())
        need(self.read()==raw,'TARGET_READBACK')
    def close(self):
        self.stream.close()

@contextmanager
def serial_apply_lock():
    import msvcrt
    lock = safe_path(Path(__file__).resolve().parent/'root-main24-composition.lock')
    try:save(lock,b'0')
    except FileExistsError:pass
    with lock.open('r+b') as stream:
        need(stream.read(1)==b'0','LOCK_FORMAT');stream.seek(0)
        msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        try:yield
        finally:
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)

def parse_stamp(value):
    value=datetime.fromisoformat(value.replace('Z','+00:00'))
    need(value.tzinfo is not None,'TIMEZONE_REQUIRED')
    return value

def apply(prepared_ref, grant_ref):
    need(os.name == 'nt','ROOT_WINDOWS_APPLY')
    prepared_path, prepared_raw = checked(prepared_ref); prepared=decode(prepared_raw)
    need(prepared['schema']=='researchos.main24-composition-prepared.v1' and prepared['status']=='PREPARED_NOT_APPLIED','PREPARED_SCHEMA')
    req, rows, edits, refs, prepared_out=input_bundle(prepared['request_ref'])
    need(prepared_path == prepared_out/'prepared.json' and prepared['source_helper_ref']==req['source_helper_ref'],'PREPARED_SCOPE')
    _,grant_raw=checked(grant_ref);grant=decode(grant_raw)
    need(set(grant)=={'schema','issued_by','project_id','operation_id','source_helper_ref','prepared_ref','independent_source_review_ref','root_authorization_observation_ref','target_paths','issued_at','expires_at','source_review_audit_ref','root_authorization_audit_ref','independent_source_review_hdf_ref','independent_source_review_mf_ref'},'GRANT_FIELDS')
    need(grant['schema']=='researchos.root-main24-composition-grant.v2' and grant['issued_by']=='codex:/root' and grant['project_id']==PROJECT,'ROOT_GRANT')
    need(grant['source_helper_ref']==req['source_helper_ref'] and grant['prepared_ref']==prepared_ref and tuple(grant['target_paths'])==PATHS,'GRANT_BINDING')
    need(re.fullmatch('[0-9a-f]{32}',grant['operation_id']) is not None,'OPERATION_ID')
    now=datetime.now(timezone.utc);issued=parse_stamp(grant['issued_at']);expires=parse_stamp(grant['expires_at'])
    need(issued<=now<expires and 0<(expires-issued).total_seconds()<=3600,'FINITE_GRANT')
    # V2 verifies canonical original audit bytes, typed Root observation and exact independent approval.
    verify_apply_authority(grant,req,prepared,prepared_ref,refs)
    add_ref(refs,grant_ref);add_ref(refs,grant['independent_source_review_ref']);add_ref(refs,grant['root_authorization_observation_ref'])
    add_ref(refs,prepared_ref);add_ref(refs,prepared['inverse_ref'])
    need(tuple(x['repo_relative_path'] for x in prepared['files'])==PATHS and len(prepared['files'])==40,'PREPARED_TARGET40')
    for expected, actual in zip(rows,prepared['files']):
        need(actual['current_ref']==expected['current_ref'] and actual['expected_composed_ref']==expected['expected_composed_ref'],'PREPARED_ROW_BINDING')
        if actual['old_archive_ref'] is not None:add_ref(refs,actual['old_archive_ref'])
        add_ref(refs,actual['desired_archive_ref'])
    # Every immutable Source/archive/grant input is held; mutable Main targets are opened separately.
    need(not any(path_key(Path(r['path'])) in {path_key(target(x)) for x in PATHS} for r in refs.values()),'MAIN_NOT_IN_READ_GUARD')
    guard_raw=GUARD.read_bytes();need(sha(guard_raw)==GUARD_SHA,'SOURCE_GUARD_PIN')
    module=types.ModuleType('main24_compose_source_guard')
    exec(compile(guard_raw,str(GUARD),'exec'),module.__dict__)
    guard=module.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    out=prepared_out/('apply-'+grant['operation_id'])
    need(not out.exists(),'NO_RETRY_OUTPUT_EXISTS')
    out.mkdir()
    handles={};completed=[];attempted=None;primary=None;cleanup=[];guard_closed=None
    try:
        guard.acquire(list(refs.values()))
        with serial_apply_lock():
            # Recheck actual authority while all immutable proof dependencies are held.
            verify_prepare_authority(req,refs)
            verify_apply_authority(grant,req,prepared,prepared_ref,refs)
            # All ten existing files are opened deny-write/delete before the all-40 preflight.
            for row in rows:
                if row['current_ref'] is not None:
                    rel=row['repo_relative_path'];handles[rel]=WriteHandle(target(rel))
            originals,desired,inverse=preflight(rows,edits,handles)
            verify_git_baseline(req)
            for row,archived in zip(rows,prepared['files']):
                rel=row['repo_relative_path']
                need(checked(archived['desired_archive_ref'])[1]==desired[rel],'DESIRED_ARCHIVE_DRIFT')
                need(archived['inverse']==inverse[rel],'EXACT_INVERSE_ARCHIVE_BINDING')
                if rel in originals:need(checked(archived['old_archive_ref'])[1]==originals[rel],'OLD_ARCHIVE_DRIFT')
            inverse_doc=decode(checked(prepared['inverse_ref'])[1])
            need(inverse_doc==dict(schema='researchos.main24-complete-inverse.v1',
                operations=[dict(repo_relative_path=r['repo_relative_path'],**r['inverse'],old_archive_ref=r['old_archive_ref']) for r in prepared['files']],
                automatic_rollback=False,not_an_execution_grant=True),'COMPLETE_INVERSE_DOCUMENT')
            document(out/'intent.json',dict(schema='researchos.main24-apply-intent.v1',
                prepared_ref=prepared_ref,grant_ref=grant_ref,all40_preflight_passed=True,
                existing_handles_held=10,status='PENDING_NOT_APPLIED',automatic_rollback=False,automatic_retry=False))
            for number,row in enumerate(rows):
                rel=row['repo_relative_path'];path=target(rel);attempted=rel
                need(datetime.now(timezone.utc)<expires,'GRANT_EXPIRED_DURING_APPLY')
                document(out/(str(number).zfill(2)+'.intent.json'),dict(path=rel,current_ref=row['current_ref'],
                    desired_sha256=sha(desired[rel]),operation=row['action']))
                if row['current_ref'] is None:
                    need(not path.exists(),'NEW_PATH_APPEARED:'+rel)
                    path.parent.mkdir(parents=True,exist_ok=True);safe_path(path.parent)
                    handle=WriteHandle(path,create=True);handles[rel]=handle
                    handle.write(desired[rel])
                else:
                    handle=handles[rel];current=handle.read()
                    need(pin(path,current)==row['current_ref'],'LATE_MAIN_BASE_DRIFT:'+rel)
                    merged,_=apply_edits(current,edits[rel])
                    need(merged==desired[rel],'LATE_INCREMENT_RESULT')
                    handle.write(merged)
                safe_path(path,True)
                receipt=document(out/(str(number).zfill(2)+'.written.json'),dict(path=rel,
                    actual_ref=pin(path,handle.read()),file_identity=list(os.fstat(handle.stream.fileno())[0:3]),
                    completed=True,formal_acceptance=False))
                completed.append(dict(path=rel,receipt_ref=receipt));attempted=None
            for row in rows:
                rel=row['repo_relative_path'];need(handles[rel].read()==desired[rel],'FINAL40_READBACK:'+rel)
            result=document(out/'applied.json',dict(schema='researchos.main24-composition-applied.v1',
                status='APPLIED_PENDING_BUILD_TEST_AND_INDEPENDENT_REVIEW',prepared_ref=prepared_ref,grant_ref=grant_ref,
                completed=completed,completed_count=40,TargetProgram=None,build_result_ref=None,test_result_ref=None,
                formal_acceptance=False,Canon_written=False,automatic_rollback=False))
    except BaseException as exc:
        primary=dict(type=type(exc).__name__,message=str(exc),attempted_path=attempted,
            completed=completed,completed_count=len(completed),status='STOPPED_PRESERVE_PARTIAL',
            automatic_rollback=False,automatic_retry=False,Main_may_be_partial=True)
        try:document(out/'failure.json',primary)
        except BaseException as secondary:cleanup.append(dict(stage='failure_persistence',error=repr(secondary)))
    finally:
        for rel,handle in reversed(list(handles.items())):
            try:handle.close()
            except BaseException as exc:cleanup.append(dict(stage='target_handle_close',path=rel,error=repr(exc)))
        try:
            guard_closed=guard.close()
            if not guard_closed.get('closed') or guard_closed.get('retained_handles_count')!=0 or guard_closed.get('errors'):
                cleanup.append(dict(stage='source_guard_close',result=guard_closed))
            document(out/'source-guard.closed.json',guard_closed)
        except BaseException as exc:cleanup.append(dict(stage='source_guard_close_or_persistence',error=repr(exc)))
        try:document(out/'outcome.json',dict(primary_failure=primary,cleanup_errors=cleanup,completed_count=len(completed),
            status='FAILED_PARTIAL_PRESERVED' if primary or cleanup else 'APPLIED_PENDING_BUILD_TEST_AND_REVIEW',
            automatic_rollback=False,automatic_retry=False))
        except BaseException as exc:cleanup.append(dict(stage='outcome_persistence',error=repr(exc)))
    if primary or cleanup:
        print(json.dumps(dict(primary_failure=primary,cleanup_errors=cleanup,out=str(out),automatic_rollback=False),ensure_ascii=False))
        return 1
    print(json.dumps(dict(result_ref=result,status='APPLIED_PENDING_BUILD_TEST_AND_REVIEW',out=str(out)),ensure_ascii=False))
    return 0

def cli_ref(path,digest,size):
    return dict(path=path,sha256=digest,bytes=size)

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare')
    for name in ('request',):
        prep.add_argument('--'+name,required=True);prep.add_argument('--'+name+'-sha256',required=True);prep.add_argument('--'+name+'-bytes',type=int,required=True)
    app=sub.add_parser('apply')
    for name in ('prepared','grant'):
        app.add_argument('--'+name,required=True);app.add_argument('--'+name+'-sha256',required=True);app.add_argument('--'+name+'-bytes',type=int,required=True)
    args=parser.parse_args()
    if args.mode=='prepare':
        result=prepare(cli_ref(args.request,args.request_sha256,args.request_bytes))
        print(json.dumps(result,ensure_ascii=False));return 0
    return apply(cli_ref(args.prepared,args.prepared_sha256,args.prepared_bytes),cli_ref(args.grant,args.grant_sha256,args.grant_bytes))

if __name__=='__main__':
    sys.exit(main())

