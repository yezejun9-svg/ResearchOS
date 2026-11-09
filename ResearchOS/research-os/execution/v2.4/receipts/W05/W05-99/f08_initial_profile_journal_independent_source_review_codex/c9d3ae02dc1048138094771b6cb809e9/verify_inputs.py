from pathlib import Path
import json,hashlib,difflib,re
out=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_initial_profile_journal_independent_source_review_codex/c9d3ae02dc1048138094771b6cb809e9');src=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_initial_profile_journal_revision_preparation_codex/bd3fe19a27f54a468431828f267cd02f')
def meta(p):
    b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def checked(ref):
    a=meta(Path(ref['path']));assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes']);return a
mf=meta(src/'manifest.json');hm=meta(src/'handoff.json')
assert (mf['sha256'],mf['bytes'])==('18b7a6dd2e33d6586c374d55f47dea1b93a05c100f3f9c366df0f0ad710a38f1',11886)
assert (hm['sha256'],hm['bytes'])==('b8832c59a594a4fd43fdfe8a04b9fabba46a953f2005411cbf04359e442ce415',7073)
m=json.loads((src/'manifest.json').read_text(encoding='utf-8'));assert len(m['files'])==36
members=[]
for ref in m['files']:
    checked(ref);p=Path(ref['path']);dest=out/'inputs'/p.relative_to(src)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());members.append(ref)
(out/'inputs/manifest.json').write_bytes((src/'manifest.json').read_bytes())
h=json.loads((src/'handoff.json').read_text(encoding='utf-8'));external=[]
def walk(v):
    if isinstance(v,dict):
        if {'path','sha256','bytes'}<=set(v):
            a=checked(v)
            if not Path(v['path']).is_relative_to(src):external.append(a)
        for x in v.values():walk(x)
    elif isinstance(v,list):
        for x in v:walk(x)
walk(h)
base=Path(h['base_source_ref']['path']);bh=json.loads(Path(h['base_handoff_ref']['path']).read_text(encoding='utf-8'))
old=base.read_bytes();new=Path(h['source_ref']['path']).read_bytes()
oldtest=Path(bh['test_proposal_ref']['path']);newtest=Path(h['test_ref']['path'])
checked(bh['test_proposal_ref'])
(out/'base').mkdir(exist_ok=True);(out/'base/source.b9.txt').write_bytes(old);(out/'base/tests.b9.txt').write_bytes(oldtest.read_bytes())
stats={}
for label,original,final in [('source',old,new),('tests',oldtest.read_bytes(),newtest.read_bytes())]:
    a=original.decode('utf-8').splitlines(keepends=True);b=final.decode('utf-8').splitlines(keepends=True)
    sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False);ops=[x for x in sm.get_opcodes() if x[0]!='equal']
    inverse=b[:]
    for tag,i1,i2,j1,j2 in reversed(ops):inverse[j1:j2]=a[i1:i2]
    assert ''.join(inverse).encode('utf-8')==original
    diff=''.join(difflib.unified_diff(a,b,fromfile=label+'-b9',tofile=label+'-v2',n=3))
    (out/(label+'.actual-full-diff.txt')).write_text(diff,encoding='utf-8')
    stats[label]={'base_bytes':len(original),'final_bytes':len(final),'base_lines':len(a),'final_lines':len(b),'inverse_bytes_equal':True,'delta':[{'tag':tag,'old_start':i1+1,'old_end':i2,'new_start':j1+1,'new_end':j2} for tag,i1,i2,j1,j2 in ops]}
before=json.loads((src/'inputs.before.json').read_text(encoding='utf-8'));after=json.loads((src/'inputs.seal-current.json').read_text(encoding='utf-8'))
assert isinstance(before['files'],list) and isinstance(after['files'],list)
bv={r['path']:(r['sha256'],r['bytes']) for r in before['files']};av={r['path']:(r['sha256'],r['bytes']) for r in after['files']}
assert len(bv)==len(av)==161 and bv==av and after['drift_count']==0
public_receipts=[];non_receipts=[]
for ref in before['files']:
    if '/execution/v2.4/receipts/' in ref['path'].replace('\\','/'):public_receipts.append(checked(ref))
    else:non_receipts.append(ref)
record={'member_count':36,'physical_with_manifest':37,'manifest':mf,'handoff':hm,'member_refs':members,'external_handoff_refs_verified':external,'source':h['source_ref'],'test':h['test_ref'],'base':h['base_source_ref'],'base_test':bh['test_proposal_ref'],'full_source_test_bytes_loaded':True,'delta':stats,'public_vector161_equal_sha_bytes':True,'public_receipt_refs_rehashed':public_receipts,'nonreceipt_original_refs_not_read':non_receipts,'not_firstread_or_Main_stdlib_cache_authentication':True,'Go_SQL_native_target_execution':False}
(out/'input-verification.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ['member_refs','external_handoff_refs_verified','public_receipt_refs_rehashed','nonreceipt_original_refs_not_read']},ensure_ascii=True))
print('RECEIPT_REFS_REHASHED '+str(len(public_receipts))+' NONRECEIPT_NOT_READ '+str(len(non_receipts)))
print('FULL_SOURCE_DIFF');print((out/'source.actual-full-diff.txt').read_text(encoding='utf-8'))
print('SOURCE_FUNCTION_INDEX')
for n,line in enumerate(new.decode('utf-8').splitlines(),1):
    if re.match(r'^func(?:\s|\()',line):print(str(n)+':'+line)

