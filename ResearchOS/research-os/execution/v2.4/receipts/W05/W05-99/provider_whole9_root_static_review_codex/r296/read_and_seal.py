import datetime
import hashlib
import json
from pathlib import Path
import subprocess

root = Path.cwd().resolve()
out = Path(__file__).resolve().parent
candidate = root / '.local/worktrees/codex-w0599-provider-binding'
mapping_ns = root / 'execution/v2.4/receipts/W05/W05-99/provider_binding_whole_scope_gap_mapping_codex/80512d54-a478-4291-9760-8e5a4b77e49f'

def ref(path):
    data = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def save(name, value):
    path = out / name
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return ref(path)

canonical = {name: ref(root / 'execution/v2.4' / name) for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']}
cp = json.loads((root / 'execution/v2.4/checkpoint.json').read_bytes())
ownership = json.loads((root / 'execution/v2.4/path_ownership.json').read_bytes())
assert cp['revision'] == 296 and ownership['revision'] == 124
mapping = json.loads((mapping_ns / 'mapping.json').read_bytes())
assert ref(mapping_ns / 'mapping.json')['sha256'] == 'b303bf4f93a89cba3a265df28ba72509474692c5b4b2bf8a0d4ccca7214e78ff'
manifest = json.loads((mapping_ns / 'manifest.json').read_bytes())
assert len(manifest['entries']) == 105
for row in manifest['entries']:
    got = ref(Path(row['path']))
    assert got['sha256'] == row['sha256'] and got['bytes'] == row['bytes']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=candidate).decode().strip() == '6fb5263681c17f0e50920c354dc07ed440a23714'
source = []
for row in mapping['candidate_source9']:
    original = candidate / row['path']
    data = original.read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['candidate_sha256']
    assert subprocess.check_output(['git', 'show', 'HEAD:' + row['path']], cwd=candidate) == data
    snapshot = out / 'candidate-source' / row['path']
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with snapshot.open('xb') as stream:
        stream.write(data)
    source.append({'original': ref(original), 'snapshot': ref(snapshot)})
