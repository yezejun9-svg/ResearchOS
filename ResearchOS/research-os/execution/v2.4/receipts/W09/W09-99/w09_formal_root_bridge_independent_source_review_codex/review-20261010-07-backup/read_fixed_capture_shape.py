import hashlib
import json
from pathlib import Path

path = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.bridge07-source-author.original.raw.jsonl')
try:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '8345bdbc50969ce1eecd04ed2ac5b8b5496c58265a25271329f044b34208f313'
    assert len(raw) == 27512
    rows = [json.loads(line) for line in raw.splitlines()]
    output = []
    for i, row in enumerate(rows):
        payload = row.get('payload')
        item = {'row': i, 'keys': list(row), 'timestamp': row.get('timestamp'), 'ordinal': row.get('ordinal'), 'type': row.get('type'), 'payload_type': type(payload).__name__}
        if isinstance(payload, dict):
            item['payload_keys'] = list(payload)
            if i == 2:
                item['small_fields'] = {k: v for k, v in payload.items() if isinstance(v, (str, int, bool)) and len(str(v)) < 200}
                for k, v in payload.items():
                    if isinstance(v, str) and len(v) >= 200:
                        item[k + '_prefix'] = v[:350]
        output.append(item)
    print(json.dumps(output, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
