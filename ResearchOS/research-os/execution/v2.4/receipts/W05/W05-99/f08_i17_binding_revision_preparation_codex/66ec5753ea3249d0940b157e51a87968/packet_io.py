"""Receipt-local byte/JSON operations; never executes candidate Go, SQL or helpers."""
from pathlib import Path
import difflib
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
RECEIPTS = OUT.parent.parent
PRIOR = OUT.parent / 'b918c16361bb4744bc7fffb6434d6849'
REVIEW = RECEIPTS / 'f08_i17_binding_revision_independent_source_review_codex/f55ac9fdfb3d4a929686b6884431f962'
MAPPING = RECEIPTS / 'f08_i17_binding_source_mapping_codex/83077264f7f748daa7c9452e22c5c2d0'
ACTOR = 'codex:/root/f08_i17_binding_impl'
ALLOW_IDENTICAL_PREPARED_REUSE = False

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(r):
    assert ref(r['path']) == r, r['path']
    return Path(r['path']).read_bytes()

def load(path):
    return json.loads(Path(path).read_bytes())

def compact(value, sorted_keys=True):
    return json.dumps(value, ensure_ascii=False, sort_keys=sorted_keys, separators=(',', ':')).encode('utf-8')

def dump(name, value):
    write(name, json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8') + b'\n')

def write(name, raw):
    path = (OUT / name).resolve()
    assert path.is_relative_to(OUT), path
    if path.exists():
        assert ALLOW_IDENTICAL_PREPARED_REUSE and not (OUT / 'manifest.json').exists()
        assert path.read_bytes() == raw, 'Prepared bytes changed; refuse overwrite: ' + str(path)
        return ref(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return ref(path)

def unified(before, after, before_name, after_name):
    # Keep every input line byte, including CRLF and absent final newline.
    pieces = difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True),
        after.decode('utf-8').splitlines(keepends=True), fromfile=before_name,
        tofile=after_name, lineterm='\n')
    result = []
    for piece in pieces:
        raw = piece.encode('utf-8')
        result.append(raw)
        if not raw.endswith(b'\n'):
            result.append(b'\n\\ No newline at end of file\n')
    return b''.join(result)

def apply_unified(before, patch):
    if not patch:
        return before
    source = before.splitlines(keepends=True)
    lines = patch.splitlines(keepends=True)
    assert lines[0].startswith(b'--- ') and lines[1].startswith(b'+++ ')
    output = []
    cursor = 0
    i = 2
    while i < len(lines):
        m = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n', lines[i])
        assert m, lines[i][:120]
        count = int(m[2] or b'1')
        position = int(m[1]) - 1 if count else int(m[1])
        assert position >= cursor
        output.extend(source[cursor:position])
        cursor = position
        old_count = new_count = 0
        i += 1
        while i < len(lines) and not lines[i].startswith(b'@@ '):
            marker, body = lines[i][:1], lines[i][1:]
            assert marker in (b' ', b'+', b'-'), lines[i][:120]
            if i + 1 < len(lines) and lines[i + 1] == b'\\ No newline at end of file\n':
                assert body.endswith(b'\n')
                body = body[:-1]
                i += 1
            if marker in (b' ', b'-'):
                assert cursor < len(source) and source[cursor] == body, cursor
                cursor += 1
                old_count += 1
            if marker in (b' ', b'+'):
                output.append(body)
                new_count += 1
            i += 1
        assert old_count == count
        assert new_count == int(m[4] or b'1')
    output.extend(source[cursor:])
    return b''.join(output)

def diff_pair(name, before_ref, after_ref):
    before, after = checked(before_ref), checked(after_ref)
    forward = unified(before, after, before_ref['path'], after_ref['path'])
    inverse = unified(after, before, after_ref['path'], before_ref['path'])
    assert apply_unified(before, forward) == after
    assert apply_unified(after, inverse) == before
    return {'name': name, 'before': before_ref, 'after': after_ref,
        'forward': write('diffs/' + name + '.forward.patch', forward),
        'inverse': write('diffs/' + name + '.inverse.patch', inverse),
        'whole_byte_forward_inverse_exact': True}

