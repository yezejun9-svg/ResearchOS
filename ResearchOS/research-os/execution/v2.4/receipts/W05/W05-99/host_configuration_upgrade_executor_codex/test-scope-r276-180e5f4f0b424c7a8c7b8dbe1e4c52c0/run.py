from pathlib import Path

base = Path(__file__).resolve().parent.parent/'implementation-df2b17aedb254da9b0fb902ca7f8575f/run.v4.py'
source = base.read_text('utf8')
source = source.replace('def invoke(name, argv):', "env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']=str(Path(__file__).with_name('current-domain.test.exe'))\n\ndef invoke(name, argv):")
source = source.replace('result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr)', "actual_cwd = root/'internal/domain' if len(argv)>2 and argv[1:3]==['tool','test2json'] else root\n        result = subprocess.run(argv, cwd=actual_cwd, env=env, stdout=stdout, stderr=stderr)")
source = source.replace('cwd=str(root), started_at=start', 'cwd=str(actual_cwd), started_at=start')
source = source.replace('paths=sorted(paths)', "paths.add(Path(__file__).resolve().parent.parent/'implementation-df2b17aedb254da9b0fb902ca7f8575f/run.v4.py')\nif Path(env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']).is_file(): paths.add(Path(env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']))\npaths=sorted(paths)")
source = source.replace("['GOROOT','GOTOOLCHAIN'", "['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE','GOROOT','GOTOOLCHAIN'")
exec(compile(source, str(base), 'exec'))
