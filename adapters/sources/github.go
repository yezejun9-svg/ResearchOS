package sources

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// GitHubReleases reads public releases of one configured repository. It does
// not claim to search every GitHub repository or all commits in a window.
type GitHubReleases struct {
	Client         *http.Client
	BaseURL        string
	AllowedOrigins []string
}

type githubRelease struct {
	ID          int64  `json:"id"`
	HTMLURL     string `json:"html_url"`
	Body        string `json:"body"`
	TagName     string `json:"tag_name"`
	PublishedAt string `json:"published_at"`
	CreatedAt   string `json:"created_at"`
	Author      struct {
		Login string `json:"login"`
	} `json:"author"`
}

func (a GitHubReleases) Fetch(ctx context.Context, q Query) (Page, error) {
	p := Page{RequestedFrom: q.From, RequestedTo: q.To}
	if !bounded(q) || !strings.HasPrefix(q.Text, "repo:") {
		return p, ErrInvalidQuery
	}
	repo := strings.TrimPrefix(q.Text, "repo:")
	parts := strings.Split(repo, "/")
	if len(parts) != 2 || !githubPathPart(parts[0]) || !githubPathPart(parts[1]) {
		return p, ErrInvalidQuery
	}
	page := 1
	if q.Cursor != "" {
		n, e := strconv.Atoi(q.Cursor)
		if e != nil || n < 1 || n > 1000 {
			return p, ErrInvalidQuery
		}
		page = n
	}
	base := a.BaseURL
	if base == "" {
		base = "https://api.github.com"
	}
	u := fmt.Sprintf("%s/repos/%s/%s/releases?per_page=%d&page=%d", strings.TrimRight(base, "/"), url.PathEscape(parts[0]), url.PathEscape(parts[1]), q.Limit, page)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return p, err
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "ResearchOS-source-adapter")
	allowed := a.AllowedOrigins
	if len(allowed) == 0 {
		allowed = []string{"https://api.github.com", "https://github.com"}
	}
	client, err := sourceClient(a.Client, allowed, func(v string) { p.RequestURLs = append(p.RequestURLs, v) }, u)
	if err != nil {
		p.Failure = "ORIGIN_DENIED"
		return p, nil
	}
	p.RequestURLs = append(p.RequestURLs, u)
	resp, err := client.Do(req)
	if err != nil {
		if errors.Is(err, ErrSourceOrigin) {
			p.Failure = "ORIGIN_DENIED"
			return p, nil
		}
		p.Failure = "TIMEOUT_OR_NETWORK"
		return p, err
	}
	defer resp.Body.Close()
	p.FinalURLs = append(p.FinalURLs, resp.Request.URL.String())
	p.FetchedAt = time.Now().UTC()
	p.HTTPStatus = resp.StatusCode
	if resp.StatusCode != 200 {
		p.Failure = classifyHTTP(resp.StatusCode, resp.Header)
		p.RetryAfter = retryTime(resp.Header, time.Now())
		return p, nil
	}
	raw, err := io.ReadAll(io.LimitReader(resp.Body, (4<<20)+1))
	if err != nil {
		return p, err
	}
	if len(raw) > 4<<20 {
		p.Failure = "TRUNCATED"
		return p, nil
	}
	p.RawResponse = raw
	p.RawMediaType = "application/vnd.github+json"
	var releases []githubRelease
	if err = json.Unmarshal(raw, &releases); err != nil {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	for _, r := range releases {
		published, e := time.Parse(time.RFC3339, r.PublishedAt)
		if e != nil {
			p.Failure = "INVALID_RESPONSE"
			return p, nil
		}
		if published.Before(q.From) || !published.Before(q.To) {
			continue
		}
		if r.ID == 0 || r.Author.Login == "" || r.TagName == "" || strings.TrimSpace(r.Body) == "" {
			p.Failure = "INCOMPLETE_ITEM"
			return p, nil
		}
		canonical := fmt.Sprintf("https://github.com/%s/%s/releases/tag/%s", parts[0], parts[1], url.PathEscape(r.TagName))
		if r.HTMLURL != canonical {
			p.Failure = "INVALID_RESPONSE"
			return p, nil
		}
		sha, status, headers, e := a.commitSHA(ctx, client, base, parts[0], parts[1], r.TagName, &p)
		if e != nil {
			if errors.Is(e, ErrSourceOrigin) {
				p.Failure = "ORIGIN_DENIED"
				return p, nil
			}
			if status != 0 {
				p.HTTPStatus = status
				p.Failure = classifyHTTP(status, headers)
				p.RetryAfter = retryTime(headers, time.Now())
			} else {
				p.Failure = "DETAIL_UNAVAILABLE"
			}
			return p, nil
		}
		p.Items = append(p.Items, Item{SourceID: q.SourceID, CanonicalURL: canonical, UpstreamID: strconv.FormatInt(r.ID, 10), Author: r.Author.Login, PublishedAt: published, UpstreamRevision: sha, Body: []byte(r.Body), MediaType: "text/markdown; charset=utf-8", Locator: "release.body"})
	}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	// The Link relation is authoritative even when the server returns fewer
	// than requested entries. A full page without Link is not proof of closure.
	if hasNextLink(resp.Header.Get("Link")) {
		p.NextCursor = strconv.Itoa(page + 1)
	} else if len(releases) == q.Limit {
		p.Failure = "PAGINATION_UNKNOWN"
	} else {
		p.Complete = true
	}
	return p, nil
}

