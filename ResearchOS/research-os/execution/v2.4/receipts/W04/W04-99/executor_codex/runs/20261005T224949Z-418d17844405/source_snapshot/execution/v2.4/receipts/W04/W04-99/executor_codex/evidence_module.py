"""W04 execution evidence helpers; no acceptance or canonical state writes."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(raw: str | bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result

    def invalid(value):
        raise ValueError('nonfinite number: ' + value)

    def number(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            invalid(value)
        return parsed
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid, parse_float=number)


def save_new(path: Path, body) -> None:
    # Preserve previous runs and raw evidence even after failure.
    with path.open('xb') as stream:
        stream.write((json.dumps(body, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def reference(root: Path, path: Path, **locator) -> dict:
    root, path = root.resolve(), path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('evidence must be an existing repository file')
    return {'path': path.relative_to(root).as_posix(), 'sha256': digest(path), **locator}


def source_vector(root: Path, relative_paths: list[str]) -> list[dict]:
    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError('duplicate source vector path')
    return [reference(root, root / name) for name in sorted(relative_paths)]


def enrolled_sources(root: Path, here: Path) -> list[Path]:
    sources=set()
    for base in ('internal','adapters','migrations','tests/contracts/fixtures','tests/context/parent','spec/v2.0/contracts'):
        for path in (root/base).rglob('*'):
            if path.is_file() and path.suffix in ('.go','.json','.sql','.md','.txt','.yaml','.yml'):
                sources.add(path)
    sources.update(p for p in here.iterdir() if p.name in ('collect.py','bridge.py','test_bridge.py','parent_driver.py','evidence_module.py','expected.json'))
    sources.add(here/'frozen_inputs/legacy_entries.json')
    sources.add(here/'frozen_inputs/commands-v24-r37.json')
    return sorted(sources)


def assertion_records(root: Path, raw_path: Path) -> tuple[list[dict], set[str]]:
    """Read observed Go JSON events, retaining exact raw line locators."""
    records, passed = [], set()
    pending = {}
    for number, line in enumerate(raw_path.read_text(encoding='utf-8').splitlines(), 1):
        event = strict_json(line)
        if not isinstance(event, dict):
            raise ValueError('Go event must be an object')
        test = event.get('Test')
        if event.get('Action') == 'pass' and test:
            passed.add(test)
        if event.get('Action') != 'output' or not test:
            continue
        # test2json may split a long single JSON assertion across Output events.
        text, start = pending.get(test, ('', number))
        text += event.get('Output', '')
        while '\n' in text:
            output, text = text.split('\n', 1)
            if output.startswith('W04_ASSERTION '):
                record = strict_json(output.removeprefix('W04_ASSERTION '))
                if not isinstance(record, dict) or not {'assertion_id', 'expected', 'actual', 'status', 'evidence'} <= record.keys():
                    raise ValueError('malformed observed assertion')
                records.append({**record, 'go_test': test,
                                'raw_evidence_refs': [reference(root, raw_path, locator={'line_start':start, 'line_end':number})]})
            start = number
        pending[test] = (text, start if text else number + 1)
    if any(text.startswith('W04_ASSERTION ') for text, _ in pending.values()):
        raise ValueError('truncated observed assertion')
    return records, passed


def exact_assertions(records: list[dict], wanted: list[str], test: str) -> list[dict]:
    selected = [row for row in records if row['go_test'] == test]
    found = [row['assertion_id'] for row in selected]
    if sorted(found) != sorted(wanted) or len(found) != len(set(found)):
        raise ValueError('incomplete/duplicate assertion roster for ' + test)
    if not selected or any(row['status'] != 'PASS' for row in selected):
        raise ValueError('not all observed assertions passed for ' + test)
    return selected
