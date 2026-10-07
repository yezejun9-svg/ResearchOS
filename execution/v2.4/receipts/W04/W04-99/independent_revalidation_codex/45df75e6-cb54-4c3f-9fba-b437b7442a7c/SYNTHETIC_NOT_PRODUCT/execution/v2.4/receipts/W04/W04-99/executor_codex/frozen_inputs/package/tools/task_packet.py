#!/usr/bin/env python3
"""只读选择实施任务卡；不执行命令、不写状态、不授予产品验收。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'NOT_STARTED', 'IN_PROGRESS', 'EXECUTION_REPORTED', 'ACCEPTED', 'BLOCKED', 'FAILED', 'CANCELLED'}
STEP_ID = re.compile(r'W(?:0[0-9]|1[0-9]|2[01])-[0-9]{2}')
SHA256 = re.compile(r'[0-9a-f]{64}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, field):
    require(isinstance(value, str) and bool(value.strip()), f'{field} 必须是非空字符串')


def strings(value, field, nonempty=False):
    require(isinstance(value, list) and (not nonempty or bool(value)), f'{field} 必须是字符串数组')
    for item in value:
        text(item, field)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'JSON 包含重复字段：{key}')
        result[key] = value
    return result


def read_json(path):
    with Path(path).open(encoding='utf-8-sig') as handle:
        return json.load(handle, object_pairs_hook=unique_object,
                         parse_constant=lambda value: require(False, f'JSON 包含非法常量：{value}'))


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(262144), b''):
            result.update(chunk)
    return result.hexdigest()


def load_plan(path):
    plan = read_json(path)
    require(isinstance(plan, dict), '执行计划必须是对象')
    require(plan.get('package_version') == '2.4.0', '执行计划版本必须是 2.4.0')
    text(plan.get('artifact_kind'), 'artifact_kind')
    steps = plan.get('steps')
    require(isinstance(steps, list) and bool(steps), '执行计划 steps 必须是非空数组')
    ids = set()
    for step in steps:
        require(isinstance(step, dict), '每张任务卡必须是对象')
        sid = step.get('id')
        require(isinstance(sid, str) and STEP_ID.fullmatch(sid) is not None and not sid.endswith('-00'), f'非法任务卡 ID：{sid!r}')
        require(sid not in ids, f'执行计划包含重复任务卡：{sid}')
        ids.add(sid)
        require(step.get('parent_task') == sid[:3], f'{sid} parent_task 不匹配')
        for field in ('title', 'rollback'):
            text(step.get(field), f'{sid}.{field}')
        for field in ('dependencies', 'affected_formal_cases', 'resource_requirements'):
            strings(step.get(field), f'{sid}.{field}')
        require(len(set(step['dependencies'])) == len(step['dependencies']), f'{sid} 依赖重复')
        for field in ('write_scope', 'actions', 'deliverables', 'limits'):
            strings(step.get(field), f'{sid}.{field}', nonempty=True)
        for field, required in (
            ('read_refs', ('path', 'selector')), ('checks', ('id', 'expected')),
            ('verification_commands', ('key', 'cwd', 'binding')),
        ):
            items = step.get(field)
            require(isinstance(items, list) and bool(items), f'{sid}.{field} 必须是非空数组')
            for item in items:
                require(isinstance(item, dict), f'{sid}.{field} 条目必须是对象')
                for key in required:
                    text(item.get(key), f'{sid}.{field}.{key}')
                if field == 'verification_commands':
                    strings(item.get('argv_template'), f'{sid}.verification_commands.argv_template', nonempty=True)
        handoff = step.get('handoff')
        require(isinstance(handoff, dict), f'{sid}.handoff 必须是对象')
        for field in ('state', 'checkpoint', 'receipt_directory'):
            text(handoff.get(field), f'{sid}.handoff.{field}')
        require(handoff.get('independent_review_required') is True, f'{sid} 必须要求独立复核')
        require(step.get('status', 'NOT_STARTED') == 'NOT_STARTED', f'{sid} 规格初始状态不能伪装成执行结果')
        if 'priority' in step:
            require(type(step['priority']) is int and step['priority'] >= 0, f'{sid}.priority 必须是非负整数')
    indexed = {step['id']: step for step in steps}
    visiting, visited = set(), set()

    def visit(sid):
        require(sid not in visiting, f'执行计划依赖成环：{sid}')
        if sid in visited:
            return
        visiting.add(sid)
        for dependency in indexed[sid]['dependencies']:
            require(dependency in indexed, f'{sid} 存在未知依赖：{dependency}')
            visit(dependency)
        visiting.remove(sid)
        visited.add(sid)

    for sid in indexed:
        visit(sid)
    return plan


def load_state(path, plan_path, plan):
    if path is None:
        return {}, 'NOT_PROVIDED_ASSUMED_EMPTY'
    path = Path(path).resolve()
    if not path.exists():
        return {}, 'MISSING_ASSUMED_EMPTY'
    state = read_json(path)
    require(isinstance(state, dict), '状态必须是对象')
    require(state.get('schema_version') == '1.0', '状态 schema_version 必须是 1.0')
    require(state.get('package_version') == '2.4.0', '状态 package_version 必须是 2.4.0')
    require(state.get('plan_sha256') == digest(plan_path), '状态对应的执行计划哈希不匹配；不能复用另一版本的接受记录')
    records = state.get('steps')
    require(isinstance(records, list), '状态 steps 必须是数组')
    known = {step['id'] for step in plan['steps']}
    indexed = {}
    for record in records:
        require(isinstance(record, dict), '状态条目必须是对象')
        sid = record.get('id')
        require(isinstance(sid, str) and sid in known, f'状态包含未知任务卡：{sid!r}')
        require(sid not in indexed, f'状态包含重复任务卡：{sid}')
        status = record.get('status')
        require(isinstance(status, str) and status in STATUSES, f'{sid} 状态非法')
        for field in ('executor_id', 'verifier_id'):
            if field in record:
                text(record[field], f'{sid}.{field}')
        evidence = record.get('evidence', [])
        require(isinstance(evidence, list), f'{sid}.evidence 必须是数组')
        if record['status'] == 'ACCEPTED':
            text(record.get('executor_id'), f'{sid}.executor_id')
            text(record.get('verifier_id'), f'{sid}.verifier_id')
            require(record['executor_id'].strip().casefold() != record['verifier_id'].strip().casefold(), f'{sid} 执行者不得自批')
            require(bool(evidence), f'{sid} ACCEPTED 缺少证据文件')
        seen_evidence = set()
        for item in evidence:
            require(isinstance(item, dict), f'{sid} 证据条目必须是对象')
            text(item.get('path'), f'{sid}.evidence.path')
            relative = Path(item['path'])
            require(not relative.is_absolute() and not relative.drive and '..' not in relative.parts,
                    f'{sid} 证据路径必须位于状态目录内')
            evidence_path = (path.parent / relative).resolve()
            require(evidence_path.is_relative_to(path.parent) and evidence_path.is_file(), f'{sid} 证据文件缺失或越界：{item["path"]}')
            require(evidence_path not in seen_evidence, f'{sid} 证据文件重复：{item["path"]}')
            seen_evidence.add(evidence_path)
            expected = item.get('sha256')
            require(isinstance(expected, str) and SHA256.fullmatch(expected) is not None, f'{sid} 证据 SHA256 格式错误')
            require(digest(evidence_path) == expected, f'{sid} 证据哈希不匹配：{item["path"]}')
        indexed[sid] = record
    for step in plan['steps']:
        if indexed.get(step['id'], {}).get('status') == 'ACCEPTED':
            for dependency in step['dependencies']:
                require(indexed.get(dependency, {}).get('status') == 'ACCEPTED', f'{step["id"]} 已接受但依赖 {dependency} 未接受')
    return indexed, 'VALIDATED_FILE'


def eligible(step, state):
    return state.get(step['id'], {}).get('status', 'NOT_STARTED') in {'NOT_STARTED', 'IN_PROGRESS'} and all(
        state.get(sid, {}).get('status') == 'ACCEPTED' for sid in step['dependencies'])


def select_next(plan, state):
    candidates = [(index, step) for index, step in enumerate(plan['steps']) if eligible(step, state)]
    selected = min(candidates, key=lambda pair: (
        state.get(pair[1]['id'], {}).get('status') != 'IN_PROGRESS', pair[1].get('priority', 0), pair[0]), default=None)
    return selected[1] if selected else None


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=ROOT / 'contracts/execution.plan.json', help='默认使用包内执行计划')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('list', 'show', 'next'):
        command = commands.add_parser(name)
        command.add_argument('--state', type=Path, help='只读施工状态；缺失时明确按空状态选择')
        if name == 'show':
            command.add_argument('id', help='例如 W00-01')
    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan)
        state, source = load_state(args.state, args.plan, plan)
        result = {'package_version': plan['package_version'], 'read_only': True,
                  'state_source': source, 'product_acceptance': 'NOT_ASSERTED',
                  'notice': '本工具只选择任务卡，不执行、不签收；身份字段与文件哈希检查不认证复核人身份。'}
        if source != 'VALIDATED_FILE':
            result['warning'] = '没有已验证的施工状态，所有任务按未执行处理；显示任务卡不代表已经施工。'
        code = 0
        if args.command == 'list':
            result['steps'] = [dict(id=s['id'], title=s['title'], dependencies=s['dependencies'],
                                    status=state.get(s['id'], {}).get('status', 'NOT_STARTED'),
                                    eligible=eligible(s, state)) for s in plan['steps']]
        elif args.command == 'show':
            found = next((step for step in plan['steps'] if step['id'] == args.id), None)
            require(found is not None, f'未知任务卡：{args.id}')
            result['step'] = found
            result['eligible'] = eligible(found, state)
        else:
            result['step'] = select_next(plan, state)
            if result['step'] is None:
                all_accepted = all(state.get(s['id'], {}).get('status') == 'ACCEPTED' for s in plan['steps'])
                result['status'] = 'ALL_STEPS_ACCEPTED' if all_accepted else 'NO_READY_STEP'
                result['notice'] += ' 全部子卡接受也不自动接受父WBS或产品。' if all_accepted else ' 等待复核、资源或人工恢复；不自动重试受阻/失败/取消的卡。'
                code = 0 if all_accepted else 3
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        print('TASK_PACKET_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
