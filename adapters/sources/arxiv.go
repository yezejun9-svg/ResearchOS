package sources

import (
	"bytes"
	"context"
	"encoding/xml"
	"errors"
	pdfapi "github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

var arxivID = regexp.MustCompile(`^[0-9]{4}\.[0-9]{4,5}v[1-9][0-9]*$`)

type Arxiv struct {
	Client         *http.Client
	APIURL         string
	PDFBaseURL     string
	AllowedOrigins []string
	MinInterval    time.Duration
	mu             sync.Mutex
	lastRequest    time.Time
}

type atomFeed struct {
	Entries []struct {
		ID        string `xml:"id"`
		Published string `xml:"published"`
		Updated   string `xml:"updated"`
		Authors   []struct {
			Name string `xml:"name"`
		} `xml:"author"`
	} `xml:"entry"`
	Total int `xml:"totalResults"`
}

// Fetch downloads the complete PDF bytes of an arXiv version. The Atom entry
// alone is metadata and never counts as a full-text snapshot.
func (a *Arxiv) Fetch(ctx context.Context, q Query) (Page, error) {
	p := Page{RequestedFrom: q.From, RequestedTo: q.To}
	if !bounded(q) || !strings.HasPrefix(q.Text, "id:") || !arxivID.MatchString(strings.TrimPrefix(q.Text, "id:")) {
		return p, ErrInvalidQuery
	}
	id := strings.TrimPrefix(q.Text, "id:")
	api := a.APIURL
	if api == "" {
		api = "https://export.arxiv.org/api/query"
	}
	u, e := url.Parse(api)
	if e != nil {
		return p, e
	}
	v := u.Query()
	v.Set("id_list", id)
	v.Set("start", "0")
	v.Set("max_results", "1")
	u.RawQuery = v.Encode()
	interval := a.MinInterval
	if interval == 0 {
		interval = 3 * time.Second
	}
	a.mu.Lock()
	if d := time.Until(a.lastRequest.Add(interval)); d > 0 {
		t := time.NewTimer(d)
		select {
		case <-ctx.Done():
			t.Stop()
			a.mu.Unlock()
			return p, ctx.Err()
		case <-t.C:
		}
	}
	a.lastRequest = time.Now()
	a.mu.Unlock()
	allowed := a.AllowedOrigins
	if len(allowed) == 0 {
		allowed = []string{"https://export.arxiv.org", "https://arxiv.org"}
	}
	pdfBase := a.PDFBaseURL
	if pdfBase == "" {
		pdfBase = "https://arxiv.org/pdf"
	}
	client, e := sourceClient(a.Client, allowed, u.String(), pdfBase)
	if e != nil {
		p.Failure = "ORIGIN_DENIED"
		return p, nil
	}
	req, e := http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)
	if e != nil {
		return p, e
	}
	req.Header.Set("User-Agent", "ResearchOS-source-adapter/1.0 (research use)")
	resp, e := client.Do(req)
	if e != nil {
		if errors.Is(e, ErrSourceOrigin) {
			p.Failure = "ORIGIN_DENIED"
			return p, nil
		}
		p.Failure = "TIMEOUT_OR_NETWORK"
		return p, e
	}
	defer resp.Body.Close()
	p.HTTPStatus = resp.StatusCode
	if resp.StatusCode != 200 {
		p.Failure = classifyHTTP(resp.StatusCode, resp.Header)
		p.RetryAfter = retryTime(resp.Header, time.Now())
		return p, nil
	}
	raw, e := io.ReadAll(io.LimitReader(resp.Body, (2<<20)+1))
	if e != nil {
		return p, e
	}
	if len(raw) > 2<<20 {
		p.Failure = "TRUNCATED"
		return p, nil
	}
	p.RawResponse = raw
	p.RawMediaType = "application/atom+xml"
	var feed atomFeed
	if e = xml.Unmarshal(raw, &feed); e != nil {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	if len(feed.Entries) == 0 {
		p.Complete = true
		return p, nil
	}
	entry := feed.Entries[0]
	if !strings.HasSuffix(entry.ID, "/abs/"+id) {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	published, e := time.Parse(time.RFC3339, entry.Published)
	if e != nil {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	if published.Before(q.From) || !published.Before(q.To) {
		p.Complete = true
		return p, nil
	}
	modified, e := time.Parse(time.RFC3339, entry.Updated)
	if e != nil {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	var names []string
	for _, author := range entry.Authors {
		if n := strings.TrimSpace(author.Name); n != "" {
			names = append(names, n)
		}
	}
	if len(names) == 0 {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	pdfURL := strings.TrimRight(pdfBase, "/") + "/" + url.PathEscape(id)
	pdfReq, e := http.NewRequestWithContext(ctx, http.MethodGet, pdfURL, nil)
	if e != nil {
		return p, e
	}
	pdfReq.Header.Set("User-Agent", "ResearchOS-source-adapter/1.0 (research use)")
	pdfResp, e := client.Do(pdfReq)
	if e != nil {
		if errors.Is(e, ErrSourceOrigin) {
			p.Failure = "ORIGIN_DENIED"
			return p, nil
		}
		p.Failure = "DETAIL_UNAVAILABLE"
		return p, e
	}
	defer pdfResp.Body.Close()
	if pdfResp.StatusCode != 200 {
		p.Failure = classifyHTTP(pdfResp.StatusCode, pdfResp.Header)
		p.RetryAfter = retryTime(pdfResp.Header, time.Now())
		return p, nil
	}
	body, e := io.ReadAll(io.LimitReader(pdfResp.Body, (32<<20)+1))
	if e != nil {
		return p, e
	}
	if len(body) > 32<<20 {
		p.Failure = "TRUNCATED"
		return p, nil
	}
	if len(body) < 1024 || !bytes.HasPrefix(body, []byte("%PDF-")) {
		p.Failure = "INVALID_FULLTEXT"
		return p, nil
	}
	if n := pdfResp.Header.Get("Content-Length"); n != "" {
		length, err := strconv.Atoi(n)
		if err == nil && length != len(body) {
			p.Failure = "TRUNCATED"
			return p, nil
		}
	}
	// A successful transfer can still be an incomplete PDF. Parse its xref,
	// trailer, page tree and object graph before declaring a full snapshot.
	conf := model.NewStatelessConfiguration()
	conf.Optimize = false
	conf.Limits.MaxInputBytes = 32 << 20
	conf.Limits.MaxObjectBytes = 8 << 20
	conf.Limits.MaxStreamBytes = 32 << 20
	conf.Limits.MaxDecodeBytes = 64 << 20
	conf.Limits.MaxObjectCount = 1_000_000
	conf.Limits.MaxXRefEntries = 1_000_000
	if e = pdfapi.Validate(ctx, bytes.NewReader(body), conf, nil); e != nil {
		p.Failure = "INVALID_FULLTEXT"
		return p, nil
	}
	canonical := "https://arxiv.org/abs/" + id
	p.Items = []Item{{SourceID: q.SourceID, CanonicalURL: canonical, UpstreamID: id, Author: strings.Join(names, ", "), PublishedAt: published, ModifiedAt: &modified, UpstreamRevision: id, Body: body, MediaType: "application/pdf", Locator: "pdf:all"}}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	p.Complete = true
	return p, nil
}
