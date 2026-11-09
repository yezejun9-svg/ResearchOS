import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
CLI = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli_exact8_continuation_preparation_codex/cli44-r309-grant-1bd789af'


def ref(path, expected=None):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def write(name, value):
    ast.parse(value)
    with (OUT / name).open('xb') as stream:
        stream.write(value.encode('utf-8'))
    return ref(OUT / name)


handoff_ref = ref(CLI / 'handoff.v4.json', '48f25026d835a36022288efa497b32cb48db9d284ec4c63f72c23555d2e18573')
handoff = json.loads((CLI / 'handoff.v4.json').read_bytes())
spec_pin = handoff['spec']
spec_ref = ref(spec_pin['path'], 'f7c171b7bcb3456958245245b670d5bef4689af8c8d4de27ef197665f7905c7e')
spec = json.loads((ROOT / spec_ref['path']).read_bytes())
manifest_ref = ref(CLI / 'manifest.v4.json', '46ec0024249181a0aa9bd4d0b83f6b36d0a087c3973c9e94dd1cc83bdb2f1d40')
manifest = json.loads((CLI / 'manifest.v4.json').read_bytes())
runner_ref = ref(CLI / 'runner.v4.py', '42fe7f31566588ff87f564085d033c15ce094d6218c404837072225cfd9f32b6')
scope = json.loads((OUT / 'cli_continuation_scope.json').read_bytes())
scope.update(prepared_handoff_ref=handoff_ref, prepared_spec_ref=spec_ref, runner_ref=runner_ref,
    prior_draft_scope_ref=ref(OUT / 'cli_continuation_scope.json'),
    amendment='Current Root grant file is a pinned execution input before freeze and each case. Original v3 retained;44/145 and original76 unchanged.')
scope['cli44_continuation'] = spec['root_grant']['cli44_continuation']
scope['cli44_continuation']['prepared_manifest_v4_sha256'] = manifest_ref['sha256']
cli_scope_ref = save('cli_continuation_scope.v2.json', scope)
prepared = json.loads((OUT / 'prepared_refs.json').read_bytes())
old_prepared_ref = ref(OUT / 'prepared_refs.json')
pins = prepared['pins']
pins.update(cli_scope=cli_scope_ref, cli_prepared_handoff=handoff_ref,
    cli_prepared_manifest=manifest_ref, cli_prepared_spec=spec_ref,
    cli_roster=ref(CLI / 'finite_selectors.v3.json'),
    list_scope=ref(OUT / 'list_independent_scope.v2.json', '8619aec61da6b0785f54849714e3574ecb3d37389145b7eacb75de2dfb761f93'),
    list_runner=ref(OUT / 'list_replay.v2.py', 'a714295db60586264dd7afdb302b48dfaa18791fd49b66e85455824783c014ad'),
    list_v2_audit=ref(OUT / 'list-v2-static-amendment.json'))
audit = json.loads((OUT / 'audit.json').read_bytes())
audit.update(prior_draft_audit_ref=ref(OUT / 'audit.json'), prior_prepared_refs=old_prepared_ref,
    additional_static_fixes='Python actual cached bytecode/loadedDLL inputs, explicit public env and full ownedJob success/finallynullable receipts in new listv2; current Root grant before/percase freeze in CLIv4.',
    actual_new_failures_or_counter_delta=0, new_product_or_native_execution=0,
    current_list_scope_ref=pins['list_scope'], current_CLI_scope_ref=cli_scope_ref)
pins['audit'] = save('audit.v2.json', audit)
register = (OUT / 'register.py').read_text(encoding='utf-8').replace('prepared_refs.json', 'prepared_refs.v2.json')
register = register.replace('prepared_manifest_v3_sha256', 'prepared_manifest_v4_sha256')
register_ref = write('register.v2.py', register)
wrapper = (OUT / 'run.py').read_text(encoding='utf-8').replace('prepared_refs.json', 'prepared_refs.v2.json')
wrapper = wrapper.replace('register.py', 'register.v2.py').replace('audit.json', 'audit.v2.json')
wrapper_ref = write('run.v2.py', wrapper)
verified = prepared['verified_refs'] + list(pins.values()) + [register_ref, wrapper_ref,
    ref(Path(__file__)), ref(OUT / 'prepare_list_v2.py'), old_prepared_ref]
for pin in manifest['entries']:
    actual = ref(CLI / pin['path'], pin['sha256'])
    assert actual['bytes'] == pin['bytes']
    verified.append(actual)
unique = {pin['path']: pin for pin in verified}
prepared.update(verified_refs=list(unique.values()), immutable_previous_prepared_refs=old_prepared_ref)
for pin in prepared['canonical_before']:
    assert ref(pin['path'], pin['sha256'])['bytes'] == pin['bytes']
prepared_ref = save('prepared_refs.v2.json', prepared)
print(json.dumps({'prepared': prepared_ref, 'register': register_ref, 'wrapper': wrapper_ref,
    'audit': pins['audit'], 'CLI_scope': cli_scope_ref, 'list_scope': pins['list_scope'], 'verified_refs': len(unique)}, ensure_ascii=True))