func (a GitHubReleases) commitSHA(ctx context.Context, client *http.Client, base, owner, repo, tag string, p *Page) (string, int, http.Header, error) {
	u := fmt.Sprintf("%s/repos/%s/%s/commits/%s", strings.TrimRight(base, "/"), url.PathEscape(owner), url.PathEscape(repo), url.PathEscape(tag))
	p.RequestURLs = append(p.RequestURLs, u)
	allowed := a.AllowedOrigins
	if len(allowed) == 0 {
		allowed = []string{"https://api.github.com", "https://github.com"}
	}
	if !sourceAllowed(allowed, u) {
		return "", 0, nil, ErrSourceOrigin
	}
	req, e := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if e != nil {
		return "", 0, nil, e
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "ResearchOS-source-adapter")
	resp, e := client.Do(req)
	if e != nil {
		return "", 0, nil, e
	}
	defer resp.Body.Close()
	p.FinalURLs = append(p.FinalURLs, resp.Request.URL.String())
	if resp.StatusCode != 200 {
		return "", resp.StatusCode, resp.Header, fmt.Errorf("commit lookup returned %d", resp.StatusCode)
	}
	var result struct {
		SHA string `json:"sha"`
	}
	if e = json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&result); e != nil {
		return "", 0, nil, e
	}
	if len(result.SHA) != 40 {
		return "", 0, nil, fmt.Errorf("invalid commit SHA")
	}
	for _, c := range result.SHA {
		if !strings.ContainsRune("0123456789abcdef", c) {
			return "", 0, nil, fmt.Errorf("invalid commit SHA")
		}
	}
	return result.SHA, 200, resp.Header, nil
}

func githubPathPart(s string) bool {
	if s == "" || len(s) > 100 {
		return false
	}
	for _, c := range s {
		if !strings.ContainsRune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.", c) {
			return false
		}
	}
	return true
}

func classifyHTTP(status int, h http.Header) string {
	switch status {
	case 401:
		return "AUTH_REVOKED"
	case 429:
		return "RATE_LIMITED"
	case 403:
		if h != nil && (h.Get("X-RateLimit-Remaining") == "0" || h.Get("Retry-After") != "") {
			return "RATE_LIMITED"
		}
		return "FORBIDDEN"
	case 404:
		return "NOT_FOUND"
	default:
		return "UNAVAILABLE"
	}
}
func retryTime(h http.Header, now time.Time) *time.Time {
	if seconds, e := strconv.Atoi(h.Get("Retry-After")); e == nil && seconds >= 0 {
		t := now.Add(time.Duration(seconds) * time.Second)
		return &t
	}
	if absolute, e := http.ParseTime(h.Get("Retry-After")); e == nil {
		t := absolute.UTC()
		return &t
	}
	if reset, e := strconv.ParseInt(h.Get("X-RateLimit-Reset"), 10, 64); e == nil && reset > 0 {
		t := time.Unix(reset, 0).UTC()
		return &t
	}
	return nil
}

func hasNextLink(value string) bool {
	for _, entry := range strings.Split(value, ",") {
		if strings.Contains(entry, `rel="next"`) {
			return true
		}
	}
	return false
}
