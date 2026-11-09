package domain

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"sort"
)

var clientQueueTables = []string{"client_queue_fences", "client_command_queue", "client_control_requests", "client_control_receipts"}

func backupQueueState(db *sql.DB) (Object, error) {
	var version int
	if err := db.QueryRow(`SELECT coalesce(max(version),0) FROM schema_migrations`).Scan(&version); err != nil {
		return nil, err
	}
	if version < 22 {
		return nil, nil
	}
	state := Object{"format": "RESEARCHOS_COMMAND_QUEUE_V1"}
	for _, table := range clientQueueTables {
		rows, err := db.Query(`SELECT * FROM ` + table)
		if err != nil {
			return nil, err
		}
		cols, err := rows.Columns()
		if err != nil {
			rows.Close()
			return nil, err
		}
		entries := []Object{}
		for rows.Next() {
			values := make([]any, len(cols))
			ptrs := make([]any, len(cols))
			for i := range values {
				ptrs[i] = &values[i]
			}
			if err = rows.Scan(ptrs...); err != nil {
				rows.Close()
				return nil, err
			}
			entry := Object{}
			for i, col := range cols {
				entry[col] = values[i]
			}
			entries = append(entries, entry)
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return nil, err
		}
		sort.Slice(entries, func(i, j int) bool { return Hash(entries[i]) < Hash(entries[j]) })
		state[table] = entries
	}
	return state, nil
}

func validateBackupQueue(db *sql.DB) error {
	state, err := backupQueueState(db)
	if err != nil || state == nil {
		return err
	}
	for _, query := range []string{
		`SELECT count(*) FROM client_queue_fences f LEFT JOIN client_sessions s ON s.project_id=f.project AND s.id=f.session_id LEFT JOIN domain_objects t ON t.project=f.project AND t.kind='Task' AND t.id=f.task_id WHERE s.id IS NULL OR t.id IS NULL OR f.accepted_through<0 OR f.sealed_through<0 OR f.sealed_through>f.accepted_through OR (f.state='SEALED' AND f.sealed_through<>f.accepted_through)`,
		`SELECT count(*) FROM client_queue_fences f WHERE f.run_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM domain_objects r WHERE r.project=f.project AND r.kind='Run' AND r.id=f.run_id AND json_extract(r.body,'$.task_id')=f.task_id AND json_extract(r.body,'$.lease_epoch')=f.runtime_epoch)`,
		`SELECT count(*) FROM client_command_queue q LEFT JOIN client_queue_fences f ON f.generation=q.generation LEFT JOIN domain_objects t ON t.project=q.project AND t.kind='Task' AND t.id=q.task_id WHERE f.generation IS NULL OR f.project<>q.project OR f.task_id<>q.task_id OR f.session_id<>q.session_id OR json_extract(t.body,'$.goal_id') IS NOT q.goal_id OR t.id IS NULL OR q.queue_sequence<1 OR q.queue_sequence>f.accepted_through OR q.accepted_writer_epoch<1`,
		`SELECT count(*) FROM client_queue_fences f WHERE f.accepted_through<>(SELECT count(*) FROM client_command_queue q WHERE q.generation=f.generation)`,
		`SELECT count(*) FROM client_command_queue q WHERE (q.state<>'ENQUEUED' AND q.last_receipt_id IS NULL) OR (q.last_receipt_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM client_control_receipts r WHERE r.receipt_id=q.last_receipt_id AND r.project=q.project AND r.generation=q.generation AND r.command_id=q.command_id))`,
		`SELECT count(*) FROM client_control_receipts r WHERE NOT EXISTS(SELECT 1 FROM client_queue_fences f WHERE f.project=r.project AND f.generation=r.generation) OR (r.previous_receipt_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM client_control_receipts p WHERE p.receipt_id=r.previous_receipt_id AND p.project=r.project AND p.generation=r.generation AND p.command_id=r.command_id AND p.receipt_id<>r.receipt_id))`,
		`SELECT count(*) FROM client_control_requests c WHERE NOT EXISTS(SELECT 1 FROM client_sessions s WHERE s.id=c.session_id AND s.project_id=c.project) OR NOT json_valid(c.task_ids) OR json_array_length(c.task_ids)=0 OR (c.state='CONFIRMED' AND c.final_response IS NULL)`,
	} {
		var n int
		if err = db.QueryRow(query).Scan(&n); err != nil {
			return err
		}
		if n != 0 {
			return fmt.Errorf("BACKUP_QUEUE_BINDING: %d invalid rows", n)
		}
	}
	for _, query := range []string{
		`SELECT count(*) FROM client_command_queue q WHERE NOT EXISTS(SELECT 1 FROM idempotency i WHERE i.principal=q.principal AND i.project=q.project AND i.operation='v2:session.send' AND i.key=q.command_id AND i.request_hash=q.request_hash)`,
		`SELECT count(*) FROM client_control_requests c WHERE NOT EXISTS(SELECT 1 FROM idempotency i WHERE i.principal=c.principal AND i.project=c.project AND i.operation='v2:session.control' AND i.key=c.command_id AND i.request_hash=c.request_hash) OR c.original_response IS NULL`,
		`SELECT count(*) FROM client_queue_fences f WHERE f.process_identity IS NOT NULL AND NOT EXISTS(SELECT 1 FROM runtime_dispatches d WHERE d.project=f.project AND d.run=f.run_id AND d.epoch=f.runtime_epoch AND d.dispatch_key=f.dispatch_key AND d.manifest_hash=f.manifest_hash AND d.identity=f.process_identity)`} {
		var n int
		if err = db.QueryRow(query).Scan(&n); err != nil {
			return err
		}
		if n != 0 {
			return fmt.Errorf("BACKUP_QUEUE_REQUEST_OR_PROCESS_BINDING")
		}
	}
	for _, row := range state["client_command_queue"].([]Object) {
		if Digest([]byte(Str(row, "content"))) != row["content_hash"] {
			return fmt.Errorf("BACKUP_QUEUE_CONTENT_HASH")
		}
		var content Object
		if json.Unmarshal([]byte(Str(row, "content")), &content) != nil || len(content) != 2 {
			return fmt.Errorf("BACKUP_QUEUE_CONTENT")
		}

		text, ok := content["text"].(string)
		attachments, valid := content["attachments"].([]any)
		if !ok || !valid || text == "" || len(Str(row, "content")) > 32*1024 {
			return fmt.Errorf("BACKUP_QUEUE_CONTENT_SHAPE")
		}
		for _, value := range attachments {
			a, ok := value.(map[string]any)
			if !ok || len(a) != 3 {
				return fmt.Errorf("BACKUP_QUEUE_ATTACHMENT")
			}
			ref, ok := a["ref"].(map[string]any)
			body, valid := a["text"].(string)
			if !ok || !valid || ref["entity_type"] != "Artifact" || ref["content_hash"] != Digest([]byte(body)) {
				return fmt.Errorf("BACKUP_QUEUE_ATTACHMENT_BINDING")
			}
		}
	}
	receipts := map[string]Object{}
	for _, row := range state["client_control_receipts"].([]Object) {
		if Digest([]byte(Str(row, "body"))) != row["body_hash"] {
			return fmt.Errorf("BACKUP_QUEUE_RECEIPT_HASH")
		}
		receipts[Str(row, "receipt_id")] = row
	}
	for id := range receipts {
		seen := map[string]bool{}
		for id != "" {
			if seen[id] {
				return fmt.Errorf("BACKUP_QUEUE_RECEIPT_CYCLE")
			}
			seen[id] = true
			id = Str(receipts[id], "previous_receipt_id")
		}
	}
	for _, row := range state["client_control_requests"].([]Object) {
		var ids []string
		if json.Unmarshal([]byte(Str(row, "task_ids")), &ids) != nil {
			return fmt.Errorf("BACKUP_CONTROL_MEMBERSHIP")
		}
		for _, id := range ids {
			var count int
			if err = db.QueryRow(`SELECT count(*) FROM domain_objects t WHERE t.project=? AND t.kind='Task' AND t.id=? AND (json_extract(t.body,'$.goal_id')=? OR json_extract(t.body,'$.active_run_id')=?)`, row["project"], id, row["target_id"], row["target_id"]).Scan(&count); err != nil {
				return err
			}
			if count != 1 {
				return fmt.Errorf("BACKUP_CONTROL_MEMBERSHIP")
			}
		}
	}
	return validateModelStreamBackup(db)
}

