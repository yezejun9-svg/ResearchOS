"""Render the explicit prototype DDL; no database is opened."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prototype import BODY_FIELDS, BODY_STRING_FIELDS, DECIMAL_FIELDS, HASH_FIELDS, IDENTITY_COLUMNS, SCHEMA_NAME

def literal(value):
    return "'" + value.replace("'", "''") + "'"

def nonempty(expression):
    return f"length(trim({expression},char(9)||char(10)||char(13)||' '))>0 AND instr({expression},char(0))=0"

def hash_shape(expression):
    return f"length({expression})=71 AND substr({expression},1,7)='sha256:' AND substr({expression},8) NOT GLOB '*[^0-9a-f]*' AND instr({expression},char(0))=0"

lines = [
    '-- C-only schema candidate. No production migration number or authorization is supplied.',
    '-- domain_objects is an explicitly fake canonical-subject table created only by fixture code.',
    'CREATE TABLE coding_delivery_bindings (',
]
definitions = []
for name in IDENTITY_COLUMNS:
    if name == 'schema_version':
        definitions.append(" schema_version INTEGER NOT NULL CHECK(typeof(schema_version)='integer' AND schema_version=1)")
    else:
        check = hash_shape(name) if name in HASH_FIELDS else nonempty(name)
        if name == 'binding_schema':
            check += ' AND binding_schema=' + literal(SCHEMA_NAME)
        definitions.append(f' {name} TEXT NOT NULL CHECK({check})')
definitions += [
    " binding_body TEXT NOT NULL CHECK(json_valid(binding_body) AND json_type(binding_body) IS 'object' AND length(CAST(binding_body AS BLOB))<=65536)",
    ' binding_hash TEXT NOT NULL CHECK(' + hash_shape('binding_hash') + ')',
    " goal_subject_kind TEXT GENERATED ALWAYS AS ('Goal') VIRTUAL",
    " task_subject_kind TEXT GENERATED ALWAYS AS ('Task') VIRTUAL",
    ' PRIMARY KEY(project,task_id)',
    ' FOREIGN KEY(project,goal_subject_kind,goal_id) REFERENCES domain_objects(project,kind,id) ON UPDATE RESTRICT ON DELETE RESTRICT',
    ' FOREIGN KEY(project,task_subject_kind,task_id) REFERENCES domain_objects(project,kind,id) ON UPDATE RESTRICT ON DELETE RESTRICT',
    ' CHECK(task_contract_hash<>goal_contract_hash)',
]
for name in IDENTITY_COLUMNS:
    value = f"json_extract(binding_body,'$.{name}')"
    kind = 'integer' if name == 'schema_version' else 'text'
    condition = f"json_type(binding_body,'$.{name}') IS '{kind}' AND {value} IS {name}"
    if name == 'schema_version':
        condition += " AND typeof(" + value + ")='integer'"
    definitions.append(' CHECK(' + condition + ')')
for name in BODY_STRING_FIELDS:
    if name in IDENTITY_COLUMNS:
        continue
    value = f"json_extract(binding_body,'$.{name}')"
    condition = f"json_type(binding_body,'$.{name}') IS 'text' AND " + nonempty(value)
    if name in HASH_FIELDS:
        condition += ' AND ' + hash_shape(value)
    if name == 'creation_method':
        condition += f" AND {value}='goal.start'"
    if name in DECIMAL_FIELDS:
        condition += f" AND length({value}) BETWEEN 1 AND 19 AND substr({value},1,1) BETWEEN '1' AND '9' AND {value} NOT GLOB '*[^0-9]*' AND (length({value})<19 OR {value}<='9223372036854775807' COLLATE BINARY)"
    definitions.append(' CHECK(' + condition + ')')
lines.append(',\n'.join(definitions))
lines += [
    ') STRICT, WITHOUT ROWID;',
    'CREATE UNIQUE INDEX coding_delivery_goal_unique ON coding_delivery_bindings(project,goal_id);',
    'CREATE UNIQUE INDEX coding_delivery_approval_unique ON coding_delivery_bindings(approval_issuer_ref,approval_ref);',
    'CREATE UNIQUE INDEX coding_delivery_lineage_unique ON coding_delivery_bindings(lineage_issuer_ref,business_anchor);',
    'CREATE TRIGGER coding_delivery_insert_conflict BEFORE INSERT ON coding_delivery_bindings',
    'WHEN EXISTS(SELECT 1 FROM coding_delivery_bindings b WHERE',
    ' (b.project=NEW.project AND (b.task_id=NEW.task_id OR b.goal_id=NEW.goal_id)) OR',
    ' (b.approval_issuer_ref=NEW.approval_issuer_ref AND b.approval_ref=NEW.approval_ref) OR',
    ' (b.lineage_issuer_ref=NEW.lineage_issuer_ref AND b.business_anchor=NEW.business_anchor))',
    "BEGIN SELECT RAISE(ABORT,'immutable binding identity already occupied'); END;",
    'CREATE TRIGGER coding_delivery_closed_body BEFORE INSERT ON coding_delivery_bindings',
    f"WHEN (SELECT count(*) FROM json_each(NEW.binding_body))<>{len(BODY_FIELDS)} OR",
    ' EXISTS(SELECT 1 FROM json_each(NEW.binding_body) WHERE key NOT IN (' + ','.join(literal(name) for name in BODY_FIELDS) + ')) OR',
    ' EXISTS(SELECT 1 FROM json_each(NEW.binding_body) GROUP BY key HAVING count(*)<>1)',
    "BEGIN SELECT RAISE(ABORT,'closed unique-key prototype binding body required'); END;",
    'CREATE TRIGGER coding_delivery_subject_relation BEFORE INSERT ON coding_delivery_bindings',
    "WHEN NOT EXISTS(SELECT 1 FROM domain_objects t WHERE t.project=NEW.project AND t.kind='Task' AND t.id=NEW.task_id AND json_extract(t.body,'$.goal_id') IS NEW.goal_id)",
    "BEGIN SELECT RAISE(ABORT,'fake canonical Task/Goal relation missing'); END;",
    'CREATE TRIGGER coding_delivery_no_update BEFORE UPDATE ON coding_delivery_bindings',
    "BEGIN SELECT RAISE(ABORT,'coding delivery binding is immutable'); END;",
    'CREATE TRIGGER coding_delivery_no_delete BEFORE DELETE ON coding_delivery_bindings',
    "BEGIN SELECT RAISE(ABORT,'coding delivery binding cannot be deleted'); END;",
]
target = ROOT / 'coding_delivery_bindings.sql'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write('\n'.join(lines) + '\n')
print('rendered C-only DDL; no database opened')
