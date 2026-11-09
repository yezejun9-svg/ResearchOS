from pathlib import Path
OUT=Path(__file__).parent
p=OUT/'independent-node.cjs'
s=p.read_text(encoding='utf-8')
old='module:{exports:{}},exports:{},Buffer,TextDecoder,console};'
assert s.count(old)==1
s=s.replace(old,'module:{exports:{}},exports:{},Buffer,TextDecoder,console,setTimeout,clearTimeout};')
old='await nativeClosureCases();await streamingCases();await wireCases();await ipcCases();'
assert s.count(old)==1
s=s.replace(old,old+'await extraCases();')
s+='\n'+(OUT/'additional-node-cases.txt').read_text(encoding='utf-8')
p.write_text(s,encoding='utf-8',newline='')
print('FROZEN_V2_HARNESS_ADAPTED_FOR_NEW_TIMER_DEPENDENCY_AND_ADDITIONAL_NEGATIVES; no tests run')