func fenceRestoredClientQueues(tx *sql.Tx) error {
	var version int
	if err := tx.QueryRow(`SELECT coalesce(max(version),0) FROM schema_migrations`).Scan(&version); err != nil {
		return err
	}
	if version < 22 {
		return nil
	}
	rows, err := tx.Query(`SELECT project,generation,command_id,state,last_receipt_id FROM client_command_queue WHERE state NOT IN ('CONSUMED','DROPPED')`)
	if err != nil {
		return err
	}
	entries := []Object{}
	for rows.Next() {
		var project, generation, command, state string
		var prior sql.NullString
		if err = rows.Scan(&project, &generation, &command, &state, &prior); err != nil {
			rows.Close()
			return err
		}
		var previous any
		if prior.Valid {
			previous = prior.String
		}
		entries = append(entries, Object{"project": project, "generation": generation, "command": command, "state": state, "previous": previous})
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, entry := range entries {
		receipt := ID()
		if err = appendClientReceipt(tx, Str(entry, "project"), Str(entry, "generation"), Str(entry, "command"), "RESTORE_UNKNOWN", receipt, Object{"prior_state": entry["state"], "reason": "SNAPSHOT_MAY_PREDATE_SEND"}, entry["previous"]); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE client_command_queue SET state='UNKNOWN',revision=revision+1,last_receipt_id=? WHERE project=? AND generation=? AND command_id=?`, receipt, entry["project"], entry["generation"], entry["command"]); err != nil {
			return err
		}
	}
	if _, err = tx.Exec(`UPDATE client_queue_fences SET restore_fenced=1,state=CASE WHEN state='CANCEL_FENCED' THEN state ELSE 'RECONCILING' END,revision=revision+1 WHERE state NOT IN ('SEALED') OR EXISTS(SELECT 1 FROM client_command_queue q WHERE q.generation=client_queue_fences.generation AND q.state='UNKNOWN')`); err != nil {
		return err
	}
	if _, err = tx.Exec(`UPDATE client_control_requests SET state='RECONCILING' WHERE state<>'CONFIRMED'`); err != nil {
		return err
	}
	_, err = tx.Exec(`UPDATE client_sessions SET resume_requires_explicit_user=1 WHERE id IN (SELECT session_id FROM client_queue_fences WHERE restore_fenced=1) OR id IN (SELECT session_id FROM client_control_requests WHERE state='RECONCILING')`)
	return err
}
