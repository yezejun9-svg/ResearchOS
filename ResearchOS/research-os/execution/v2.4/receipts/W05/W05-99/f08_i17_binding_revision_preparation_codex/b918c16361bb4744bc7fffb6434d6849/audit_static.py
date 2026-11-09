"""Meaningful static byte/data checks only; Python AST, no Go AST/compiler."""
from pathlib import Path
import ast
import base64
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent

def reference(p):
    b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def dump(name,value):
    (OUT/name).write_bytes(json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')+b'\n')
def load(name):return json.loads((OUT/name).read_bytes())

def apply_unified(original,patch):
    src=original.decode('utf-8').splitlines(keepends=True);lines=patch.decode('utf-8').splitlines(keepends=True)
    result=[];cursor=0;i=2
    while i<len(lines):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert m,lines[i]
        start=int(m[1]);count=int(m[2] or 1);idx=start-1 if count else start
        assert idx>=cursor
        result.extend(src[cursor:idx]);cursor=idx;i+=1;old_count=0;new_count=0
        while i<len(lines) and not lines[i].startswith('@@'):
            mark,body=lines[i][0],lines[i][1:]
            if mark in ' -':assert cursor<len(src) and src[cursor]==body,(cursor,repr(src[cursor]),repr(body));cursor+=1;old_count+=1
            if mark in ' +':result.append(body);new_count+=1
            assert mark in ' +-';i+=1
        assert old_count==count
        assert new_count==int(m[4] or 1)
    result.extend(src[cursor:]);return ''.join(result).encode('utf-8')

def mask_go(text):
    # Lexically remove comments/strings, preserving byte position and newlines.
    # Structural delimiter check is explicitly not a Go AST or compilation.
    out=list(text);i=0
    while i<len(text):
        if text.startswith('//',i):
            end=text.find('\n',i);end=len(text) if end<0 else end
        elif text.startswith('/*',i):
            j=text.find('*/',i+2);assert j>=0;end=j+2
        elif text[i] in ('"',"'",'`'):
            quote=text[i];j=i+1
            while j<len(text):
                if quote!='`' and text[j]=='\\':j+=2;continue
                if text[j]==quote:break
                j+=1
            assert j<len(text);end=j+1
        else:i+=1;continue
        for k in range(i,end):
            if text[k] not in '\r\n':out[k]=' '
        i=end
    return ''.join(out)

def functions(text):
    masked=mask_go(text);stack=[];pairs={};match={')':'(',']':'[','}':'{'}
    for i,c in enumerate(masked):
        if c in '([{':stack.append((c,i))
        elif c in ')]}':
            assert stack and stack[-1][0]==match[c],(c,i)
            _,start=stack.pop();pairs[start]=i
    assert not stack
    funcs={}
    for m in re.finditer(r'\bfunc\s*(?:\([^\n]*?\)\s*)?(\w+)\s*\(',masked):
        # Function declarations in these files have bodies; skips anonymous funcs.
        brace=masked.find('{',m.end());assert brace>=0
        funcs[m[1]]=text[m.start():pairs[brace]+1].replace('\r\n','\n')
    return funcs

results={'schema':'researchos.f08.i17.static-byte-audit.v1','status':'STATIC_CHECKED_SOURCE_PREPARATION_ONLY','Go_AST_compile_gofmt_SQL_native_calls':0,'checks':{}}
changes=load('changes.json')
for change in changes:
    before=Path(change['before']['path']).read_bytes();after=Path(change['after']['path']).read_bytes()
    assert apply_unified(before,Path(change['forward']['path']).read_bytes())==after
    assert apply_unified(after,Path(change['inverse']['path']).read_bytes())==before
results['checks']['whole_byte_forward_and_inverse']=True
driver_before=functions((OUT/'innocuous_test.go.before.txt').read_text(encoding='utf-8'))
driver_after=functions((OUT/'innocuous_test.go.proposed.txt').read_text(encoding='utf-8'))
unchanged_driver=[f'TestDriverI{i:02d}' for i in range(1,19) if i!=17]
for name in unchanged_driver:assert driver_before[name]==driver_after[name],name
assert 'driver18Error(t,err,275' not in driver_after['TestDriverI17']
assert 'f.integer(t,query,0,bad...)' not in driver_after['TestDriverI17']
assert 'direct!=nil||directErr==nil||directErr.Error()!=v.FixedCallbackError' in driver_after['TestDriverI17']
assert 'SELECT count(*) FROM ' in driver_after['TestDriverI17']
assert 'var driver18F08Bindings func()' in (OUT/'innocuous_test.go.proposed.txt').read_text()
results['checks']['driver_17_only_assertion_revision_other17_test_bodies_unchanged']=unchanged_driver

tests_before=functions((OUT/'client_cancel_finalization_test.v4.go.before.txt').read_text(encoding='utf-8'))
tests_after=functions((OUT/'client_cancel_finalization_test.v4.go.proposed.txt').read_text(encoding='utf-8'))
existing_tests=[name for name in tests_before if name.startswith('Test')]
for name in existing_tests:assert tests_before[name]==tests_after[name],name
for name in ['f08FullJournalDataFixture','f08TestDataSetup','step','put','graph','materialize','f08FixtureClone']:
    body=tests_after[name]
    assert 'evaluate(' not in body and 'f08BuildCallbacks(' not in body,name
assert 'frames=append' in tests_after['step'] and 'bytes.Clone(raw)' in tests_after['step']
assert 'f08FullJournalDataFixture' in tests_after['f08FullJournalFixture']
assert tests_after['f08FullJournalFixture'].index('f08FullJournalDataFixture')<tests_after['f08FullJournalFixture'].index('.evaluate(')
assert 'f08Strict(' not in tests_after['f08FixtureClone']
results['checks']['all_v3_Test_bodies_unchanged']=existing_tests
results['checks']['construct_freeze_before_replay_no_predicate_in_data_construction']=True

harnesspath=OUT/'client_cancel_finalization_i17_integration_test.go.proposed.txt'
harness=harnesspath.read_text(encoding='utf-8');functions(harness)
assert harness.startswith('package domain\n')
assert 'RegisterFunction(' not in harness
assert 'f08BuildCallbacks(backupConfigurationProtocol,backupConfigurationDomain)' in harness
assert 'PRAGMA trusted_schema=OFF' in harness and 'pragma_function_list' in harness and 'flags!=2099200' in harness
assert 'direct!=nil||e==nil||e.Error()!=v.FixedCallbackError' in harness
assert 'native.Code()&255' in harness and 'after!=count' in harness
assert 'TestF08I17ProducerFreeze' in harness
assert not re.search(r'\bfunc\s+F08\w*',harness)
assert 'FATAL_OPEN' in harness
assert 't.Parallel(' not in harness and 'os/exec' not in harness
results['checks']['domain_private_factory_real_init_names_genuine_SQL_error_and_registration']=True

# Exact new-file forward and inverse artifact; before is ABSENT, not a claimed
# pre-existing empty product file. These diffs are never installed here.
raw=harnesspath.read_bytes();hname='client_cancel_finalization_i17_integration_test.go'
import difflib
forward=''.join(difflib.unified_diff([],raw.decode().splitlines(keepends=True),fromfile='/dev/null',tofile='internal/domain/'+hname)).encode()
inverse=''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),[],fromfile='internal/domain/'+hname,tofile='/dev/null')).encode()
(OUT/(hname+'.forward.patch')).write_bytes(forward);(OUT/(hname+'.inverse.patch')).write_bytes(inverse)
assert apply_unified(b'',forward)==raw and apply_unified(raw,inverse)==b''
results['new_harness_change']={'before':'ABSENT','after':reference(harnesspath),'forward':reference(OUT/(hname+'.forward.patch')),'inverse':reference(OUT/(hname+'.inverse.patch'))}

