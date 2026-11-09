from pathlib import Path
import json
P=Path(__file__).resolve().parent
failure={'origin_key':'core-system-drive-independent-suffix-boundary','classification':'INDEPENDENT_FIXTURE_MANIFEST_BOUNDARY_MISMATCH_BEFORE_TEST','raw_tool_chunk':'597ad9','exit_code':1,'tests_executed':0,'detail':'Reviewer hash included the createDesktopManagement marker; author manifest suffix starts after that marker. Direct before/after byte comparison had already passed.','raw':'AssertionError at review.py:24: hashlib.sha256(after[ab:]).hexdigest()==manifest after_environment_suffix_sha256','correction':'Use the same explicit marker boundary as freeze-source.py for the hash; retain direct full prefix/suffix byte equality.'}
assert not (P/'attempt-01-failure.json').exists()
(P/'attempt-01-failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
code=(P/'review.py').read_text()
code=code.replace('R=Path(__file__).resolve().parent',"R=Path(__file__).resolve().parent;R.mkdir(exist_ok=True)")
code=code.replace("A=R.parent/'product-v1-core-system-drive-author-20261104'","A=R.parent.parent/'product-v1-core-system-drive-author-20261104'")
code=code.replace("hashlib.sha256(after[ab:]).hexdigest()==m['preserved_boundaries']['after_environment_suffix_sha256']","hashlib.sha256(after.split(b'\\nfunction createDesktopManagement(options)',1)[1]).hexdigest()==m['preserved_boundaries']['after_environment_suffix_sha256']")
target=P/'attempt-02';target.mkdir(exist_ok=False)
script=target/'review.py';script.write_text(code,encoding='utf-8')
exec(compile(code,str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
