package domain

import (
	"context"
	"testing"
	"time"
)

func TestW06ArtifactReuse(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	first := o.claim(o.task("same-bytes-first", Empty(), Empty()))
	content := []byte(`{"result":"verified"}`)
	canonical := o.report(first, content)
	req := o.acceptance(first, canonical)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(first.task), req)
	second := o.claim(o.task("same-bytes-second", Empty(), Empty()))
	executorToken := f.token
	beforeRead, _, _ := f.request("GET", f.path("/artifacts/"+Str(canonical, "id")), "", "", nil)
	observation := second.observation("SETTLED", true)
	observation["artifacts"] = []any{Object{"path": "result.json", "content_hash": canonical["content_hash"], "byte_size": canonical["byte_size"]}}
	second.observe(observation)
	forged, reply, _ := f.request("POST", f.path("/runs/"+Str(second.run, "id")+"/report"), ID(), testTag(second.run), second.report([]any{canonical["id"]}, 0))
	orchestrationAssert(t, "W06-USES-NO-UPLOAD-NO-CLAIM", []any{404, 422}, []any{beforeRead, forged}, reply)
	badCheckpoint := second.heartbeat()
	badCheckpoint["checkpoint_artifact_id"] = canonical["id"]
	status, reply, _ := f.request("POST", f.path("/runs/"+Str(second.run, "id")+"/heartbeat"), ID(), testTag(second.run), badCheckpoint)
	orchestrationAssert(t, "W06-USES-CHECKPOINT-FENCE", 422, status, reply)
	f.token = o.owner
	tag := f.stateTag()
	f.token = executorToken
	upload := f.expect(201, "POST", f.path("/content"), ID(), "", content)
	seal := Object{"run_id": second.run["id"], "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(content), "input_refs": Empty(), "source_refs": Empty(), "produced_by": second.executor, "access_class": "PROJECT"}
	elevated, _ := Decode(Bytes(seal))
	elevated["measurement_mode"] = "LIVE"
	status, reply, _ = f.request("POST", f.path("/artifacts"), ID(), tag, elevated)
	orchestrationAssert(t, "W06-USES-NO-EVIDENCE-UPGRADE", 409, status, reply)
	staleUpload, _ := Decode(Bytes(seal))
	staleUpload["storage_key"] = canonical["storage_key"]
	status, reply, _ = f.request("POST", f.path("/artifacts"), ID(), tag, staleUpload)
	orchestrationAssert(t, "W06-USES-NO-BORROWED-UPLOAD", 403, status, reply)
	key := ID()
	reused := f.expect(201, "POST", f.path("/artifacts"), key, tag, seal)
	again := f.expect(201, "POST", f.path("/artifacts"), key, tag, seal)
	afterRead := f.read("artifacts", Str(reused, "id"))
	second.call("/report", second.report([]any{reused["id"]}, 0), 200)
	f.token = o.owner
	second.task = f.read("tasks", Str(second.task, "id"))
	request := o.acceptance(second, reused)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(second.task), request)
	var artifactCount, useCount int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.content_hash')=? AND json_extract(body,'$.kind')='REPORT'", f.project, canonical["content_hash"]).Scan(&artifactCount)
	f.db.QueryRow("SELECT count(*) FROM artifact_uses WHERE project=? AND artifact=?", f.project, canonical["id"]).Scan(&useCount)
	orchestrationAssert(t, "W06-USES-EXACT-REUSE", []any{true, true, true, true, 1, 2, "PASS"}, []any{reused["id"] == canonical["id"], again["id"] == canonical["id"], reused["run_id"] == first.run["id"], afterRead["produced_by"] == first.executor, artifactCount, useCount, receipt["verdict"]}, Object{"canonical": reused, "first_run": Ref(first.run, "Run"), "second_run": Ref(second.run, "Run"), "acceptance": receipt, "bytes_hash": Digest(content)})
	f.token, _ = f.s.IssueCredential(context.Background(), second.executor, time.Minute)
	if e := f.s.RevokePrincipal(context.Background(), second.executor); e != nil {
		t.Fatal(e)
	}
	status, reply, _ = f.request("GET", f.path("/artifacts/"+Str(canonical, "id")), "", "", nil)
	orchestrationAssert(t, "W06-USES-REVOKED-READ", 401, status, reply)
}
