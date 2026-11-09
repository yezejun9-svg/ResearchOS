package api

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"

	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/domain"
)

func mountHarnessV1(mux *http.ServeMux, port domain.HarnessAPI) {
	reply := func(w http.ResponseWriter, value domain.Object, err error, status int) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		if err != nil {
			code, message := "INTERNAL_ERROR", "Host operation failed"
			status = 500
			var h *domain.HarnessError
			body := domain.Object{"code": code, "message": message, "retryable": false, "task_ref": nil, "current_task_revision": nil, "current_run": nil}
			if errors.As(err, &h) {
				status = h.Status
				body["code"] = h.Code
				body["message"] = h.Message
				body["task_ref"] = h.TaskRef
				body["current_task_revision"] = h.Revision
				body["current_run"] = h.Run
			}
			w.WriteHeader(status)
			json.NewEncoder(w).Encode(domain.Object{"api_version": "harness.v1", "error": body})
			return
		}
		w.WriteHeader(status)
		json.NewEncoder(w).Encode(value)
	}
	fail := func(w http.ResponseWriter, status int, code, message string) {
		reply(w, nil, &domain.HarnessError{Status: status, Code: code, Message: message}, status)
	}
	token := func(w http.ResponseWriter, r *http.Request) (string, bool) {
		value := bearerToken(r)
		if value == "" {
			fail(w, 401, "HOST_AUTH_REQUIRED", "Host credential required")
			return "", false
		}
		if port == nil {
			fail(w, 503, "HARNESS_UNAVAILABLE", "Codex Harness unavailable")
			return "", false
		}
		return value, true
	}
	query := func(w http.ResponseWriter, r *http.Request, allowed ...string) bool {
		set := map[string]bool{}
		for _, key := range allowed {
			set[key] = true
		}
		for key, values := range r.URL.Query() {
			if key == "cursor" && len(values) == 1 {
				if _, err := domain.HarnessDecimal(values[0], false); err != nil {
					fail(w, 400, "INVALID_REQUEST", "canonical cursor required")
					return false
				}
			}
			if !set[key] || len(values) != 1 {
				fail(w, 400, "INVALID_REQUEST", "unknown or repeated query field")
				return false
			}
		}
		return true
	}
	readBody := func(w http.ResponseWriter, r *http.Request, out any, required ...string) bool {
		raw, err := io.ReadAll(io.LimitReader(r.Body, 128*1024+1))
		if err != nil || len(raw) > 128*1024 {
			fail(w, 400, "INVALID_REQUEST", "request size invalid")
			return false
		}
		normalized, err := canonical.JSON(raw)
		if err != nil {
			fail(w, 400, "INVALID_REQUEST", "JSON object required")
			return false
		}
		var keys map[string]json.RawMessage
		if json.Unmarshal(normalized, &keys) != nil || keys == nil || len(keys) != len(required) {
			fail(w, 400, "INVALID_REQUEST", "exact request fields required")
			return false
		}
		for _, key := range required {
			if _, ok := keys[key]; !ok {
				fail(w, 400, "INVALID_REQUEST", "required request field missing")
				return false
			}
		}
		decoder := json.NewDecoder(bytes.NewReader(normalized))
		decoder.DisallowUnknownFields()
		if decoder.Decode(out) != nil {
			fail(w, 400, "INVALID_REQUEST", "invalid request fields")
			return false
		}
		return true
	}
	limit := func(w http.ResponseWriter, r *http.Request, fallback, max int) (int, bool) {
		s := r.URL.Query().Get("limit")
		if s == "" {
			return fallback, true
		}
		n, err := strconv.Atoi(s)
		if err != nil || n < 1 || n > max {
			fail(w, 400, "INVALID_REQUEST", "limit outside range")
			return 0, false
		}
		return n, true
	}
	cursor := func(r *http.Request) string {
		s := r.URL.Query().Get("cursor")
		if s == "" {
			return "0"
		}
		return s
	}
	mux.HandleFunc("GET /harness/v1/capabilities", func(w http.ResponseWriter, r *http.Request) {
		t, ok := token(w, r)
		if !ok || !query(w, r) {
			return
		}
		v, e := port.Capabilities(r.Context(), t)
		reply(w, v, e, 200)
	})
	mux.HandleFunc("POST /harness/v1/tasks", func(w http.ResponseWriter, r *http.Request) {
		t, ok := token(w, r)
		if !ok || !query(w, r) {
			return
		}
		var input domain.HarnessSubmit
		if !readBody(w, r, &input, "request_id", "project_id", "workspace_ref", "harness_id", "scope", "prompt") {
			return
		}
		v, e := port.Submit(r.Context(), t, input)
		reply(w, v, e, 202)
	})
	mux.HandleFunc("GET /harness/v1/tasks", func(w http.ResponseWriter, r *http.Request) {
		t, ok := token(w, r)
		if !ok || !query(w, r, "project_id", "cursor", "limit", "request_id") {
			return
		}
		n, ok := limit(w, r, 20, 100)
		if !ok {
			return
		}
		v, e := port.List(r.Context(), t, domain.HarnessList{ProjectID: r.URL.Query().Get("project_id"), Cursor: cursor(r), RequestID: r.URL.Query().Get("request_id"), Limit: n})
		reply(w, v, e, 200)
	})
	mux.HandleFunc("GET /harness/v1/tasks/{task_id}", func(w http.ResponseWriter, r *http.Request) {
		t, ok := token(w, r)
		if !ok || !query(w, r, "project_id") {
			return
		}
		v, e := port.Get(r.Context(), t, r.URL.Query().Get("project_id"), r.PathValue("task_id"))
		reply(w, v, e, 200)
	})
	mux.HandleFunc("GET /harness/v1/tasks/{task_id}/events", func(w http.ResponseWriter, r *http.Request) {
		t, ok := token(w, r)
		if !ok || !query(w, r, "project_id", "cursor", "limit") {
			return
		}
		n, ok := limit(w, r, 100, 500)
		if !ok {
			return
		}
		v, e := port.Events(r.Context(), t, domain.HarnessEvents{ProjectID: r.URL.Query().Get("project_id"), TaskID: r.PathValue("task_id"), Cursor: cursor(r), Limit: n})
		reply(w, v, e, 200)
	})
	mux.HandleFunc("POST /harness/v1/tasks/{task_id}/cancel", func(w http.ResponseWriter, r *http.Request) {
		t, ok := token(w, r)
		if !ok || !query(w, r, "project_id") {
			return
		}
		var input domain.HarnessCancel
		if !readBody(w, r, &input, "request_id", "expected_task_revision", "expected_run_id", "expected_epoch") {
			return
		}
		v, e := port.Cancel(r.Context(), t, r.URL.Query().Get("project_id"), r.PathValue("task_id"), input)
		reply(w, v, e, 200)
	})
}
