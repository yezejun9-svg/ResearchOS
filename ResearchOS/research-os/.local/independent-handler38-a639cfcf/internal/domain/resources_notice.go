package domain

import (
	"database/sql"
	"encoding/json"
)

// resourceRequestNotice gives the project's active human-facing principals one IN_APP notice per
// ResourceRequest. The exists-check is the whole point: a repeated shortage round merges into the same
// OPEN request (createResourceRequest dedups on the project/category/account/reason hash), so without the
// check every round would raise a fresh alert for one unresolved blocker. Mirrors the milestone notice in
// milestones.go, including the two-phase shape - recipients are collected and the rows closed before any
// insert, because the store runs on a single connection and a query issued mid-iteration deadlocks it.
// Delivery stops at the in-app queue: no external channel is authorised here.
func (s *Service) resourceRequestNotice(tx *sql.Tx, project string, request Object, actor, cid string) error {
	type recipient struct {
		id    string
		roles []string
	}
	rows, e := tx.Query("SELECT p.id,p.roles FROM auth_principals p JOIN auth_grants g ON g.principal=p.id "+
		"WHERE p.revoked=0 AND g.project=? AND g.task='' AND g.run='' GROUP BY p.id,p.roles ORDER BY p.id", project)
	if e != nil {
		return e
	}
	recipients := []recipient{}
	for rows.Next() {
		var r recipient
		var roles string
		if e = rows.Scan(&r.id, &roles); e != nil {
			rows.Close()
			return e
		}
		if e = json.Unmarshal([]byte(roles), &r.roles); e != nil {
			rows.Close()
			return e
		}
		recipients = append(recipients, r)
	}
	if e = rows.Err(); e != nil {
		rows.Close()
		return e
	}
	rows.Close()
	for _, r := range recipients {
		human := false
		for _, role := range r.roles {
			if role == "OWNER" || role == "READER" {
				human = true
			}
		}
		if !human {
			continue
		}
		var exists int
		e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Notification' "+
			"AND json_extract(body,'$.resource_request_id')=? AND json_extract(body,'$.recipient_id')=? "+
			"AND json_extract(body,'$.channel')='IN_APP'", project, request["id"], r.id).Scan(&exists)
		if e != nil {
			return e
		}
		if exists != 0 {
			continue
		}
		n := Merge(Base(project), Object{"release_id": nil, "resource_request_id": request["id"],
			"recipient_id": r.id, "channel": "IN_APP",
			"dedup_key": Hash([]any{request["id"], r.id, "IN_APP"}), "status": "UNREAD",
			"summary": Str(request, "summary"), "read_at": nil})
		if e = s.put(tx, "Notification", n); e != nil {
			return e
		}
		if e = s.event(tx, project, "Notification", n, actor, cid, "NOTIFICATION_CHANGED"); e != nil {
			return e
		}
	}
	return nil
}
