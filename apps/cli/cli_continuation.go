package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const continuationReadLimit = 2 << 20

// This projection only reads public, principal-scoped objects. It does not
// acquire a writer, dispatch work, or interpret a pending task as executable.
func cliReadContinuation(c *v2Context, snapshot map[string]any) (map[string]any, string, int) {
	return cliReadContinuationContext(context.Background(), c, snapshot)
}

func cliReadContinuationContext(parent context.Context, c *v2Context, snapshot map[string]any) (map[string]any, string, int) {
	out, reason, code, _ := cliReadContinuationWithCause(parent, c, snapshot)
	return out, reason, code
}

func cliReadContinuationWithCause(parent context.Context, c *v2Context, snapshot map[string]any) (map[string]any, string, int, bool) {
	cancelledIO := false
	goalID := continuationString(snapshot, "goal_id")
	if goalID == "" {
		return nil, "", exitCompleted, false
	}
	out := map[string]any{"status": "UNAVAILABLE", "project_id": c.projectID,
		"session_id": c.sessionID, "goal_id": goalID, "event_watermark": snapshot["event_sequence"],
		"goal": nil, "unfinished_tasks": []any{}, "next_step": nil, "selection": "NONE"}
	fail := func(reason string) (map[string]any, string, int, bool) {
		out["reason"] = reason
		return out, reason, exitFailed, cancelledIO
	}
	if snapshot["project_id"] != c.projectID || snapshot["session_id"] != c.sessionID ||
		!continuationID(c.projectID) || !continuationID(goalID) {
		return fail("CONTINUATION_SCOPE_MISMATCH")
	}
	budget, cancel := context.WithTimeout(parent, 8*time.Second)
	defer cancel()
	remaining := int64(continuationReadLimit)
	client := &http.Client{CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}
	prefix := strings.TrimRight(c.baseURL, "/") + "/v1/projects/" + url.PathEscape(c.projectID)
	get := func(path string) (map[string]any, string) {
		if remaining <= 0 {
			return nil, "CONTINUATION_RESPONSE_TOO_LARGE"
		}
		req, err := http.NewRequestWithContext(budget, http.MethodGet, prefix+path, nil)
		if err != nil {
			return nil, "CONTINUATION_INVALID_URL"
		}
		req.Header.Set("Authorization", "Bearer "+c.credential)
		c.requestLog = append(c.requestLog, "GET "+req.URL.RequestURI())
		resp, err := client.Do(req)
		if err != nil {
			cancelledIO = errors.Is(err, context.Canceled)
			return nil, "CONTINUATION_READ_FAILED"
		}
		defer resp.Body.Close()
		body, err := io.ReadAll(io.LimitReader(resp.Body, remaining+1))
		if int64(len(body)) > remaining {
			return nil, "CONTINUATION_RESPONSE_TOO_LARGE"
		}
		remaining -= int64(len(body))
		if err != nil {
			// Non-200 headers already identify a terminal HTTP failure, even
			// when cancellation happens while reading its error body.
			cancelledIO = resp.StatusCode == http.StatusOK && errors.Is(err, context.Canceled)
			return nil, "CONTINUATION_READ_FAILED"
		}
		if resp.StatusCode != http.StatusOK {
			return nil, fmt.Sprintf("CONTINUATION_HTTP_%d", resp.StatusCode)
		}
		var object map[string]any
		if json.Unmarshal(body, &object) != nil || object == nil {
			return nil, "CONTINUATION_INVALID_RESPONSE"
		}
		return object, ""
	}
	goal, reason := get("/goals/" + url.PathEscape(goalID))
	if reason != "" {
		return fail(reason)
	}
	if goal["id"] != goalID || goal["project_id"] != c.projectID {
		return fail("CONTINUATION_SCOPE_MISMATCH")
	}
	ids, ok := goal["task_ids"].([]any)
	if !ok {
		return fail("CONTINUATION_INVALID_GOAL_TASKS")
	}
	wanted := map[string]bool{}
	for _, value := range ids {
		id, ok := value.(string)
		if !ok || !continuationID(id) || wanted[id] {
			return fail("CONTINUATION_INVALID_GOAL_TASKS")
		}
		wanted[id] = true
	}
	tasks := []map[string]any{}
	seen, cursors := map[string]bool{}, map[string]bool{}
	cursor := ""
	for page := 0; ; page++ {
		if page == 10 {
			return fail("CONTINUATION_PAGE_LIMIT")
		}
		path := "/tasks?limit=100"
		if cursor != "" {
			path += "&cursor=" + url.QueryEscape(cursor)
		}
		list, reason := get(path)
		if reason != "" {
			return fail(reason)
		}
		items, ok := list["items"].([]any)
		if !ok || len(items) > 100 {
			return fail("CONTINUATION_INVALID_TASK_PAGE")
		}
		for _, value := range items {
			task, ok := value.(map[string]any)
			id := continuationString(task, "id")
			if !ok || !continuationID(id) || task["project_id"] != c.projectID || seen[id] {
				return fail("CONTINUATION_SCOPE_MISMATCH")
			}
			seen[id] = true
			if (task["goal_id"] == goalID) != wanted[id] {
				return fail("CONTINUATION_INCOMPLETE_GOAL_TASKS")
			}
			if wanted[id] {
				tasks = append(tasks, task)
			}
		}
		value, exists := list["next_cursor"]
		if !exists {
			return fail("CONTINUATION_INVALID_TASK_PAGE")
		}
		if value == nil {
			break
		}
		cursor, ok = value.(string)
		if !ok || cursor == "" || cursors[cursor] {
			return fail("CONTINUATION_INVALID_TASK_PAGE")
		}
		cursors[cursor] = true
	}
	if len(tasks) != len(wanted) {
		return fail("CONTINUATION_INCOMPLETE_GOAL_TASKS")
	}
	unfinished, active, contextual := []any{}, []any{}, []any{}
	for _, task := range tasks {
		switch task["status"] {
		case "ACCEPTED", "CANCELLED":
			continue
		case "DRAFT", "READY", "RUNNING", "EXECUTION_REPORTED", "VERIFYING", "FAILED", "BLOCKED", "NEEDS_REVALIDATION", "DEFERRED_NO_PROGRESS", "PENDING":
		default:
			return fail("CONTINUATION_INVALID_TASK_STATUS")
		}
		for _, field := range []string{"active_run_id", "context_bundle_id"} {
			if task[field] != nil && !continuationID(continuationString(task, field)) {
				return fail("CONTINUATION_INVALID_TASK_REFERENCE")
			}
		}
		row := map[string]any{}
		for _, field := range []string{"id", "title", "status", "context_bundle_id", "active_run_id"} {
			row[field] = task[field]
		}
		unfinished = append(unfinished, row)
		next := func(source string) map[string]any {
			return map[string]any{"task_id": task["id"], "title": task["title"], "source": source}
		}
		if runID := continuationString(task, "active_run_id"); runID != "" {
			if !continuationID(runID) {
				return fail("CONTINUATION_INVALID_RUN")
			}
			run, reason := get("/runs/" + url.PathEscape(runID))
			if reason != "" {
				return fail(reason)
			}
			if run["id"] != runID || run["project_id"] != c.projectID || run["task_id"] != task["id"] {
				return fail("CONTINUATION_SCOPE_MISMATCH")
			}
			switch run["status"] {
			case "QUEUED", "STARTING", "RUNNING", "CANCEL_REQUESTED", "LOST", "RECONCILING":
				active = append(active, next("ACTIVE_RUN"))
				continue
			case "SETTLED", "FAILED", "CANCELLED":
				// Unaccepted tasks retain terminal Run references. Their saved
				// context remains useful but does not identify an active Run.
			default:
				return fail("CONTINUATION_INVALID_RUN_STATUS")
			}
		}
		if bundleID := continuationString(task, "context_bundle_id"); bundleID != "" {
			if !continuationID(bundleID) {
				return fail("CONTINUATION_INVALID_CONTEXT")
			}
			bundle, reason := get("/context-bundles/" + url.PathEscape(bundleID))
			if reason != "" {
				return fail(reason)
			}
			if bundle["id"] != bundleID || bundle["project_id"] != c.projectID || bundle["task_id"] != task["id"] {
				return fail("CONTINUATION_SCOPE_MISMATCH")
			}
			found := false
			for _, line := range strings.Split(continuationString(bundle, "summary"), "\n") {
				if !strings.HasPrefix(line, "Continuation: ") {
					continue
				}
				var saved map[string]any
				if found || json.Unmarshal([]byte(strings.TrimPrefix(line, "Continuation: ")), &saved) != nil ||
					saved["goal_id"] != goalID || saved["next_task_id"] != task["id"] {
					return fail("CONTINUATION_INVALID_CONTEXT")
				}
				found = true
			}
			if found {
				contextual = append(contextual, next("CONTEXT_BUNDLE"))
			}
		}
	}
	out["status"], out["unfinished_tasks"] = "AVAILABLE", unfinished
	out["goal"] = map[string]any{"id": goalID, "title": goal["title"], "status": goal["status"], "original_intent": goal["original_intent"]}
	candidates := active
	if len(candidates) == 0 {
		candidates = contextual
	}
	if len(candidates) == 0 && len(unfinished) == 1 {
		task := unfinished[0].(map[string]any)
		candidates = []any{map[string]any{"task_id": task["id"], "title": task["title"], "source": "ONLY_UNFINISHED_TASK"}}
	}
	if len(candidates) == 1 {
		out["selection"], out["next_step"] = "UNIQUE", candidates[0]
	} else if len(unfinished) > 1 {
		out["selection"] = "AMBIGUOUS"
	}
	return out, "", exitCompleted, false
}

func continuationString(object map[string]any, key string) string {
	value, _ := object[key].(string)
	return value
}

func continuationID(id string) bool {
	return id != "." && id != ".." && commandIDPattern.MatchString(id)
}
