"""Preserve the original builder block including all string-literal indentation."""
from pathlib import Path
N=Path(__file__).resolve().parent
raw=(N/'continue_caller.py').read_text(encoding='utf-8')
before="body='\\n'.join(line[1:] if line.startswith(' ') else line for line in original_builder[start:end].splitlines())"
after="body='if True:\\n'+original_builder[start:end]"
assert before in raw
raw=raw.replace(before,after).replace("N/'source-guard-corrected.closed.json'","N/'source-guard-corrected-v2.closed.json'")
exec(compile(raw,str(N/'continue_caller.py'),'exec'),{'__file__':str(N/'continue_caller.py'),'__name__':'bounded_caller_continuation_v2'})

