import hashlib
import json
from pathlib import Path

REF = {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.bridge08-source-author.original.raw.jsonl', 'sha256': '1e27755a095e37909bebd69c2deb07781027ecb3eea4582272bee210208896ba', 'bytes': 27917}
def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)

try:
    raw = Path(REF['path']).read_bytes()
    if len(raw) != REF['bytes'] or hashlib.sha256(raw).hexdigest() != REF['sha256']:
        raise ValueError('fixed author capture pin differs')
    lines = raw.splitlines(keepends=True)
    rows = []
    for index, line in enumerate(lines):
        value = json.loads(line)
        nodes = []
        for node in walk(value):
            if node.get('type') in {'inter_agent_communication', 'inter_agent_communication_metadata'} or 'sender' in node or 'author' in node:
                nodes.append({key: node[key] for key in ['type', 'sender', 'recipient', 'author', 'message_id', 'client_authored', 'ordinal', 'timestamp', 'content', 'message'] if key in node and key not in {'content', 'message'}} | {'field_types': {key: type(item).__name__ for key, item in node.items()}})
        rows.append({'index': index, 'root_keys': list(value), 'root_type': value.get('type'), 'timestamp': value.get('timestamp'), 'payload_type': value.get('payload', {}).get('type') if isinstance(value.get('payload'), dict) else None, 'payload_keys': list(value['payload']) if isinstance(value.get('payload'), dict) else None, 'selected_nodes': nodes})
    print(json.dumps({'capture_ref': REF, 'line_count': len(lines), 'rows': rows}, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
