//go:build windows

package domain

import (
	"fmt"
	"strconv"
	"strings"
)

func controlVersionKey(row Object) string {
	return Hash([]any{row["project"], row["kind"], row["id"], row["revision"]})
}
func controlEntityKey(row Object) string { return Hash([]any{row["project"], row["kind"], row["id"]}) }

// Version and event rows are part of the checked delta, not ignored metadata.
func controlValidateVersionEvents(n *controlCurrentNames, after upgradeData) error {
	old := map[string]Object{}
	versions := map[string]Object{}
	objects := map[string]Object{}
	for _, r := range n.Rows["domain_objects"] {
		old[controlEntityKey(r)] = r
	}
	for _, r := range after["domain_versions"] {
		versions[controlVersionKey(r)] = r
	}
	for _, r := range after["domain_objects"] {
		objects[controlEntityKey(r)] = r
	}
	for key, r := range objects {
		base := old[key]
		if Hash(base) == Hash(r) {
			continue
		}
		head := versions[controlVersionKey(r)]
		if head == nil || head["body"] != r["body"] || head["content_hash"] != r["content_hash"] {
			return fmt.Errorf("CONTROL_CURRENT_VERSION_HEAD")
		}
		start := int64(0)
		if base != nil {
			start, _ = Num(base, "revision")
		}
		end, _ := Num(r, "revision")
		if end <= start || end-start > 1000 {
			return fmt.Errorf("CONTROL_CURRENT_REVISION_RANGE")
		}
		for revision := start + 1; revision <= end; revision++ {
			key := Hash([]any{r["project"], r["kind"], r["id"], revision})
			v := versions[key]
			if v == nil {
				return fmt.Errorf("CONTROL_CURRENT_VERSION_GAP")
			}
			body, e := controlBody(v)
			if e != nil {
				return e
			}
			var expected any
			if receipt, exists := body["receipt_hash"]; exists {
				if receipt != Receipt(body) {
					return fmt.Errorf("CONTROL_CURRENT_RECEIPT_HASH")
				}
				expected = receipt
			} else if r["kind"] == "Artifact" {
				expected = body["content_hash"]
			}
			if v["content_hash"] != expected {
				return fmt.Errorf("CONTROL_CURRENT_VERSION_CONTENT_HASH")
			}
		}
	}
	stateKey := Hash([]any{n.Project, "ProjectState", n.State})
	base := old[stateKey]
	head := objects[stateKey]
	if base == nil || head == nil {
		return fmt.Errorf("CONTROL_CURRENT_STATE_ABSENT")
	}
	bb, e := controlBody(base)
	if e != nil {
		return e
	}
	hb, e := controlBody(head)
	if e != nil {
		return e
	}
	baseSeq, _ := Num(bb, "event_sequence")
	baseRev, _ := Num(bb, "revision")
	headSeq, _ := Num(hb, "event_sequence")
	headRev, _ := Num(hb, "revision")
	newEvents := map[int64]Object{}
	eventIDs := map[string]Object{}
	for key, r := range objects {
		if r["project"] != n.Project || r["kind"] != "EventEnvelope" || old[key] != nil {
			continue
		}
		body, e := controlBody(r)
		if e != nil {
			return e
		}
		seq, _ := Num(body, "sequence")
		if newEvents[seq] != nil {
			return fmt.Errorf("CONTROL_CURRENT_EVENT_DUPLICATE")
		}
		newEvents[seq] = body
		eventIDs[Str(body, "id")] = body
	}
	if headSeq-baseSeq != int64(len(newEvents)) || headRev-baseRev != int64(len(newEvents)) {
		return fmt.Errorf("CONTROL_CURRENT_STATE_EVENT_COUNT")
	}
	for seq := baseSeq + 1; seq <= headSeq; seq++ {
		if newEvents[seq] == nil {
			return fmt.Errorf("CONTROL_CURRENT_EVENT_GAP")
		}
	}
	snapshots := map[string]Object{}
	for _, row := range after["event_state_snapshots"] {
		snapshots[Str(row, "event_id")] = row
	}
	for id, event := range eventIDs {
		snapshot := snapshots[id]
		if snapshot == nil {
			return fmt.Errorf("CONTROL_CURRENT_EVENT_SNAPSHOT_ABSENT")
		}
		seq, _ := Num(event, "sequence")
		revision := baseRev + seq - baseSeq
		version := versions[Hash([]any{n.Project, "ProjectState", n.State, revision})]
		if version == nil || snapshot["body"] != version["body"] || Hash(snapshot["revision"]) != Hash(revision) {
			return fmt.Errorf("CONTROL_CURRENT_EVENT_SNAPSHOT_BINDING")
		}
		ref, _ := event["aggregate_ref"].(map[string]any)
		version = versions[Hash([]any{n.Project, ref["entity_type"], ref["id"], ref["revision"]})]
		if version == nil || version["content_hash"] != ref["content_hash"] {
			return fmt.Errorf("CONTROL_CURRENT_EVENT_AGGREGATE_BINDING")
		}
	}
	return nil
}

func controlReferenceRowBound(row Object, versions map[string]Object, baseline map[string]Object) bool {
	version := versions[controlVersionKey(row)]
	if version == nil {
		return false
	}
	if old := baseline[controlEntityKey(row)]; old != nil {
		revision, _ := Num(row, "revision")
		prior, _ := Num(old, "revision")
		if revision <= prior {
			return false
		}
	}
	body, err := controlBody(version)
	if err != nil {
		return false
	}
	var value any = body
	parts := strings.Split(strings.TrimPrefix(Str(row, "field"), "/"), "/")
	for _, part := range parts {
		switch v := value.(type) {
		case map[string]any:
			value = v[part]
		case []any:
			i, e := strconv.Atoi(part)
			if e != nil || i < 0 || i >= len(v) {
				return false
			}
			value = v[i]
		default:
			return false
		}
	}
	if ref, ok := value.(map[string]any); ok {
		return ref["entity_type"] == row["target_kind"] && ref["id"] == row["target_id"] && Hash(ref["revision"]) == Hash(row["target_revision"]) && row["target_project"] == row["project"]
	}
	field := parts[len(parts)-1]
	target := relationKind(Str(row, "kind"), field)
	if field == "supersedes_id" || field == "parent_policy_id" {
		target = Str(row, "kind")
	}
	if target != row["target_kind"] {
		return false
	}
	values := []any{value}
	if array, ok := value.([]any); ok {
		values = array
	}
	for _, id := range values {
		if id == row["target_id"] {
			return row["target_project"] == row["project"] || row["target_project"] == "" && (target == "BudgetPolicy" || target == "RunPolicy")
		}
	}
	return false
}
