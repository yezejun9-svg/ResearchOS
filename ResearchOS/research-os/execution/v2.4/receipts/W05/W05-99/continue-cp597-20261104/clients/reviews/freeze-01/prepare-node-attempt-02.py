from pathlib import Path
import hashlib, json
p = Path(__file__).parent
source = (p/'independent-node.cjs').read_text(encoding='utf-8')
old = "value:reply||{status:'ACKNOWLEDGED',result:null,revision:null}"
new = "value:reply||['object',[['status',['string','ACKNOWLEDGED']],['result',['null']],['revision',['null']]]]"
assert source.count(old) == 1
source = source.replace(old,new)
source = source.replace("'node-independent-checks.json'", "'node-independent-checks-attempt-02.json'")
(p/'independent-node-attempt-02.cjs').write_text(source,encoding='utf-8',newline='')
records = []
for name in ('independent-node.cjs','node-independent.log','node-independent-checks.json','independent-node-attempt-02.cjs'):
    b=(p/name).read_bytes()
    records.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(p/'node-reviewer-harness-diagnostic.json').write_text(json.dumps(dict(
    origin='independent reviewer harness',
    first_tool_terminal='009d44', first_exit=1,
    source_counterexamples_valid=['native-stream/trailing-later-chunk/{}','native-stream/trailing-later-chunk/garbage','ipc-origin-change-after-proof-before-post'],
    harness_only_failure='ipc-replay-fresh-bearer-same-raw-no-secret-storage',
    cause='Mock validator returned plain response object; real wire-values.reify requires typed tree. The actual fake POST observations and stream acceptance counterexamples precede this harness-only response decoding issue.',
    readback_tools=['a8d920','2806bd','99efb6'],
    correction='New separately preserved attempt02 provides a typed ACK tree; actual source control flow and assertions are retained.',
    original_files_retained=True,
    records=records),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='NEW_ATTEMPT_STAGED_ORIGINAL_RETAINED',records=records)))
