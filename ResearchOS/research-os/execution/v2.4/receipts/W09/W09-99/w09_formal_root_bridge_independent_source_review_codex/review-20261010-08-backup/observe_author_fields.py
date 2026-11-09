import hashlib
import json
from pathlib import Path
try:
    raw = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.bridge08-source-author.original.raw.jsonl').read_bytes()
    if len(raw) != 27917 or hashlib.sha256(raw).hexdigest() != '1e27755a095e37909bebd69c2deb07781027ecb3eea4582272bee210208896ba':
        raise ValueError('fixed author capture pin differs')
    final = json.loads(raw.splitlines()[2])
    payload = final['payload']
    content = payload['content']
    print(json.dumps({'ordinal': final['ordinal'], 'metadata': final.get('metadata'), 'passthrough': payload['internal_chat_message_metadata_passthrough'], 'content_items': [{'keys': list(item), 'type': item.get('type'), 'text_prefix': item.get('text', '')[:160]} for item in content]}, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
