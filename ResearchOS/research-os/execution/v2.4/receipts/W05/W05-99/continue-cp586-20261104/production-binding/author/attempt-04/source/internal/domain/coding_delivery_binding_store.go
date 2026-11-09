package domain

import (
	"context"
	"database/sql"
	_ "embed"
	"fmt"
	"strings"
	"sync"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

// This dedicated schema is intentionally not installed by a migration, store
// startup, API or backup hook. Old databases lack this capability and fail closed.
//
//go:embed contracts/coding_delivery_bindings.sql
var codingDeliveryBindingSQL string

const codingDeliveryBindingColumns = `binding_schema,schema_version,project,goal_id,task_id,approval_issuer_ref,approval_ref,lineage_issuer_ref,business_anchor,owner_principal,owner_root,owner_host,task_contract_hash,goal_contract_hash,binding_body,binding_hash`
const codingDeliveryBindingInsert = `INSERT INTO coding_delivery_bindings (` + codingDeliveryBindingColumns + `) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`

type codingDeliveryBindingQuery interface {
	QueryContext(context.Context, string, ...any) (*sql.Rows, error)
	QueryRowContext(context.Context, string, ...any) *sql.Row
}

var codingDeliverySchemaOnce sync.Once
var codingDeliverySchemaExpected Object
var codingDeliverySchemaError error

func codingDeliverySchemaRows(ctx context.Context, q codingDeliveryBindingQuery, query string) ([]Object, error) {
	rows, err := q.QueryContext(ctx, query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}
	result := []Object{}
	for rows.Next() {
		values := make([]any, len(columns))
		pointers := make([]any, len(columns))
		for i := range values {
			pointers[i] = &values[i]
		}
		if err = rows.Scan(pointers...); err != nil {
			return nil, err
		}
		row := Object{}
		for i, name := range columns {
			row[name] = values[i]
		}
		result = append(result, row)
	}
	return result, rows.Err()
}

func codingDeliverySchemaSnapshot(ctx context.Context, q codingDeliveryBindingQuery) (Object, error) {
	result := Object{}
	for _, spec := range []struct{ name, query string }{
		{"objects", `SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE tbl_name='coding_delivery_bindings' ORDER BY type,name`},
		{"columns", `SELECT * FROM pragma_table_xinfo('coding_delivery_bindings') ORDER BY cid`},
		{"foreign_keys", `SELECT * FROM pragma_foreign_key_list('coding_delivery_bindings') ORDER BY id,seq`},
		{"indexes", `SELECT * FROM pragma_index_list('coding_delivery_bindings') ORDER BY name`},
	} {
		rows, err := codingDeliverySchemaRows(ctx, q, spec.query)
		if err != nil {
			return nil, err
		}
		result[spec.name] = rows
	}
	details := Object{}
	for _, row := range result["indexes"].([]Object) {
		name, ok := row["name"].(string)
		if !ok {
			return nil, fmt.Errorf("CODING_DELIVERY_SCHEMA_INDEX")
		}
		escaped := strings.ReplaceAll(name, "'", "''")
		rows, err := codingDeliverySchemaRows(ctx, q, `SELECT * FROM pragma_index_xinfo('`+escaped+`') ORDER BY seqno`)
		if err != nil {
			return nil, err
		}
		details[name] = rows
	}
	result["index_columns"] = details
	return result, nil
}

func codingDeliveryBindingSchemaIntegrity(ctx context.Context, q codingDeliveryBindingQuery) error {
	codingDeliverySchemaOnce.Do(func() {
		expected, err := sql.Open("sqlite", ":memory:")
		if err != nil {
			codingDeliverySchemaError = err
			return
		}
		defer expected.Close()
		expected.SetMaxOpenConns(1)
		// Only a dependency for parsing FKs/triggers; not a substitute for canonical
		// subjects. The expected fingerprint contains only the dedicated schema.
		_, err = expected.Exec(`CREATE TABLE domain_objects(project TEXT NOT NULL,kind TEXT NOT NULL,id TEXT NOT NULL,body TEXT NOT NULL,PRIMARY KEY(project,kind,id));`)
		if err == nil {
			_, err = expected.Exec(codingDeliveryBindingSQL)
		}
		if err == nil {
			codingDeliverySchemaExpected, err = codingDeliverySchemaSnapshot(context.Background(), expected)
		}
		codingDeliverySchemaError = err
	})
	if codingDeliverySchemaError != nil {
		return codingDeliverySchemaError
	}
	var foreignKeys int
	if err := q.QueryRowContext(ctx, "PRAGMA foreign_keys").Scan(&foreignKeys); err != nil {
		return err
	}
	if foreignKeys != 1 {
		return fmt.Errorf("CODING_DELIVERY_FOREIGN_KEYS_REQUIRED")
	}
	actual, err := codingDeliverySchemaSnapshot(ctx, q)
	if err != nil {
		return err
	}
	if Hash(actual) != Hash(codingDeliverySchemaExpected) {
		return fmt.Errorf("CODING_DELIVERY_SCHEMA_UNSUPPORTED")
	}
	rows, err := q.QueryContext(ctx, "PRAGMA foreign_key_check(coding_delivery_bindings)")
	if err != nil {
		return err
	}
	defer rows.Close()
	if rows.Next() {
		return fmt.Errorf("CODING_DELIVERY_FOREIGN_KEY_INTEGRITY")
	}
	return rows.Err()
}

var codingDeliveryContractSchemaOnce sync.Once
var codingDeliveryContractSchema *Contracts
var codingDeliveryContractSchemaError error

func codingDeliveryContractIntegrity(value any, expectedHash string, mandatory ...string) error {
	codingDeliveryContractSchemaOnce.Do(func() {
		// Reuse the exact embedded public domain schema, including closed CheckSpec
		// and VersionRef types. No hand-written subset or new contract is installed.
		if Digest(backupConfigurationDomain) != "sha256:b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54" {
			codingDeliveryContractSchemaError = fmt.Errorf("CODING_DELIVERY_CONTRACT_SCHEMA_SOURCE")
			return
		}
		doc, err := Decode(backupConfigurationDomain)
		if err != nil {
			codingDeliveryContractSchemaError = err
			return
		}
		// Use the same offline domain-definition compiler and generic-value
		// validation as LoadContracts. The protocol loader requires method/event
		// maps and intentionally cannot be used for a domain-only document.
		compiler := jsonschema.NewCompiler()
		compiler.UseLoader(localOnly{})
		compiler.AssertFormat()
		compiler.DefaultDraft(jsonschema.Draft2020)
		location := Str(doc, "$id")
		if err = compiler.AddResource(location, doc); err != nil {
			codingDeliveryContractSchemaError = err
			return
		}
		schema, err := compiler.Compile(location + "#/$defs/AcceptanceContract")
		if err != nil {
			codingDeliveryContractSchemaError = err
			return
		}
		codingDeliveryContractSchema = &Contracts{Schemas: map[string]*jsonschema.Schema{"AcceptanceContract": schema}}
	})
	if codingDeliveryContractSchemaError != nil {
		return codingDeliveryContractSchemaError
	}
	if err := codingDeliveryContractSchema.Validate("AcceptanceContract", value); err != nil {
		return err
	}
	c, ok := value.(map[string]any)
	if !ok || c["contract_hash"] != expectedHash || c["contract_hash"] != contractDigest(c) {
		return fmt.Errorf("CODING_DELIVERY_CONTRACT_INTEGRITY")
	}
	checks, ok := c["checks"].([]any)
	if !ok {
		return fmt.Errorf("CODING_DELIVERY_CONTRACT_CHECKS")
	}
	seen, required := map[string]bool{}, map[string]bool{}
	for _, item := range checks {
		check, ok := item.(map[string]any)
		if !ok || seen[Str(check, "check_id")] {
			return fmt.Errorf("CODING_DELIVERY_CONTRACT_CHECKS")
		}
		id := Str(check, "check_id")
		seen[id] = true
		if check["required"] == true && check["kind"] == "DETERMINISTIC" {
			required[id] = true
		}
	}
	for _, id := range mandatory {
		if !required[id] {
			return fmt.Errorf("CODING_DELIVERY_REQUIRED_CHECK_MISSING")
		}
	}
	return nil
}
func codingDeliverySubjectIntegrity(b codingDeliveryBinding, goal, task Object) error {
	if goal["id"] != b.GoalID || goal["project_id"] != b.Project || task["id"] != b.TaskID || task["project_id"] != b.Project ||
		task["goal_id"] != b.GoalID || task["origin_problem_id"] != b.OriginProblemID || task["candidate_id"] != b.CandidateID ||
		Hash(task["requirement_refs"]) != b.RequirementRefsHash || Hash(goal["requirement_refs"]) != b.RequirementRefsHash ||
		Hash(task["input_refs"]) != b.InputRefsHash {
		return fmt.Errorf("CODING_DELIVERY_CANONICAL_SUBJECT_MISMATCH")
	}
	if err := codingDeliveryContractIntegrity(task["acceptance_contract"], b.TaskContractHash, "mu.turn-output-v1", "coding.pure-scalar-delivery-v1"); err != nil {
		return err
	}
	return codingDeliveryContractIntegrity(goal["acceptance_contract"], b.GoalContractHash, "coding.accepted-task-delivery-v1")
}

func codingDeliverySubjectsTx(ctx context.Context, tx *sql.Tx, b codingDeliveryBinding) error {
	subjects := make([]Object, 2)
	for i, subject := range []struct{ kind, id string }{{"Goal", b.GoalID}, {"Task", b.TaskID}} {
		var raw string
		if err := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?`, b.Project, subject.kind, subject.id).Scan(&raw); err != nil {
			return err
		}
		var err error
		subjects[i], err = Decode([]byte(raw))
		if err != nil {
			return err
		}
	}
	return codingDeliverySubjectIntegrity(b, subjects[0], subjects[1])
}

func codingDeliveryBindingArguments(b codingDeliveryBinding, raw []byte, digest string) []any {
	return []any{b.BindingSchema, b.SchemaVersion, b.Project, b.GoalID, b.TaskID, b.ApprovalIssuerRef, b.ApprovalRef,
		b.LineageIssuerRef, b.BusinessAnchor, b.OwnerPrincipal, b.OwnerRoot, b.OwnerHost, b.TaskContractHash, b.GoalContractHash, string(raw), digest}
}

// A future normal creation transaction may call this only after authenticating
// the original Host plan and checking the original approval journal/UNKNOWN and
// NoProgress lineage. This helper has no authorization-producing caller today.
// It neither commits nor performs external effects; rollback refunds SQL rows
// only. No row or rolled-back row ever proves external approval is unused.
func insertCodingDeliveryBindingTx(ctx context.Context, tx *sql.Tx, b, expected codingDeliveryBinding) error {
	if err := codingDeliveryBindingContext(b, expected); err != nil {
		return err
	}
	if err := codingDeliveryBindingSchemaIntegrity(ctx, tx); err != nil {
		return err
	}
	if err := codingDeliverySubjectsTx(ctx, tx, b); err != nil {
		return err
	}
	raw, digest, err := codingDeliveryBindingBytes(b)
	if err != nil {
		return err
	}
	result, err := tx.ExecContext(ctx, codingDeliveryBindingInsert, codingDeliveryBindingArguments(b, raw, digest)...)
	if err != nil {
		return err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if affected != 1 {
		return fmt.Errorf("CODING_DELIVERY_EXACT_INSERT_REQUIRED")
	}
	return nil
}

// A missing binding is unsupported, never approval to retry an external scope.
// The result proves stored data integrity only. Current authority/Run/lease,
// qualification, journal settlement and acceptance remain independent gates.
func readCodingDeliveryBindingTx(ctx context.Context, tx *sql.Tx, project, task string, expected codingDeliveryBinding) (codingDeliveryBinding, error) {
	var b codingDeliveryBinding
	if err := expected.validate(); err != nil {
		return b, err
	}
	if project != expected.Project || task != expected.TaskID {
		return b, fmt.Errorf("CODING_DELIVERY_EXPECTED_SUBJECT_MISMATCH")
	}
	if err := codingDeliveryBindingSchemaIntegrity(ctx, tx); err != nil {
		return b, err
	}
	rows, err := tx.QueryContext(ctx, `SELECT `+codingDeliveryBindingColumns+` FROM coding_delivery_bindings WHERE project=? AND task_id=?`, project, task)
	if err != nil {
		return b, err
	}
	var identity codingDeliveryBindingIdentity
	var body, digest string
	count := 0
	for rows.Next() {
		count++
		err = rows.Scan(&identity.BindingSchema, &identity.SchemaVersion, &identity.Project, &identity.GoalID, &identity.TaskID,
			&identity.ApprovalIssuerRef, &identity.ApprovalRef, &identity.LineageIssuerRef, &identity.BusinessAnchor,
			&identity.OwnerPrincipal, &identity.OwnerRoot, &identity.OwnerHost, &identity.TaskContractHash, &identity.GoalContractHash, &body, &digest)
		if err != nil {
			break
		}
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return b, err
	}
	if count != 1 {
		return b, fmt.Errorf("CODING_DELIVERY_EXACT_BINDING_REQUIRED")
	}
	b, err = decodeCodingDeliveryBinding([]byte(body))
	if err != nil {
		return b, err
	}
	if identity != b.codingDeliveryBindingIdentity || !codingDeliveryHash(digest) || Hash(b) != digest {
		return b, fmt.Errorf("CODING_DELIVERY_COLUMN_OR_HASH_MISMATCH")
	}
	if err = codingDeliveryBindingContext(b, expected); err != nil {
		return b, err
	}
	if err = codingDeliverySubjectsTx(ctx, tx, b); err != nil {
		return b, err
	}
	return b, nil
}

type codingDeliveryBindingKey struct{ Project, TaskID string }

// This standalone complete-inventory validator can check a fresh restored
// fixture. It is not installed into the product backup/restore protocol.
func codingDeliveryBindingInventoryTx(ctx context.Context, tx *sql.Tx, expected map[codingDeliveryBindingKey]codingDeliveryBinding) error {
	if err := codingDeliveryBindingSchemaIntegrity(ctx, tx); err != nil {
		return err
	}
	rows, err := tx.QueryContext(ctx, `SELECT project,task_id FROM coding_delivery_bindings ORDER BY project,task_id`)
	if err != nil {
		return err
	}
	keys := []codingDeliveryBindingKey{}
	for rows.Next() {
		var key codingDeliveryBindingKey
		if err = rows.Scan(&key.Project, &key.TaskID); err != nil {
			break
		}
		keys = append(keys, key)
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return err
	}
	if len(keys) != len(expected) {
		return fmt.Errorf("CODING_DELIVERY_COMPLETE_INVENTORY_MISMATCH")
	}
	for _, key := range keys {
		b, ok := expected[key]
		if !ok {
			return fmt.Errorf("CODING_DELIVERY_COMPLETE_INVENTORY_MISMATCH")
		}
		if _, err = readCodingDeliveryBindingTx(ctx, tx, key.Project, key.TaskID, b); err != nil {
			return err
		}
	}
	return nil
}
