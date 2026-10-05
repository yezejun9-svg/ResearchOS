package domain

import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

const workbenchReplayWindow = 24 * time.Hour
const workbenchHeartbeat = 15 * time.Second

// Each poll finishes its transaction before any network write or wait. The
// retained outbox is never deleted; 24h only bounds SSE transport replay.
func (s *Service) workbenchEvents(ctx context.Context, token, project string, op Operation, after int64) ([]Object, int64, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, after, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, after, e
	}
	roleOK := false
	for _, role := range op.Roles {
		roleOK = roleOK || p.HasRole(role)
	}
	if !roleOK {
		return nil, after, Fail(403, "FORBIDDEN", "role not authorized for events")
	}
	if !p.Allowed(project, "", "", false) {
		return nil, after, Fail(404, "NOT_FOUND", "project unavailable")
	}
	var watermark int64
	if e = tx.QueryRow("SELECT COALESCE(MAX(sequence),0) FROM outbox WHERE project=?", project).Scan(&watermark); e != nil {
		return nil, after, e
	}
	// Absence of Last-Event-ID starts at the current journal watermark, so an
	// initial subscription cannot replay unbounded historical activity.
	if after == -1 {
		return []Object{}, watermark, nil
	}
	if after > watermark {
		return nil, after, Fail(400, "INVALID_REQUEST", "event cursor exceeds current watermark")
	}
	if after == watermark {
		return []Object{}, after, nil
	}
	rows, e := tx.Query("SELECT sequence,id,body FROM outbox WHERE project=? AND sequence>? ORDER BY sequence LIMIT 128", project, after)
	if e != nil {
		return nil, after, e
	}
	type entry struct {
		sequence int64
		id       string
		body     Object
	}
	batch := []entry{}
	for rows.Next() {
		var raw string
		var row entry
		if e = rows.Scan(&row.sequence, &row.id, &raw); e != nil {
			rows.Close()
			return nil, after, e
		}
		ev, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return nil, after, err
		}
		row.body = ev
		batch = append(batch, row)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, after, e
	}
	if len(batch) == 0 {
		return nil, after, Fail(410, "CURSOR_EXPIRED", "fetch current state/progress then resume from its event sequence")
	}
	visible := []Object{}
	for _, row := range batch {
		if row.sequence != after+1 {
			return nil, after, Fail(410, "CURSOR_EXPIRED", "fetch current state/progress then resume from its event sequence")
		}
		ev := row.body
		if _, typed := ev["protocol_version"]; typed {
			// Session events use a separate local sequence and have no v1 timestamp.
			// Consume their global positions without emitting a different wire schema.
			clientEvent, err := DecodeEvent(Bytes(ev))
			if err != nil {
				return nil, after, err
			}
			if *clientEvent.EventID != row.id {
				return nil, after, Fail(500, "INTERNAL_ERROR", "session event identity differs from outbox")
			}
			after = row.sequence
			continue
		}
		sequence, err := Num(ev, "sequence")
		if err != nil {
			return nil, after, err
		}
		at, err := time.Parse(time.RFC3339Nano, Str(ev, "created_at"))
		if err != nil {
			return nil, after, err
		}
		if sequence != row.sequence || time.Since(at) > workbenchReplayWindow {
			return nil, after, Fail(410, "CURSOR_EXPIRED", "fetch current state/progress then resume from its event sequence")
		}
		after = sequence
		if s.visible(tx, p, project, ev) {
			visible = append(visible, ev)
		}
	}
	return visible, after, nil
}

func (s *Service) streamWorkbenchEvents(w http.ResponseWriter, r *http.Request, op Operation) {
	cid := ID()
	if !strings.HasPrefix(r.Header.Get("Authorization"), "Bearer ") {
		s.writeError(w, cid, Fail(401, "UNAUTHENTICATED", "Bearer credential required"))
		return
	}
	if len(r.URL.Query()) != 0 || r.ContentLength != 0 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "event stream accepts headers only"))
		return
	}
	after := int64(-1)
	values, present := r.Header[http.CanonicalHeaderKey("Last-Event-ID")]
	if present {
		value := r.Header.Get("Last-Event-ID")
		valid := len(values) == 1 && value != ""
		for _, c := range value {
			valid = valid && c >= '0' && c <= '9'
		}
		n, e := strconv.ParseInt(value, 10, 64)
		if !valid || e != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "invalid Last-Event-ID"))
			return
		}
		after = n
	}
	token := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
	project := r.PathValue("project_id")
	events, position, e := s.workbenchEvents(r.Context(), token, project, op, after)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Accel-Buffering", "no")
	w.Header().Set("X-Correlation-ID", cid)
	controller := http.NewResponseController(w)
	write := func(payload string) bool {
		_ = controller.SetWriteDeadline(time.Now().Add(5 * time.Second))
		if _, err := fmt.Fprint(w, payload); err != nil {
			return false
		}
		return controller.Flush() == nil
	}
	if !write(": connected\n\n") {
		return
	}
	// ponytail: short polling fits local SQLite; replace the wakeup with a commit
	// signal if many concurrent subscribers make idle polling measurable.
	poll := time.NewTicker(250 * time.Millisecond)
	heartbeat := time.NewTicker(workbenchHeartbeat)
	defer poll.Stop()
	defer heartbeat.Stop()
	for {
		for _, ev := range events {
			if !write(fmt.Sprintf("id: %v\nevent: message\ndata: %s\n\n", ev["sequence"], Bytes(ev))) {
				return
			}
		}
		after = position
		select {
		case <-r.Context().Done():
			return
		case <-heartbeat.C:
			if !write(": heartbeat\n\n") {
				return
			}
		case <-poll.C:
		}
		events, position, e = s.workbenchEvents(r.Context(), token, project, op, after)
		if e != nil {
			// Headers may already be sent. Revocation or expiry terminates this
			// connection; reconnection receives the current HTTP auth/error code.
			return
		}
	}
}
