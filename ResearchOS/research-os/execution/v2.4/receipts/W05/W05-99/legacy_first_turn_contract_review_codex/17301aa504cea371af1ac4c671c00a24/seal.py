import sys
sys.dont_write_bytecode = True
import hashlib, json
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
T5 = R / '.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
S = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
Q = Path(__file__).resolve().parent

expected = {
 'internal/domain/runtime_sessions_windows.go': ('e7863372d15063e1526cb2703a64b5b492fd03def2ff2001de852efab99b513d', 17357),
 'internal/domain/client_protocol_sessions.go': ('7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3', 19629),
 'internal/domain/client_protocol_configuration.go': ('afacf661d3354f05e85913fa358f48ffeb9eb2613ec3f6d8e09f4dbdc5daf3d9', 48697),
 'internal/domain/client_protocol.go': ('8eab2b524cbf436a11c48ac40b738c7f682d6c4e59cf58df9f3655fd2ed85bcf', 50304),
 'internal/domain/client_protocol_goal.go': ('f8a4f04987d927a7807ab21e41772574bf509e562df25a497e598b50b1494f12', 15419),
 'internal/domain/client_protocol_goal_test.go': ('3aebfa43aa5131a1c809ec3d64d800351b87f30155be0428f545799520ae319f', 14343),
 'internal/domain/runtime_qualification.go': ('420aaec664f877806af079d47cf5e5a0cc4950f2cdc42b8ae1dc16ef7a4c5c54', 16400),
 'internal/domain/runtime_model.go': ('3617fa407a3913768c9ac10f3e3d11bb562dabfad0946f1a5b2a96e56c3e8692', 7048),
 'internal/domain/client_configuration.go': ('8ca6db67fd00cea0a5c58e03cf7900534522c689567a2fadba4b016f0fe75129', 12265),
 'internal/domain/v24_sessions.go': ('fb19149d9686074fd2e57aa31ce5cceefe028d6f5e8e44a26f1cbace1626a0f2', 7640),
 'internal/host/client_configuration.go': ('6190271b794d2cf1722f6215ffbea5ca806ddf89d920ab3ef9be12ef890e4039', 1916),
 'migrations/sqlite/0016_runtime_qualification.sql': ('7fd44c42be4c0753c367fc8361e9990b56e4f9a001a5f443ef62d0d87d05a03f', 1841),
}

def pin(path):
 raw = path.read_bytes()
 return {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def write_new(name, obj):
 with (Q / name).open('x', encoding='utf-8', newline='\n') as out:
  json.dump(obj, out, ensure_ascii=False, indent=2)
  out.write('\n')

pairs = []
for rel, prior in expected.items():
 main, t5 = pin(R / rel), pin(T5 / rel)
 pairs.append({'relative': rel, 'Main': main, 'T5': t5, 'Main_T5_byte_equal': (main['sha256'], main['bytes']) == (t5['sha256'], t5['bytes']), 'T5_matches_inspected_pin': (t5['sha256'], t5['bytes']) == prior})
doc = pin(S / '22_CLIENT_INTERFACE_DETAILS.md')
schema = pin(S / 'contracts/client.protocol.schema.json')
schema_copies = [pin(root / rel) for root in (R, T5) for rel in ('internal/api/contracts/client.protocol.schema.json', 'internal/domain/contracts/client.protocol.schema.json')]
schema_equal = all((x['sha256'], x['bytes']) == (schema['sha256'], schema['bytes']) for x in schema_copies)
drift = sum(not x['T5_matches_inspected_pin'] for x in pairs)
drift += int((doc['sha256'], doc['bytes']) != ('01b3d5eaeff08d8c5c496631a7334fbf50361b8da27b032f4efd9eba06bedd48', 29855))
drift += int((schema['sha256'], schema['bytes']) != ('8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b', 161794))
refs = {'authority': 'NONE', 'formal_acceptance': False, 'primary_source_root': T5.as_posix(), 'main_source_root': R.as_posix(), 'spec_root': S.as_posix(), 'source_pairs': pairs, 'normative_doc': doc, 'normative_schema': schema, 'schema_copies': schema_copies, 'schema_copies_equal_to_normative': schema_equal, 'inspected_pin_drift': drift}
write_new('refs.json', refs)
lines = len((Q / 'report.md').read_text(encoding='utf-8').splitlines())
members = [pin(p) for p in sorted(Q.iterdir()) if p.is_file()]
seal = {'status': 'SEALED_READONLY_REPORT' if drift == 0 and lines <= 150 else 'OBSERVED_DRIFT_OR_REPORT_LIMIT', 'authority': 'NONE', 'formal_acceptance': False, 'report_lines': lines, 'source_pin_drift': drift, 'source_pair_count': len(pairs), 'Main_T5_equal_count': sum(x['Main_T5_byte_equal'] for x in pairs), 'failure_ordinal': 808, 'original_full_fail_count': 25, 'original_full_skip_count': 4, 'sources_written': 0, 'Go_native_SQL_model_executed': 0, 'members': members, 'self_hash_excluded': ['seal.json']}
write_new('seal.json', seal)
member_drift = sum(pin(Path(x['path'])) != x for x in members)
print(json.dumps({'seal': pin(Q / 'seal.json'), 'report': pin(Q / 'report.md'), 'refs': pin(Q / 'refs.json'), 'tool_io': pin(Q / 'tool-io.json'), 'failure808': pin(Q / 'failure-origin.808.json'), 'report_lines': lines, 'source_pairs': len(pairs), 'Main_T5_equal': sum(x['Main_T5_byte_equal'] for x in pairs), 'source_pin_drift': drift, 'member_drift': member_drift, 'schema_copies_equal': schema_equal}, ensure_ascii=False))

