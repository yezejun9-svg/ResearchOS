//go:build windows

package main

// A constructed, user-only journal is deliberately used here. The 201st
// message crosses the published snapshot bound through the production
// session.send transaction; no model or tool is started by this fixture.
import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

func serveTranscriptFixture(ctx context.Context, db *sql.DB, h *host.Host, client *http.Client,
	base, token, project, session, workspace, root, dataDir, addr string) error {
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		return err
	}
	initial, err := command(ctx, client, base, token, "session.get", "transcript-before-seed", &project, &session, nil, nil, domain.Object{})
	if err != nil {
		return err
	}
	revision, err := domain.Num(initial, "revision")
	if err != nil {
		return err
	}
	sequence, err := domain.Num(initial, "event_sequence")
	if err != nil {
		return err
	}
	writer, ok := initial["writer"].(map[string]any)
	if !ok {
		return errors.New("transcript fixture requires the actual session writer")
	}
	epoch, err := domain.Num(writer, "epoch")
	if err != nil {
		return err
	}
	buildID := domain.Str(initial, "core_build_id")
	if buildID == "" {
		return errors.New("transcript fixture session omitted core build")
	}
	var beforeTasks, beforeRuns, beforeEffects int
	for _, item := range []struct {
		query string
		to    *int
	}{
		{`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'`, &beforeTasks},
		{`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'`, &beforeRuns},
		{`SELECT count(*) FROM resource_effects WHERE project=?`, &beforeEffects},
	} {
		if err := db.QueryRowContext(ctx, item.query, project).Scan(item.to); err != nil {
			return err
		}
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	seedIDs := make([]string, 200)
	for index := range seedIDs {
		messageID := domain.ID()
		seedIDs[index] = messageID
		text := fmt.Sprintf("u%03d", index+1)
		for _, part := range []domain.Object{
			{"phase": "START", "text": "", "content_offset_utf8_bytes": 0},
			{"phase": "DELTA", "text": text, "content_offset_utf8_bytes": 0},
			{"phase": "END", "text": "", "content_offset_utf8_bytes": len([]byte(text))},
		} {
			part["message_id"], part["role"], part["part_index"] = messageID, "USER", 0
			sequence++
			eventID, eventSession, eventBuild, protocol, kind, eventSequence := domain.ID(), session, buildID, domain.ProtocolV2, "MESSAGE", sequence
			event := &domain.SessionEvent{EventID: &eventID, SessionID: &eventSession, CoreBuildID: &eventBuild,
				ProtocolVersion: &protocol, Kind: &kind, Sequence: &eventSequence, Payload: domain.Bytes(part)}
			if err := domain.AppendSessionEvent(ctx, tx, doc, project, event, epoch, revision); err != nil {
				tx.Rollback()
				return fmt.Errorf("seed message %d event %d: %w", index+1, sequence, err)
			}
			revision++
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	beforeSend, err := command(ctx, client, base, token, "session.get", "transcript-after-200", &project, &session, nil, nil, domain.Object{})
	if err != nil {
		return err
	}
	observedSequence, err := domain.Num(beforeSend, "event_sequence")
	if err != nil {
		return err
	}
	if len(domain.Arr(beforeSend, "messages")) != 200 || beforeSend["has_earlier_messages"] != false || observedSequence != sequence {
		return errors.New("exactly 200 seeded messages were not durably replayed")
	}
	// 14,000 CJK code points are about 42 KiB, above Mu's 32 KiB bounded
	// history and below session.send's 16,384-rune input limit.
	finalText := "transcript-final:" + strings.Repeat("续", 14000)
	if len([]byte(finalText)) <= 32768 || len([]rune(finalText)) > 16384 {
		return errors.New("fixture final message missed intended byte/rune bounds")
	}
	client.Timeout = 60 * time.Second
	sent, err := command(ctx, client, base, token, "session.send", "transcript-201st-real-send", &project, &session, revision, epoch,
		domain.Object{"text": finalText, "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	if err != nil {
		return err
	}
	finalID := domain.Str(sent, "message_id")
	if finalID == "" {
		return errors.New("session.send omitted the persisted message id")
	}
	snapshot, err := command(ctx, client, base, token, "session.get", "transcript-final-snapshot", &project, &session, nil, nil, domain.Object{})
	if err != nil {
		return err
	}
	visible := domain.Arr(snapshot, "messages")
	if len(visible) != 200 || snapshot["has_earlier_messages"] != true {
		return errors.New("201-message snapshot did not retain the latest 200 with earlier-history flag")
	}
	firstVisible, ok := visible[0].(map[string]any)
	if !ok || firstVisible["message_id"] != seedIDs[1] {
		return errors.New("snapshot oldest visible message was not seed 2")
	}
	lastVisible, ok := visible[len(visible)-1].(map[string]any)
	if !ok || lastVisible["message_id"] != finalID || messageText(lastVisible) != finalText {
		return errors.New("snapshot newest visible message did not preserve real 201st text")
	}
	ref, ok := snapshot["transcript_artifact_ref"].(map[string]any)
	if !ok || domain.Str(ref, "id") == "" || domain.Str(ref, "content_hash") == "" {
		return errors.New("201-message snapshot omitted sealed full transcript ArtifactRef")
	}
	contentURL := base + "/v1/projects/" + project + "/artifacts/" + domain.Str(ref, "id") + "/content"
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, contentURL, nil)
	if err != nil {
		return err
	}
	request.Header.Set("Authorization", "Bearer "+token)
	response, err := client.Do(request)
	if err != nil {
		return err
	}
	full, readErr := io.ReadAll(io.LimitReader(response.Body, 5<<20))
	response.Body.Close()
	if response.StatusCode != 200 || readErr != nil || domain.Digest(full) != ref["content_hash"] {
		return fmt.Errorf("sealed transcript content/hash mismatch: HTTP %d read=%v", response.StatusCode, readErr)
	}
	var body domain.Object
	if err := json.Unmarshal(full, &body); err != nil {
		return err
	}
	all := domain.Arr(body, "messages")
	if body["schema"] != "researchos.session-transcript.v1" || body["project_id"] != project || body["session_id"] != session ||
		len(all) != 201 || domain.Str(all[0].(map[string]any), "message_id") != seedIDs[0] ||
		domain.Str(all[200].(map[string]any), "message_id") != finalID || messageText(all[200].(map[string]any)) != finalText {
		return errors.New("sealed transcript did not preserve all 201 original messages")
	}
	var afterTasks, afterRuns, afterEffects int
	for _, item := range []struct {
		query string
		to    *int
	}{
		{`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'`, &afterTasks},
		{`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'`, &afterRuns},
		{`SELECT count(*) FROM resource_effects WHERE project=?`, &afterEffects},
	} {
		if err := db.QueryRowContext(ctx, item.query, project).Scan(item.to); err != nil {
			return err
		}
	}
	if afterTasks != beforeTasks+1 || afterRuns != beforeRuns || afterEffects != beforeEffects {
		return fmt.Errorf("fixture made unexpected Task/Run/effects: %d→%d / %d→%d / %d→%d", beforeTasks, afterTasks, beforeRuns, afterRuns, beforeEffects, afterEffects)
	}
	var taskID string
	if err := db.QueryRowContext(ctx, `SELECT task_id FROM client_sessions WHERE project_id=? AND id=?`, project, session).Scan(&taskID); err != nil {
		return err
	}
	discovery := filepath.Join(dataDir, "discovery.json")
	if err := writeDiscovery(discovery, addr, dataDir, h.InstanceID()); err != nil {
		return err
	}
	ready := domain.Object{"ready": true, "fixture": "W13-03 sealed transcript FIXTURE", "base_url": base,
		"discovery_file": discovery, "project_id": project, "session_id": session, "workspace_ref": workspace,
		"workspace_root": root, "task_id": taskID, "goal_id": snapshot["goal_id"], "model_config_ref": fixtureModelRef,
		"seed_count": 200, "visible_count": len(visible), "full_count": len(all), "first_message_id": seedIDs[0],
		"first_visible_message_id": seedIDs[1], "last_message_id": finalID, "last_text_hash": domain.Digest([]byte(finalText)),
		"last_text_bytes": len([]byte(finalText)), "transcript_artifact_ref": ref,
		"transcript_through_sequence": body["through_sequence"], "snapshot_event_sequence": snapshot["event_sequence"],
		"before_task_count": beforeTasks, "after_task_count": afterTasks, "before_run_count": beforeRuns,
		"after_run_count": afterRuns, "before_effect_count": beforeEffects, "after_effect_count": afterEffects,
		"provider_calls": 0, "measurement_mode": "FIXTURE", "source": "constructed typed USER journal, then one real session.send"}
	if err := json.NewEncoder(os.Stdout).Encode(ready); err != nil {
		return err
	}
	wait, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	<-wait.Done()
	return nil
}

func messageText(value map[string]any) string {
	parts := domain.Arr(value, "parts")
	var text string
	for _, part := range parts {
		if object, ok := part.(map[string]any); ok {
			text += domain.Str(object, "text")
		}
	}
	return text
}
