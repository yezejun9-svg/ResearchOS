package sources

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os/exec"
	"regexp"
	"strings"
	"time"
)

// BrowserActRunner is deliberately a narrow, testable boundary. Only public
// article fields returned by our JavaScript are parsed or persisted.
type BrowserActRunner interface {
	Run(context.Context, ...string) ([]byte, error)
}

type BrowserActCLI struct{ Executable string }

func (b BrowserActCLI) Run(ctx context.Context, args ...string) ([]byte, error) {
	cmd := exec.CommandContext(ctx, b.Executable, args...)
	return cmd.Output()
}

type XBrowser struct {
	Runner    BrowserActRunner
	BrowserID string
}

type xPublicPost struct {
	URL         string `json:"url"`
	PublishedAt string `json:"published_at"`
	Text        string `json:"text"`
	Author      string `json:"author"`
	Truncated   bool   `json:"truncated"`
}
type xPublicResult struct {
	URL   string        `json:"url"`
	Items []xPublicPost `json:"items"`
	Empty bool          `json:"empty"`
}

var xStatusURL = regexp.MustCompile(`^https://x\.com/([A-Za-z0-9_]{1,15})/status/([0-9]{1,25})$`)

const xSearchScript = `JSON.stringify({url:location.href,items:Array.from(document.querySelectorAll('article')).slice(0,20).map(a=>({url:a.querySelector('a[href*="/status/"]')?.href||"",published_at:a.querySelector('time')?.dateTime||"",text:a.querySelector('[data-testid="tweetText"]')?.innerText||"",author:a.querySelector('[data-testid="User-Name"] a[href^="/"]')?.getAttribute('href')||""})),empty:!!document.querySelector('[data-testid="emptyState"]')})`
const xPostScript = `JSON.stringify({url:location.href,items:Array.from(document.querySelectorAll('article')).filter(a=>a.querySelector('a[href*="/status/"]')?.href===location.href).slice(0,1).map(a=>({url:location.href,published_at:a.querySelector('time')?.dateTime||"",text:a.querySelector('[data-testid="tweetText"]')?.innerText||"",author:a.querySelector('[data-testid="User-Name"] a[href^="/"]')?.getAttribute('href')||"",truncated:!!a.querySelector('[data-testid="tweet-text-show-more-link"]')||Array.from(a.querySelectorAll('a,button')).some(x=>/^(show more|显示更多)$/i.test(x.innerText?.trim()||""))}))})`

