import datetime, hashlib, json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit('usage: reviewer_logger.py COMMAND [ARG ...]')
    captures = ROOT / 'command-captures'
    captures.mkdir(exist_ok=True)
    ordinal = max([int(p.name) for p in captures.iterdir() if p.is_dir() and p.name.isdigit()] or [0]) + 1
    dest = captures / f'{ordinal:04d}'
    dest.mkdir(exist_ok=False)
    tmp = ROOT.parents[6] / '.local' / 'owned-core-stop-r5-independent-review-20261015-tmp'
    tmp = pathlib.Path('D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r5-independent-review-20261015-tmp')
    tmp.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMP=str(tmp), TEMP=str(tmp), GOTMPDIR=str(tmp), GOCACHE=str(tmp / 'gocache'), GOPATH='D:/作品集/ResearchOS/research-os/.local/tools/gopath', GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod', GOTOOLCHAIN='local')
    metadata = {'ordinal': ordinal, 'argv': args, 'cwd': str(pathlib.Path.cwd()), 'relevant_environment': {key: os.environ[key] for key in ['TMP','TEMP','GOTMPDIR','GOCACHE','GOPATH','GOMODCACHE','GOTOOLCHAIN']}, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (dest / 'command.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except Exception as exc:
        stdout, stderr, code = b'', repr(exc).encode('utf-8'), 127
    (dest / 'stdout.txt').write_bytes(stdout)
    (dest / 'stderr.txt').write_bytes(stderr)
    metadata.update(exit_code=code, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest())
    (dest / 'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    with (ROOT / 'command-ledger.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(metadata, ensure_ascii=False) + '\n')
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    if False and args[-1].replace('\\', '/').endswith('/build_review.py'):
        from build_review import seal_after_capture
        seal_after_capture()
    raise SystemExit(code)
if __name__ == '__main__':
    main()
