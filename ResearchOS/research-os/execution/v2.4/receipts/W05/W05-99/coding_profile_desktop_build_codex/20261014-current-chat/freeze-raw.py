"""Copy D-local build receipts and referenced compiler files into formal D evidence."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/profile-result-build-20261014'
RAW = SOURCE / '.local/receipts/profile-result-c8b7adab-20261014'
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def need(value, message):
    if not value:
        raise RuntimeError(message)

def main():
    raw_target = HERE / 'raw-build-receipts'
    archive_target = HERE / 'compiler-archive'
    need(not raw_target.exists() and not archive_target.exists() and
         not (HERE / 'raw-freeze.json').exists(), 'freeze target already exists')
    shutil.copytree(RAW, raw_target)
    raw_rows = []
    for source in sorted(RAW.iterdir()):
        if not source.is_file():
            continue
        target = raw_target / source.name
        need(target.is_file() and sha(source) == sha(target), 'raw copy drift: ' + source.name)
        raw_rows.append({'source': str(source), 'copy': str(target),
                         'bytes': target.stat().st_size, 'sha256': sha(target)})
    archive = json.loads((raw_target / 'compiler-work-archive.json').read_bytes())
    archive_target.mkdir()
    saved = {}
    for kind in ('WORK', 'archives'):
        folder = archive_target / kind
        folder.mkdir()
        rows = []
        for number, entry in enumerate(archive[kind]):
            source = Path(entry['path'])
            need(source.is_file() and source.is_relative_to(SOURCE / '.local/builds/profile-result-c8b7adab-20261014') and
                 source.stat().st_size == entry['bytes'] and sha(source) == entry['sha256'],
                 'compiler input changed: ' + str(source))
            target = folder / f'{number:04d}.bin'
            shutil.copyfile(source, target)
            need(target.stat().st_size == entry['bytes'] and sha(target) == entry['sha256'],
                 'compiler archive copy drift: ' + str(target))
            rows.append({'source': str(source), 'copy': str(target),
                         'bytes': entry['bytes'], 'sha256': entry['sha256']})
        saved[kind] = rows
    payload = {'schema': 'researchos.cp477-formal-raw-build-freeze/1',
               'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'raw_files': raw_rows, 'compiler_files': saved,
               'raw_count': len(raw_rows),
               'WORK_count': len(saved['WORK']), 'archive_count': len(saved['archives']),
               'WORK_bytes': sum(row['bytes'] for row in saved['WORK']),
               'archive_bytes': sum(row['bytes'] for row in saved['archives'])}
    with (HERE / 'raw-freeze.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': 'FORMAL_RAW_FREEZE_PASS', 'raw_count': payload['raw_count'],
                      'WORK_count': payload['WORK_count'], 'archive_count': payload['archive_count']}))

if __name__ == '__main__':
    main()
