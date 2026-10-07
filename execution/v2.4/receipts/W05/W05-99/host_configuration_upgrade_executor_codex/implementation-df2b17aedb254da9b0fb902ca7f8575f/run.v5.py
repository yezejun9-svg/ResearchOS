from pathlib import Path

# Exact existing run.v4 capture algorithm, with the separately authorized,
# immutable historical14 executable added to environment and source inventory.
base = Path(__file__).with_name('run.v4.py')
source = base.read_text('utf8')
assert source.count('def invoke(name, argv):') == 1
source = source.replace('def invoke(name, argv):', "env['RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL']=str(main/'.local/bin/researchos-remote.exe')\n\ndef invoke(name, argv):")
assert source.count('paths=sorted(paths)') == 1
source = source.replace('paths=sorted(paths)', "paths.add(Path(env['RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL']))\npaths.add(Path(__file__).with_name('run.v4.py'))\npaths=sorted(paths)")
source = source.replace("['GOROOT','GOTOOLCHAIN'", "['RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL','GOROOT','GOTOOLCHAIN'")
exec(compile(source, str(base), 'exec'))
