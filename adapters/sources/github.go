package sources

import (
	"context"
	"encoding/json"
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
	Client  *http.Client
	BaseURL string
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
	client := a.Client
	if client == nil {
		client = &http.Client{Timeout: 15 * time.Second}
	}
	resp, err := client.Do(req)
	if err != nil {
		p.Failure = "TIMEOUT_OR_NETWORK"
		return p, err
	}
	defer resp.Body.Close()
	p.HTTPStatus = resp.StatusCode
	if resp.StatusCode != 200 {
		p.Failure = classifyHTTP(resp.StatusCode)
		p.RetryAfter = retryTime(resp.Header, time.Now())
		return p, nil
	}
	raw, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20+1))
	if err != nil {
		return p, err
	}
	if len(raw) > 4<<20 {
		p.Failure = "TRUNCATED"
		return p, nil
	}
	var releases []githubRelease
	if err = json.Unmarshal(raw, &releases); err != nil {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	for _, r := range releases {
		published, e := time.Parse(time.RFC3339, r.PublishedAt)
		if e != nil || published.Before(q.From) || !published.Before(q.To) {
			continue
		}
		if r.ID == 0 || r.Author.Login == "" || r.TagName == "" || strings.TrimSpace(r.Body) == "" {
			continue
		}
		canonical := fmt.Sprintf("https://github.com/%s/%s/releases/tag/%s", parts[0], parts[1], url.PathEscape(r.TagName))
		if r.HTMLURL != canonical {
			continue
		}
		sha, e := a.commitSHA(ctx, client, base, parts[0], parts[1], r.TagName)
		if e != nil {
			p.Failure = "DETAIL_UNAVAILABLE"
			return p, nil
		}
		p.Items = append(p.Items, Item{SourceID: q.SourceID, CanonicalURL: canonical, UpstreamID: strconv.FormatInt(r.ID, 10), Author: r.Author.Login, PublishedAt: published, UpstreamRevision: sha, Body: []byte(r.Body), MediaType: "text/markdown; charset=utf-8", Locator: "release.body"})
	}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	// GitHub's releases endpoint is ordered newest-first. A full page may hide
	// older releases; an incomplete page is the only proof this query is done.
	if len(releases) == q.Limit {
		p.NextCursor = strconv.Itoa(page + 1)
	} else {
		p.Complete = true
	}
	return p, nil
}

func (a GitHubReleases) commitSHA(ctx context.Context, client *http.Client, base, owner, repo, tag string) (string, error) {
	u := fmt.Sprintf("%s/repos/%s/%s/commits/%s", strings.TrimRight(base, "/"), url.PathEscape(owner), url.PathEscape(repo), url.PathEscape(tag))
	req, e := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if e != nil {
		return "", e
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "ResearchOS-source-adapter")
	resp, e := client.Do(req)
	if e != nil {
		return "", e
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("commit lookup returned %d", resp.StatusCode)
	}
	var result struct {
		SHA string `json:"sha"`
	}
	if e = json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&result); e != nil {
		return "", e
	}
	if len(result.SHA) != 40 {
		return "", fmt.Errorf("invalid commit SHA")
	}
	for _, c := range result.SHA {
		if !strings.ContainsRune("0123456789abcdef", c) {
			return "", fmt.Errorf("invalid commit SHA")
		}
	}
	return result.SHA, nil
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

func classifyHTTP(status int) string {
	switch status {
	case 401:
		return "AUTH_REVOKED"
	case 403, 429:
		return "RATE_LIMITED"
	case 404:
		return "NOT_CONFIGURED"
	default:
		return "UNAVAILABLE"
	}
}
func retryTime(h http.Header, now time.Time) *time.Time {
	if seconds, e := strconv.Atoi(h.Get("Retry-After")); e == nil && seconds >= 0 {
		t := now.Add(time.Duration(seconds) * time.Second)
		return &t
	}
	if reset, e := strconv.ParseInt(h.Get("X-RateLimit-Reset"), 10, 64); e == nil && reset > 0 {
		t := time.Unix(reset, 0).UTC()
		return &t
	}
	return nil
}
