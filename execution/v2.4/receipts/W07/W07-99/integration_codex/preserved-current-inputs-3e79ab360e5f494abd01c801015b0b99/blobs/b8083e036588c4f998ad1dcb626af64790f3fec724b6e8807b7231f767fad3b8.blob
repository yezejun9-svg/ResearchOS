package sources

import (
	"testing"
	"time"
)

func TestW07HealthDetailPrecedesSuccessfulEnvelope(t *testing.T) {
	p := Page{Complete: true, ProviderResult: &ProviderResult{ExitCode: 0, Status: "ok", DetailErrors: []string{"page_timeout"}}}
	h := NormalizeSourceHealth(&p, nil)
	if h.Status != "PARTIAL" || h.Reason != "page_timeout" || p.Complete {
		t.Fatalf("detail failure hidden: %+v", h)
	}
}
func TestW07HealthEmptyProofAndIndexReadLevel(t *testing.T) {
	now := time.Now().UTC()
	base := Page{Complete: true, RequestedFrom: now.Add(-time.Hour), RequestedTo: now, FetchedAt: now, RawResponse: []byte("[]"), RawMediaType: "application/json", RequestURLs: []string{"https://api.github.com"}, FinalURLs: []string{"https://api.github.com"}}
	p := base
	h := NormalizeSourceHealth(&p, nil)
	if h.Status != "COMPLETE" || h.FullReadCount != 0 {
		t.Fatal(h)
	}
	p = base
	p.VisibleEmpty = true
	h = NormalizeSourceHealth(&p, nil)
	if h.Status != "PARTIAL" || h.Exhaustive {
		t.Fatal(h)
	}
	p = base
	p.Items = []Item{{ReadLevel: "INDEX", Body: []byte("search snippet")}}
	h = NormalizeSourceHealth(&p, nil)
	if h.Status != "PARTIAL" || h.FullReadCount != 0 || h.IndexCount != 1 {
		t.Fatal(h)
	}
	p = base
	p.RawResponse = nil
	h = NormalizeSourceHealth(&p, nil)
	if h.Status == "COMPLETE" {
		t.Fatal(h)
	}
}
func TestW07HealthUnavailableClassification(t *testing.T) {
	for _, tc := range []struct {
		failure        string
		http           int
		status, reason string
	}{{"NOT_CONFIGURED", 0, "NOT_CONFIGURED", "NOT_CONFIGURED"}, {"", 429, "RATE_LIMITED", "RATE_LIMITED"}, {"", 401, "UNAVAILABLE", "AUTH_REVOKED"}, {"TIMEOUT_OR_NETWORK", 0, "PARTIAL", "TIMEOUT_OR_NETWORK"}} {
		p := Page{Failure: tc.failure, HTTPStatus: tc.http}
		h := NormalizeSourceHealth(&p, nil)
		if h.Status != tc.status || h.Reason != tc.reason {
			t.Fatalf("%+v: %+v", tc, h)
		}
	}
}
