from pathlib import Path
import concurrent.futures

base = Path(__file__).resolve().parent.parent/'implementation-df2b17aedb254da9b0fb902ca7f8575f/run.v4.py'
source = base.read_text('utf8')
source = source.replace('def invoke(name, argv):', "env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']=str(Path(__file__).with_name('current-domain.test.exe'))\n\ndef invoke(name, argv):")
source = source.replace('result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr)', "actual_cwd = root/'internal/domain' if len(argv)>2 and argv[1:3]==['tool','test2json'] else root\n        result = subprocess.run(argv, cwd=actual_cwd, env=env, stdout=stdout, stderr=stderr)")
source = source.replace('cwd=str(root), started_at=start', 'cwd=str(actual_cwd), started_at=start')
source = source.replace('paths=sorted(paths)', "paths.add(Path(__file__).resolve().parent.parent/'implementation-df2b17aedb254da9b0fb902ca7f8575f/run.v4.py')\nif Path(env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']).is_file(): paths.add(Path(env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']))\npaths=sorted(paths)")
source = source.replace("['GOROOT','GOTOOLCHAIN'", "['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE','GOROOT','GOTOOLCHAIN'")
start=source.index('def source():')
end=source.index("save('environment.json'",start)
# Same complete file inventory and byte digests, read with a bounded pool.
# This does not change a running or historical capture helper.
source=source[:start]+'''def source():
    def item(p):
        if p.is_relative_to(root): key='repo:'+p.relative_to(root).as_posix()
        elif p.is_relative_to(main): key='main:'+p.relative_to(main).as_posix()
        else: key='absolute:'+p.as_posix()
        return key, sha(p) if p.is_file() else 'MISSING'
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(item, paths))
'''+source[end:]
exec(compile(source, str(base), 'exec'))
