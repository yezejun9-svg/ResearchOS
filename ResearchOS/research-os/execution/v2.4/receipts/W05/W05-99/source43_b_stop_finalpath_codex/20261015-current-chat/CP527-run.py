import json
import os
import pathlib
import subprocess
import sys
import time

recipe_path = pathlib.Path(sys.argv[1]).resolve()
recipe = json.loads(recipe_path.read_text(encoding='utf-8-sig'))
root = recipe_path.parent
command_id = recipe['id']
capture = root / command_id
capture.mkdir(exist_ok=False)
env = os.environ.copy()
env.update(recipe.get('env', {}))
argv = recipe['argv']
invocation = {
    'id': command_id,
    'argv': argv,
    'cwd': recipe['cwd'],
    'env': {key: env.get(key) for key in ('TMP', 'TEMP', 'GOTMPDIR', 'GOCACHE', 'GOPATH', 'GOTOOLCHAIN', 'GOPROXY', 'GOSUMDB', 'GOFLAGS', 'PYTHONUTF8', 'RESEARCHOS_SOURCE43_ASCII_FIXTURE_ROOT')},
    'recipe': str(recipe_path),
    'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
}
(capture / 'invocation.json').write_text(json.dumps(invocation, ensure_ascii=False, indent=2), encoding='utf-8')
with (capture / 'stdout.raw').open('wb') as stdout, (capture / 'stderr.raw').open('wb') as stderr:
    try:
        result = subprocess.run(argv, cwd=recipe['cwd'], env=env, stdout=stdout, stderr=stderr, timeout=recipe.get('timeout'))
        code = result.returncode
    except Exception as exc:
        stderr.write((repr(exc) + '\n').encode('utf-8'))
        code = 127
(capture / 'exit.json').write_text(json.dumps({'exit': code, 'end_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
sys.stdout.buffer.write((capture / 'stdout.raw').read_bytes())
sys.stderr.buffer.write((capture / 'stderr.raw').read_bytes())
sys.exit(code)
