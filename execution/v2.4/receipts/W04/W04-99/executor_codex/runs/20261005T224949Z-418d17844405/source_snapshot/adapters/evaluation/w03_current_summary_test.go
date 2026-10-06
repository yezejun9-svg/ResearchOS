package evaluation

import "testing"

func TestW03SummaryPreservesReportVersion(t *testing.T) {
	m, rows, _ := fixture(t)
	exit := 0
	raw := Bytes(rows)
	report, err := Normalize(m, m, raw, Digest(raw), &exit, 1)
	if err != nil {
		t.Fatal(err)
	}
	if report["schema_version"] != "2.0.0" {
		t.Fatal("legacy normalization changed")
	}
	for _, version := range []any{"2.0.0", "2.4.0", "unknown", nil} {
		report["schema_version"] = version
		summary := Summary(report, Object{"entity_type": "Artifact", "id": "report", "revision": 1, "content_hash": Digest(raw)})
		if summary["schema_version"] != version {
			t.Fatalf("summary changed %v into %v", version, summary["schema_version"])
		}
		for _, field := range []string{"dataset_hash", "candidate_hash", "baseline_hash", "rubric_hash", "counts"} {
			if string(Bytes(summary[field])) != string(Bytes(report[field])) {
				t.Fatalf("summary changed version-bound field %s", field)
			}
		}
		if _, present := summary["results"]; present {
			t.Fatal("summary leaked individual results")
		}
	}
}