paths = {row['path'] for row in mapping['candidate_source9']}
handler_paths = ownership['card_path_bindings']['W05-99']['subtasks']['host_configuration_public_handlers']['paths']
assert not paths.intersection(handler_paths)
review = {
    'schema': 'researchos.provider-whole9-root-static-review.v1',
    'reviewer': 'codex:/root', 'source_author': 'codex:/root/command_queue_impl',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'decision': 'ORIGINAL7_STATIC_BOUNDARIES_REVIEWED_NO_IMPLEMENTATION_ACCEPTANCE',
    'candidate': '6fb5263681c17f0e50920c354dc07ed440a23714', 'candidate_schema': 22,
    'source_count': 9, 'source_refs': source,
    'prior_exact2_review_reused': mapping['established_proof']['review_ref'],
    'readonly_input_manifest': ref(mapping_ns / 'manifest.json'), 'verified_manifest_entries': 105,
    'actual_read_basis': ['b7c17a', 'c11106', 'f56442', '2216ee'],
    'root_scope': 'Original7 full incremental diff plus actual unchanged producer/dispatch/transport/credential/stream context. Exact2 source-ready evidence reused; no repeated SQL/test execution.',
    'boundaries': [
        {'path': 'adapters/runtime/mu/worker.mjs', 'finding': 'Policy absent retains original model tuple, thinking off, no SDK retries, broker-only fetch and fixed worker prompt; policy present uses exact provider/model/endpoint, high thinking and max_tokens. Generic worker/stream/privatewire/cancel unchanged.',
         'open': 'Actual rebuilt SDK G1 required. contextWindow=1000000 is metadata, not proof of gateway context. Go broader loopback fixtures and JS literal127.0.0.1/[::1] domain discrepancy requires explicit pure boundary coverage if claimed.'},
        {'path': 'adapters/runtime/mu/worker-provider-binding.test.mjs', 'finding': 'Actual pinned SDK imported and iterated, fixed custom fetch and exact reasoning/body assertions; cancellation child uses synthetic process/transport facts honestly.',
         'open': 'Six advertised controls require actual test events. Child cancellation control is transport-only, does not establish durable SQLite/Host/LIVE or 40-delta ordinary provider path.'},
        {'path': 'internal/domain/runtime_model.go', 'finding': 'Policy presence distinguishes absent legacy from explicit unknown/null/false. Added endpoint/config/request constraints leave legacy branch intact; existing complete payload/body, tools, 48KiB and original call-limit gates retain authority.',
         'open': 'Go3 current execution and refusal layers required, not only zero external requests.'},
        {'path': 'internal/domain/runtime_broker_windows.go', 'finding': 'New policy requires frozen bound route and monetary upperbound; immutable providerTransport inserted before original cost/PREPARED and independently recalculated after dispatch gate before STARTED. Original request/cost hashes and stable frame keys remain authority; MODEL stays MODEL with zero money.',
         'open': 'New policy causal call caps, route/header tampering, Session affinity and UNKNOWN/replay need G2/G4 actual controls.'},
        {'path': 'internal/domain/runtime_model_windows.go', 'finding': 'Original host-only credential resolution, proxy nil/no redirects/90s/no semantic retry preserved. HTTP headers originate immutable intent; added reasoning policy runs on quarantined complete SSE before release. Confirmed actual_cost remains null and old reservation held; original late-response dispatch gate preserves cancelled execution denial.',
         'open': 'Ordinary Session quarantine and delayed ACK/cancel durable credit proofs under new provider policy remain G4, no LIVE claim.'},
        {'path': 'internal/domain/runtime_model_stream.go', 'finding': 'New inventory check occurs even with zero streams at final evidence and backup. ProviderResponse/Reasoning/WireHistory supplement original SSE/SDK/dispatch/cost obligations, rather than replacing original effect facts.',
         'open': 'Current Main23/configuration handler composition and semantically corrupt archive publicRestore not qualified by candidate22 publicCreateBackup refusals.'},
        {'path': 'internal/domain/runtime_provider_binding_test.go', 'finding': 'Deterministic config/body/legacy protection plus byte-exact history/alias/block-order controls. Unused textFirst local is not a tested alternate-first-signature branch; JS actual SDK branch separately required.',
         'open': 'Go3 actual execution, including subcase events and no skips, still required.'}],
    'whole9_source_ready': False, 'Main23_composition_accepted': False,
    'G1_authorization': 'Separate Root canonical bounded execution registration required after concrete prepared runner/resource review.',
    'G2_G3_G4_G5_G6': 'All original missing/held/current-composition/LIVE gates remain open as mapped; static review does not unlock held positive automatic retry.',
    'preserve': 'Oldhistory5/P1/public2 failures, 64+12 established controls, oldcase02 historical non-equivalence and C10 missing historical inputs remain unchanged.',
    'production_source_writes': 0, 'SQL_or_test_or_Node_or_HTTP_or_model_calls': 0, 'new_failures': 0, 'formal_increment': 0}
review_ref = save('source_review.json', review)
assert all(ref(root / 'execution/v2.4' / name) == value for name, value in canonical.items())
files = [ref(path) for path in sorted(out.rglob('*')) if path.is_file()]
manifest_ref = save('manifest.json', {'schema': 'researchos.public-source-manifest.v1', 'files': files, 'self_excluded': True, 'public_only': True})
handoff_ref = save('handoff.json', {'decision': review['decision'], 'source_review_ref': review_ref,
    'manifest_ref': manifest_ref, 'whole9_source_ready': False, 'next': 'Root reviews exact prepared G1 source/resources/runner then bounded execution; no Main integration or held positives.', 'formal_increment': 0})
print(json.dumps({'review_ref': review_ref, 'manifest_ref': manifest_ref, 'handoff_ref': handoff_ref, 'source_count': 9, 'formal_increment': 0}, ensure_ascii=True))
