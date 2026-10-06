package domain

import (
	"bytes"
	"io"
	"net/http"
	"strings"
)

type orchestrationResponse struct {
	target http.ResponseWriter
	header http.Header
	body   bytes.Buffer
	status int
}

func (w *orchestrationResponse) Header() http.Header { return w.header }
func (w *orchestrationResponse) WriteHeader(status int) {
	if w.status == 0 {
		w.status = status
	}
}
func (w *orchestrationResponse) Write(b []byte) (int, error) {
	if w.status == 0 {
		w.status = 200
	}
	return w.body.Write(b)
}
func (w *orchestrationResponse) Unwrap() http.ResponseWriter { return w.target }

// Failed acceptance/claim transactions roll back before this separate immutable
// audit append. Rejections never publish successful business events or outputs.
func (s *Service) handleAuditedOrchestration(w http.ResponseWriter, r *http.Request, op Operation) {
	response := &orchestrationResponse{target: w, header: make(http.Header)}
	s.handle(response, r, op)
	if response.status >= 400 {
		reply, _ := Decode(response.body.Bytes())
		cid := response.header.Get("X-Correlation-ID")
		tx, e := s.DB.Begin()
		if e != nil {
			s.writeError(w, cid, e)
			return
		}
		var principal any
		if p, err := authenticate(tx, strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")); err == nil {
			principal = p.ID
		}
		_, e = tx.Exec("INSERT INTO orchestration_rejections(correlation_id,project,operation,principal,status,code,body_hash,recorded_at) VALUES(?,?,?,?,?,?,?,?)", cid, r.PathValue("project_id"), op.ID, principal, response.status, Str(reply, "code"), Digest(response.body.Bytes()), Now())
		if e == nil {
			e = tx.Commit()
		} else {
			tx.Rollback()
		}
		if e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	for key, values := range response.header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}
	w.WriteHeader(response.status)
	io.Copy(w, &response.body)
}
