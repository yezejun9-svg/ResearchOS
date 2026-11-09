# Retain ordinal 029 unchanged: the first review harness expectation omitted
# the producer metadata's intentionally relocated public build-stage path.
from pathlib import Path
original=Path(__file__).with_name('verify_r3_build_delta.py').read_text(encoding='utf-8')
needle="'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'},output_changed"
replacement="'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe','apps/desktop/resources/control/runtime/mu-worker.mjs.build.json'},output_changed"
assert original.count(needle)==1
anchor="assert manifest['core']['migration_count']==25 and manifest['electron']['file_count']==75"
additional="""
mu_relative='apps/desktop/resources/control/runtime/mu-worker.mjs.build.json'
mu_new=read(B/mu_relative);mu_old=read(pathlib.Path(oldmanifest['bundle_root'])/mu_relative)
assert [key for key in mu_new if mu_new[key]!=mu_old[key]]==['bundle']
assert pathlib.Path(mu_new['bundle'])==B.with_name(B.name+'-mu-stage')/'mu-worker.mjs'
assert sha(pathlib.Path(mu_new['bundle']))==mu_new['bundle_sha256']==manifest['mu']['bundle_sha256']
"""
assert original.count(anchor)==1
exec(compile(original.replace(needle,replacement).replace(anchor,anchor+additional),__file__,'exec'))
