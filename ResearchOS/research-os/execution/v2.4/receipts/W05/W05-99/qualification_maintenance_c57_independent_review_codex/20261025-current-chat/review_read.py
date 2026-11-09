import hashlib, json, pathlib, subprocess, sys, time
BASE = pathlib.Path(__file__).parent
def main():
    tag, command = sys.argv[1], sys.argv[2]
    dest = BASE / tag
    dest.mkdir(exist_ok=False)
    argv = ['pwsh', '-NoLogo', '-NoProfile', '-Command', command]
    (dest/'recipe.json').write_text(json.dumps({'argv':argv, 'cwd':r'D:\作品集\ResearchOS\research-os', 'phase':'PHASE1_READ_ONLY_NO_ACCEPTANCE'},ensure_ascii=False,indent=2),encoding='utf-8')
    p=subprocess.run(argv,cwd=r'D:\作品集\ResearchOS\research-os',capture_output=True)
    (dest/'stdout.raw').write_bytes(p.stdout)
    (dest/'stderr.raw').write_bytes(p.stderr)
    (dest/'result.json').write_text(json.dumps({'native_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},indent=2),encoding='utf-8')
    sys.stdout.buffer.write(p.stdout)
    sys.stderr.buffer.write(p.stderr)
    print('\nNATIVE_EXIT='+str(p.returncode))
    sys.exit(p.returncode)
if __name__=='__main__': main()
