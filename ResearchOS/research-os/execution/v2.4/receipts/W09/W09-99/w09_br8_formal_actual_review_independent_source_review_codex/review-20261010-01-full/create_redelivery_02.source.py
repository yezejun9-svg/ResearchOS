from pathlib import Path
import datetime
import hashlib
import json
import uuid

D = Path(__file__).resolve().parent
previous = D / 'redelivery.json'
raw = previous.read_bytes()
assert len(raw) == 3645
assert hashlib.sha256(raw).hexdigest() == 'f8fb8b6cdeefba987d69818db96e8af72cac1f08f65b2357bca6a2381a3381ca'
original = json.loads(raw)
previous_ref = {'path': str(previous), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
delivery = {
    'schema': 'researchos.independent-source-review-redelivery.v1',
    'operation': 'SOURCE_REVIEW_WITNESS_REDELIVERY',
    'redelivery_id': str(uuid.uuid4()),
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
    'review_author': original['review_author'],
    'backend_actor_id': original['backend_actor_id'],
    'actor_thread_id': original['actor_thread_id'],
    'root_thread_id': original['root_thread_id'],
    'previous_redelivery_ref': previous_ref,
    'deliveries': original['deliveries'],
    'original_Root_capture_failures_retained': [1241, 1242, 1244],
    'original_reviews_resealed': False,
    'successful_checks_replayed': False,
    'SourceGuard_controls_replayed': False,
    'new_actual_final_timestamp_predicted': False,
    'original_metadata_or_logs_modified': False,
    'failure_counter_reset': False,
    'retained_handles_count': 0,
    'live_Canon_handles_held': 0,
    'new_product_calls': 0,
    'Main_Canon_Scope_Registry_writes': 0,
    'execution_grant': False,
    'formal_acceptance': False,
    'parent_acceptance': False,
    'STOP': True,
}
body = (json.dumps(delivery, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
target = D / 'redelivery-02.json'
with target.open('xb') as stream:
    stream.write(body)
ref = {'path': str(target), 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)}
print(json.dumps({'redelivery_02_ref': ref, 'previous_redelivery_ref': previous_ref}, ensure_ascii=False))