// Fetch reads X's authorized public search page, then the canonical post page
// for a complete visible post body. It never inspects account sidebars or XHR
// authentication headers. UI search cannot certify exhaustive window coverage.
func (a XBrowser) Fetch(ctx context.Context, q Query) (Page, error) {
	p := Page{RequestedFrom: q.From, RequestedTo: q.To}
	if !bounded(q) || strings.TrimSpace(q.Text) == "" || len(q.Text) > 120 || a.Runner == nil || a.BrowserID == "" {
		return p, ErrInvalidQuery
	}
	query := q.Text + " since:" + q.From.UTC().Format("2006-01-02") + " until:" + q.To.UTC().Add(24*time.Hour).Format("2006-01-02")
	searchURL := "https://x.com/search?q=" + url.QueryEscape(query) + "&src=typed_query&f=live"
	p.RequestURLs = append(p.RequestURLs, searchURL)
	session := fmt.Sprintf("researchos-w07-%d", time.Now().UnixNano())
	if _, e := a.Runner.Run(ctx, "--session", session, "browser", "open", a.BrowserID, searchURL); e != nil {
		p.Failure = "UNAVAILABLE"
		return p, e
	}
	defer func() {
		cleanup, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_, _ = a.Runner.Run(cleanup, "session", "close", session)
	}()
	// The browser-open acknowledgement can precede X's client-rendered results.
	_, _ = a.Runner.Run(ctx, "--session", session, "wait", "stable", "--timeout", "15000")
	search, raw, e := a.eval(ctx, session, xSearchScript)
	if e != nil {
		p.Failure = "UNAVAILABLE"
		return p, e
	}
	if search.URL != searchURL {
		p.Failure = "AUTH_OR_NAVIGATION"
		return p, nil
	}
	if len(search.Items) == 0 && !search.Empty {
		_, _ = a.Runner.Run(ctx, "--session", session, "wait", "selector", "--selector", "main article", "--timeout", "15000")
		search, raw, e = a.eval(ctx, session, xSearchScript)
		if e != nil {
			p.Failure = "UNAVAILABLE"
			return p, e
		}
		if search.URL != searchURL {
			p.Failure = "AUTH_OR_NAVIGATION"
			return p, nil
		}
	}
	p.FinalURLs = append(p.FinalURLs, search.URL)
	p.FetchedAt = time.Now().UTC()
	// This is a deliberately narrow public-article extraction, never page HTML.
	p.RawResponse, p.RawMediaType = raw, "application/json"
	if len(search.Items) == 0 {
		if search.Empty {
			// A visible empty result is a valid observation, never exhaustive coverage.
			p.VisibleEmpty = true
		} else {
			p.Failure = "UNAVAILABLE"
		}
		return p, nil
	}
	for _, candidate := range search.Items {
		match := xStatusURL.FindStringSubmatch(candidate.URL)
		if match == nil {
			continue
		}
		published, e := time.Parse(time.RFC3339Nano, candidate.PublishedAt)
		if e != nil || published.Before(q.From) || !published.Before(q.To) {
			continue
		}
		if _, e = a.Runner.Run(ctx, "--session", session, "navigate", candidate.URL); e != nil {
			p.Failure = "DETAIL_UNAVAILABLE"
			return p, e
		}
		p.RequestURLs = append(p.RequestURLs, candidate.URL)
		_, _ = a.Runner.Run(ctx, "--session", session, "wait", "stable", "--timeout", "15000")
		post, _, e := a.eval(ctx, session, xPostScript)
		if e != nil {
			p.Failure = "DETAIL_UNAVAILABLE"
			return p, e
		}
		if post.URL != candidate.URL || len(post.Items) != 1 {
			p.Failure = "INCOMPLETE_ITEM"
			return p, nil
		}
		p.FinalURLs = append(p.FinalURLs, post.URL)
		p.FetchedAt = time.Now().UTC()
		full := post.Items[0]
		if full.URL != candidate.URL || full.Author != "/"+match[1] || strings.TrimSpace(full.Text) == "" || full.PublishedAt != candidate.PublishedAt || full.Truncated {
			p.Failure = "INCOMPLETE_ITEM"
			return p, nil
		}
		p.Items = append(p.Items, Item{SourceID: q.SourceID, CanonicalURL: full.URL, UpstreamID: match[2], Author: match[1], PublishedAt: published, UpstreamRevision: match[2], Body: []byte(full.Text), MediaType: "text/plain; charset=utf-8", Locator: "post.text"})
		if len(p.Items) >= q.Limit {
			break
		}
	}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	if len(p.Items) > 0 {
		p.NextCursor = "observed_tail:" + p.Items[len(p.Items)-1].UpstreamID
	}
	// No complete=true from a visible X UI page: results can be limited or
	// re-ordered, and there is no durable provider cursor in this channel.
	return p, nil
}

func (a XBrowser) eval(ctx context.Context, session, script string) (xPublicResult, []byte, error) {
	var result xPublicResult
	raw, e := a.Runner.Run(ctx, "--session", session, "eval", script)
	if e != nil {
		return result, nil, e
	}
	if len(raw) > 1<<20 {
		return result, nil, fmt.Errorf("public article extraction too large")
	}
	if e = json.Unmarshal(raw, &result); e != nil {
		return result, nil, e
	}
	return result, raw, nil
}
