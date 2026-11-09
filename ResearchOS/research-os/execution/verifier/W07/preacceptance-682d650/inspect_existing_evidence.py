import hashlib
import json
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent / 'snapshot'
RUNS = ['run-b4cb609929024e02b3bda5d20619f07a', 'run-ed654d3301f94890ad46ed978e24a44e']
results = []
for run in RUNS:
    folder = ROOT / 'execution/receipts/W07' / run
    summary = json.loads((folder / 'report.json').read_text(encoding='utf-8'))
    row = {'run': run, 'reported_status': summary['status'], 'execution_head': summary['execution_head'],
           'reported_assertion_ids': summary.get('assertion_ids'), 'sources': []}
    for kind in ['GITHUB', 'PAPER', 'X']:
        report = json.loads((folder / ('report-' + kind + '.json')).read_text(encoding='utf-8'))
        db_path = folder / ('live-' + kind + '.sqlite')
        actual_hash = 'sha256:' + hashlib.sha256(db_path.read_bytes()).hexdigest()
        expected_hash = summary.get('live', {}).get('reports', {}).get(kind, {}).get('db_sha256')
        db = sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        source = {'source': kind, 'reported_status': report['status'], 'failure': report.get('failure'),
                  'db_sha256': actual_hash, 'reported_db_sha256': expected_hash,
                  'db_hash_matches_if_recorded': actual_hash == expected_hash if expected_hash else None,
                  'requested_window': [report.get('window_from'), report.get('window_to')],
                  'observed_window': [report.get('observed_from'), report.get('observed_to')],
                  'complete': report['page_complete'], 'items': []}
        def artifact(artifact_id):
            record = db.execute("SELECT d.body,u.bytes FROM domain_objects d JOIN uploaded_content u "
                                "ON u.storage_key=json_extract(d.body,'$.storage_key') "
                                "WHERE d.kind='Artifact' AND d.id=?", (artifact_id,)).fetchone()
            meta, content = json.loads(record[0]), record[1]
            actual = 'sha256:' + hashlib.sha256(content).hexdigest()
            return meta, content, actual
        for field in ['raw_page', 'manifest']:
            if report.get(field):
                meta, content, digest = artifact(report[field]['artifact_id'])
                source[field + '_hash_matches'] = digest == report[field]['sha256'] == meta['content_hash']
        for item in report.get('items', []):
            meta, content, digest = artifact(item['artifact_ref']['id'])
            ev = json.loads(db.execute("SELECT body FROM domain_objects WHERE kind='Evidence' AND id=?",
                                       (item['evidence_id'],)).fetchone()[0])
            observed = {'url': item['url'], 'body_bytes': len(content), 'body_sha256': digest,
                        'hash_matches': digest == item['body_sha256'] == meta['content_hash'],
                        'stance': ev['stance'], 'verification_status': ev['verification_status'],
                        'origin_evidence_id': ev['origin_evidence_id']}
            if kind == 'X':
                text = content.decode('utf-8')
                begin = text.index('#2 paperclipai/paperclip')
                observed['claim_excerpt'] = text[begin:text.index('Model selection', begin)].strip()
            if kind == 'GITHUB':
                observed['release_summary'] = content.decode('utf-8').split('## Fixes')[0].strip()
            source['items'].append(observed)
        db.close()
        row['sources'].append(source)
    results.append(row)
print(json.dumps({'mode': 'READ_ONLY_EXISTING_EVIDENCE', 'results': results}, ensure_ascii=False, indent=2))