def masked_go(raw):
    # Byte-position lexical masking only, not a Go AST/compiler/parser run.
    masked = bytearray(raw)
    i = 0
    while i < len(raw):
        if raw[i:i+2] == b'//':
            end = raw.find(b'\n', i)
            if end < 0:
                end = len(raw)
        elif raw[i:i+2] == b'/*':
            end = raw.find(b'*/', i+2)
            assert end >= 0
            end += 2
        elif raw[i] in (34, 39, 96):
            quote = raw[i]
            end = i + 1
            while end < len(raw):
                if quote != 96 and raw[end] == 92:
                    end += 2
                elif raw[end] == quote:
                    break
                else:
                    end += 1
            assert end < len(raw)
            end += 1
        else:
            i += 1
            continue
        for k in range(i, end):
            if raw[k] not in (10, 13):
                masked[k] = 32
        i = end
    return bytes(masked)

def functions(raw):
    masked = masked_go(raw)
    stack, pairs = [], {}
    matches = {41: 40, 93: 91, 125: 123}
    for position, char in enumerate(masked):
        if char in (40, 91, 123):
            stack.append((char, position))
        elif char in matches:
            assert stack and stack[-1][0] == matches[char], position
            _, start = stack.pop()
            pairs[start] = position
    assert not stack
    found = {}
    for m in re.finditer(rb'\bfunc\s*(?:\([^\n]*?\)\s*)?(\w+)\s*\(', masked):
        brace = masked.find(b'{', m.end())
        assert brace in pairs
        found[m[1].decode('ascii')] = {
            'start_byte': m.start(), 'end_byte_exclusive': pairs[brace]+1,
            'raw': raw[m.start():pairs[brace]+1]}
    return found

def byte_body_record(before, after, name):
    a, b = before[name], after[name]
    assert a['raw'] == b['raw'], name
    return {'name': name, 'before_start_byte': a['start_byte'],
        'after_start_byte': b['start_byte'], 'bytes': len(a['raw']),
        'sha256_before': hashlib.sha256(a['raw']).hexdigest(),
        'sha256_after': hashlib.sha256(b['raw']).hexdigest(),
        'raw_byte_equal_without_normalization': True}

def source_rules(raw):
    rules = {}
    for line in raw.decode('utf-8').splitlines():
        m = re.search(r'"([a-z_]+)": \{mask:"([sihSIH]+)", unique:\[\]\[\]int\{(.*?)\}\},', line)
        if m:
            keys = [[int(n) for n in inner.split(',')] for inner in re.findall(r'\{([0-9,]+)\}', m[3])]
            rules[m[1]] = {'mask': m[2], 'unique': keys}
    assert len(rules) == 34, len(rules)
    return rules

def shape(frame, rules):
    assert set(frame) == {'action', 'row', 'old', 'sources'}
    assert frame['action'] in ('commit.insert', 'journal.update')
    category = 'commits' if frame['action'] == 'commit.insert' else 'idempotency'
    def tuple_shape(row, category):
        mask = rules[category]['mask']
        assert isinstance(row, list) and len(row) == len(mask), category
        for value, kind in zip(row, mask):
            if value is None and kind.isupper():
                continue
            if kind.lower() == 's':
                assert isinstance(value, str), (category, kind)
            elif kind.lower() == 'i':
                assert type(value) is int and -(2**63) <= value < 2**63
            elif kind.lower() == 'h':
                assert isinstance(value, str) and len(value) % 2 == 0
                assert bytes.fromhex(value).hex().upper() == value
            else:
                raise AssertionError(kind)
    tuple_shape(frame['row'], category)
    if frame['action'] == 'journal.update':
        tuple_shape(frame['old'], category)
    else:
        assert frame['old'] is None
    seen = {}
    for pair in frame['sources']:
        assert isinstance(pair, list) and len(pair) == 2
        category, row = pair
        assert category in rules
        tuple_shape(row, category)
        for key_no, indices in enumerate(rules[category]['unique']):
            key = tuple(row[n] for n in indices)
            if None in key:
                continue
            pool = seen.setdefault((category, key_no), set())
            assert key not in pool, (category, key_no)
            pool.add(key)
    return {'frame_keys_closed': True, 'action_accepted_for_mode5': True,
        'row_and_OLD_masks_valid': True, 'source34_masks_valid': True,
        'source34_unique_keys_valid': True, 'source_tuple_count': len(frame['sources']),
        'validation_authority': 'INDEPENDENT_STATIC_DATA_SHAPE_ONLY_NOT_AUTHORITY_PREDICATE_RUN'}