manifest=load('vector-manifest.json');seen=set();function_counts={n:0 for n in manifest['names']}
for v in manifest['vectors']:
    assert v['id'] not in seen;seen.add(v['id']);function_counts[v['function']]+=1
    assert v['status']=='SOURCE_DERIVED_NOT_RUN' and v['corrupt_kind']=='CALLBACK_ERROR'
    assert v['expected_sqlite_primary_code']==1 and v['sqlite_code_evidence']=='SOURCE_INFERENCE_NOT_NATIVE_RUN'
    assert v['valid_expected']=={'driver_type':'int64','value':1}
    assert len(v['valid'])==len(v['corrupt']) and v['valid']!=v['corrupt']
    for a in v['valid']+v['corrupt']:
        if a['kind']=='BLOB':assert reference(Path(a['ref']['path']))==a['ref']
        else:assert a['kind'] in ['NULL','INTEGER','TEXT']
    assert v['provenance']['predicate_executions']==0
assert all(function_counts.values())
seqs=load('raw-sequences.json');transitions=0
for seq in seqs['sequences']:
    assert not seq['actual_sql_native_capture'];assert len(seq['frames'])>=20
    for frame in seq['frames']:
        raw=Path(frame['go_producer_raw']['path']).read_bytes();data=json.loads(raw)
        assert set(data)=={'action','row','old','sources'}
        assert frame['action']==data['action'] and frame['row_width']==len(data['row'])
        assert len(frame['category_counts_all34'])==34
        assert sum(frame['category_counts_all34'].values())==len(data['sources'])
        assert not frame['sql_native_bytes_proven'] and not frame['storage_types_before_cast_runtime_proven']
        if data['action'].endswith('.update'):assert data['old'] is not None and len(data['old'])==len(data['row'])
        else:assert data['old'] is None
        for cat,row in data['sources']:
            if cat=='idempotency':assert row[9]==seq['body_type'] and row[10]=='text'
        transitions+=1
results['checks']['raw_args_refs_types_original_nulls_journal_type_and_34category_counts']=True
results['vector_count']=len(seen);results['function_vector_counts']=function_counts;results['pretransition_frame_count']=transitions
provenance=load('fixture-provenance.json');env=(OUT/'raw/request.original-envelope.json').read_bytes()
header=json.loads((OUT/'raw/request.private-header.json').read_bytes())
assert base64.b64decode(header['raw_envelope_base64'],validate=True)==env
assert provenance['request_hash']!=provenance['raw_envelope_digest']
results['checks']['private_header_padded_base64_exact_original_request_hash_contract_distinct_from_raw_digest']=True

for script in ['prepare_binding.py','audit_static.py']:
    ast.parse((OUT/script).read_text(encoding='utf-8'),filename=script)
results['checks']['Python_AST_parse_only']=True
before=load('inputs.before.json');after=load('inputs.after.json');assert before==after
for r in before:assert reference(Path(r['path']))==r
results['checks']['all46_selected_inputs_still_byte_exact']=True
results['checks']['v5_DDL_whole_byte_unchanged']=reference(OUT/'v5-candidate.sql.unchanged.txt')['sha256']=='e3d58e53a76d00cfecb5cf139320f09055c0996c88616e288a49cfdd2ca07736'
assert results['checks']['v5_DDL_whole_byte_unchanged']
dump('static-byte-audit.json',results)
print(json.dumps({'status':results['status'],'vectors':len(seen),'frames':transitions,'existing_v3_Test_bodies_unchanged':len(existing_tests),'other_driver_tests_unchanged':len(unchanged_driver),'inverse_bytes_exact':True,'Go_AST_compile_SQL_executed':False},ensure_ascii=False))
