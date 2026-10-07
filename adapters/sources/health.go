package sources

import (
	"context"
	"strings"
	"time"
)

// ProviderResult preserves the transport envelope separately from its conclusion.
type ProviderResult struct {
	ExitCode     int      `json:"exit_code"`
	Status       string   `json:"status"`
	DetailErrors []string `json:"detail_errors"`
}

type SourceHealth struct {
	ObservationMarker string          `json:"observation_marker"`
	Status            string          `json:"status"`
	Reason            string          `json:"reason"`
	RequestedFrom     time.Time       `json:"requested_from"`
	RequestedTo       time.Time       `json:"requested_to"`
	ActualFrom        *time.Time      `json:"actual_from"`
	ActualTo          *time.Time      `json:"actual_to"`
	ObservedFrom      *time.Time      `json:"observed_from"`
	ObservedTo        *time.Time      `json:"observed_to"`
	AccessScope       string          `json:"access_scope"`
	FullReadCount     int             `json:"full_read_count"`
	IndexCount        int             `json:"index_count"`
	HTTPStatus        int             `json:"http_status"`
	RetryAfter        *time.Time      `json:"retry_after"`
	Provider          *ProviderResult `json:"provider_result"`
	Exhaustive        bool            `json:"exhaustive"`
}

// NormalizeSourceHealth is the sole production precedence rule. Neither a zero
// process exit nor an 'ok' envelope can hide a detail failure.
func NormalizeSourceHealth(p *Page, err error) SourceHealth {
	reason := p.Failure
	if p.ProviderResult != nil {
		for _, detail := range p.ProviderResult.DetailErrors {
			if strings.TrimSpace(detail) != "" {
				reason = detail
				break
			}
		}
		if reason == "" && (p.ProviderResult.ExitCode != 0 || p.ProviderResult.Status != "ok") {
			reason = "PROVIDER_RESULT_INVALID"
		}
	}
	if reason == "" && err != nil {
		reason = err.Error()
	}
	if reason == "" && p.HTTPStatus >= 400 {
		reason = "HTTP_ERROR"
	}
	if p.HTTPStatus == 429 {
		reason = "RATE_LIMITED"
	}
	if p.HTTPStatus == 401 {
		reason = "AUTH_REVOKED"
	}
	status := "PARTIAL"
	if reason == "NOT_CONFIGURED" {
		status = "NOT_CONFIGURED"
	} else if reason == "RATE_LIMITED" {
		status = "RATE_LIMITED"
	} else if reason == "AUTH_REVOKED" || reason == "UNAVAILABLE" || reason == "ORIGIN_DENIED" {
		status = "UNAVAILABLE"
	}
	if reason != "" {
		p.Complete = false
	}
	if p.VisibleEmpty || p.AccessScope == "VISIBLE_PUBLIC_POSTS" {
		p.Complete = false
		p.NextCursor = ""
		p.ObservationMarker = ""
		for _, item := range p.Items {
			if item.ReadLevel != "INDEX" && len(item.Body) > 0 {
				p.ObservationMarker = "observed_tail:" + item.UpstreamID
			}
		}
	}
	reads, indexes := 0, 0
	for _, item := range p.Items {
		if item.ReadLevel == "INDEX" {
			indexes++
		} else if len(item.Body) > 0 {
			reads++
		}
	}
	if indexes > 0 {
		p.Complete = false
		if reason == "" {
			reason = "INDEX_ONLY"
		}
	}
	if p.Complete && len(p.RawResponse) > 0 && p.RawMediaType != "" && !p.FetchedAt.IsZero() && len(p.RequestURLs) > 0 && len(p.FinalURLs) > 0 {
		status = "COMPLETE"
	} else if p.Complete {
		p.Complete = false
		reason = "MISSING_RAW_PROOF"
	}
	p.Failure = reason
	if p.AccessScope == "" {
		p.AccessScope = "BOUNDED_PROVIDER_QUERY"
	}
	if p.ActualFrom == nil {
		t := p.RequestedFrom
		p.ActualFrom = &t
	}
	if p.ActualTo == nil {
		t := p.RequestedTo
		p.ActualTo = &t
	}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	return SourceHealth{p.ObservationMarker, status, reason, p.RequestedFrom, p.RequestedTo, p.ActualFrom, p.ActualTo, p.ObservedFrom, p.ObservedTo, p.AccessScope, reads, indexes, p.HTTPStatus, p.RetryAfter, p.ProviderResult, p.Complete}
}

// Unconfigured performs no provider/browser operation but still enters the
// same authenticated durable health path as a failed provider read.
type Unconfigured struct{}

func (Unconfigured) Fetch(_ context.Context, q Query) (Page, error) {
	return Page{RequestedFrom: q.From, RequestedTo: q.To, FetchedAt: time.Now().UTC(), Failure: "NOT_CONFIGURED", AccessScope: "NONE"}, nil
}
