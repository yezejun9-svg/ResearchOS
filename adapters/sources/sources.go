package sources

import (
	"context"
	"errors"
	"time"
)

// Query is a bounded, source-specific read. The caller owns scheduling and
// persistence; an adapter never advances the authoritative SourceCursor.
type Query struct {
	SourceID string
	Text     string
	From     time.Time
	To       time.Time
	Cursor   string
	Limit    int
}

type Item struct {
	SourceID         string
	CanonicalURL     string
	UpstreamID       string
	Author           string
	PublishedAt      time.Time
	ModifiedAt       *time.Time
	UpstreamRevision string
	Body             []byte
	MediaType        string
	Locator          string
}

type Page struct {
	Items         []Item
	NextCursor    string
	RequestedFrom time.Time
	RequestedTo   time.Time
	ObservedFrom  *time.Time
	ObservedTo    *time.Time
	Complete      bool
	Failure       string
	RetryAfter    *time.Time
	HTTPStatus    int
}

type Adapter interface {
	Fetch(context.Context, Query) (Page, error)
}

var ErrInvalidQuery = errors.New("invalid bounded source query")

func bounded(q Query) bool {
	return q.SourceID != "" && !q.From.IsZero() && !q.To.IsZero() && q.From.Before(q.To) && q.Limit > 0 && q.Limit <= 100
}

func observed(items []Item) (*time.Time, *time.Time) {
	var lo, hi *time.Time
	for _, item := range items {
		t := item.PublishedAt
		if lo == nil || t.Before(*lo) {
			x := t
			lo = &x
		}
		if hi == nil || t.After(*hi) {
			x := t
			hi = &x
		}
	}
	return lo, hi
}
