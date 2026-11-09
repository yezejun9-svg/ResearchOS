# Review harness correction only: builder canonical JSON includes a trailing LF.
# Original 018 script, assertion failure and raw records remain unchanged.
from pathlib import Path
original=Path(__file__).with_name('verify_r2_source_before.py').read_text(encoding='utf-8')
old="json.dumps(before['files'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()"
new="(json.dumps(before['files'],sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\\n').encode()"
assert original.count(old)==1
exec(compile(original.replace(old,new),__file__,'exec'))
