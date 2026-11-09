package sources

import (
	"context"
	"errors"
	"net/http"
	"net/url"
	"strings"
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
	RequestURLs   []string
	FinalURLs     []string
	FetchedAt     time.Time
	NextCursor    string
	RequestedFrom time.Time
	RequestedTo   time.Time
	ObservedFrom  *time.Time
	ObservedTo    *time.Time
	Complete      bool
	VisibleEmpty  bool // provider UI explicitly rendered an empty result, not full-window coverage
	Failure       string
	RetryAfter    *time.Time
	HTTPStatus    int
	RawResponse   []byte
	RawMediaType  string
}

type Adapter interface {
	Fetch(context.Context, Query) (Page, error)
}

var ErrInvalidQuery = errors.New("invalid bounded source query")
var ErrSourceOrigin = errors.New("source request origin is not allowed")

func sourceAllowed(allowed []string, raw string) bool {
	o := sourceOrigin(raw)
	if o == "" {
		return false
	}
	for _, v := range allowed {
		if sourceOrigin(v) == o {
			return true
		}
	}
	return false
}

func sourceOrigin(raw string) string {
	u, e := url.Parse(raw)
	if e != nil || u.User != nil || u.Host == "" {
		return ""
	}
	if u.Scheme != "https" && !(u.Scheme == "http" && (u.Hostname() == "127.0.0.1" || u.Hostname() == "localhost" || u.Hostname() == "::1")) {
		return ""
	}
	return strings.ToLower(u.Scheme + "://" + u.Host)
}

func sourceClient(base *http.Client, allowed []string, trace func(string), initial ...string) (*http.Client, error) {
	approved := map[string]bool{}
	fixture := len(initial) > 0
	for _, v := range initial {
		if !strings.HasPrefix(sourceOrigin(v), "http://") {
			fixture = false
		}
	}
	for _, v := range allowed {
		o := sourceOrigin(v)
		if o == "" || (!fixture && strings.HasPrefix(o, "http://")) {
			return nil, ErrSourceOrigin
		}
		approved[o] = true
	}
	for _, v := range initial {
		if !approved[sourceOrigin(v)] {
			return nil, ErrSourceOrigin
		}
	}
	client := http.Client{Timeout: 30 * time.Second}
	if base != nil {
		client = *base
	}
	prior := client.CheckRedirect
	client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
		if !approved[sourceOrigin(req.URL.String())] {
			return ErrSourceOrigin
		}
		if len(via) >= 10 {
			return errors.New("too many source redirects")
		}
		if prior != nil {
			if e := prior(req, via); e != nil {
				return e
			}
		}
		if trace != nil {
			trace(req.URL.String())
		}
		return nil
	}
	return &client, nil
}

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
