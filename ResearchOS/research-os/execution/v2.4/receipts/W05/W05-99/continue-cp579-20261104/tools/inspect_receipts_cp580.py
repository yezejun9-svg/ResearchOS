import json
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
for relative in ['host-author/author-summary.json','host-author/source-manifest.json','host-author/diagnostics.json','routing-author/author-summary.json','routing-author/diagnostics.json']:
    value=json.loads((out/relative).read_bytes())
    print(json.dumps({'path':relative,'content':value},ensure_ascii=True))
