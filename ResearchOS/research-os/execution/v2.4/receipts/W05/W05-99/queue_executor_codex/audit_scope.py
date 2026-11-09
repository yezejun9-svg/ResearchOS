from pathlib import Path
import json,hashlib,difflib
root=Path(__file__).parent
scope=json.loads(Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_legacy_target_fixture_scope_amendment.json').read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
report={}
for p,spans in scope['minimal_diff_bounds'].items():
    before=(root/(Path(p).name+'.before_target_scope')).read_bytes()
    after=Path(p).read_bytes()
    intervals=[(s['start_byte'],s['end_byte_exclusive']) for s in spans]
    if p==scope['new_helper_insertion']['path']:
        n=scope['new_helper_insertion']['byte_offset'];intervals.append((n,n))
    # Inspect every changed source interval, allowing only registered spans.
    changes=[]
    for op,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if op=='equal':continue
        assert any(x<=a and b<=y for x,y in intervals),(p,op,a,b)
        changes.append({'operation':op,'original_range':[a,b],'new_range':[c,d]})
    segments=scope['protected_existing_bytes'][p]['segments']
    offset=0;verified=[]
    for segment in segments:
        raw=before[segment['start_byte']:segment['end_byte_exclusive']]
        assert sha(raw)==segment['sha256']
        found=after.find(raw,offset)
        assert found>=0,(p,segment)
        offset=found+len(raw)
        verified.append({'sha256':sha(raw),'bytes':len(raw),'new_start':found})
    report[p]={'before_sha256':sha(before),'after_sha256':sha(after),'protected_segments':verified,'changes':changes}
raw=Path('apps/cli/cli_stream_test.go').read_bytes()
suffix=raw[raw.index(b'// Only these composition tests resolve a project Goal binding.'):]
assert sha(suffix)=='9ce153cb99d2252c694665411a71d0ce8c8fce424796e177d99ccd12ad4be862'
report['S5_suffix']={'sha256':sha(suffix),'bytes':len(suffix)}
(root/'scope_boundaries.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Protected legacy segments and S5 suffix verified; exact registered changes only.')
