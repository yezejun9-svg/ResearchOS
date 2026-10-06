package sources

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// GitHubPR reads one configured canonical PR detail; it never interprets a
// search index or a closed issue as a merged pull request.
type GitHubPR struct {
	Client         *http.Client
	BaseURL        string
	AllowedOrigins []string
}

func (a GitHubPR) Fetch(ctx context.Context, q Query) (Page, error) {
	p := Page{RequestedFrom: q.From, RequestedTo: q.To, AccessScope: "PINNED_PR_DETAIL"}
	parts := strings.Split(strings.TrimPrefix(q.Text, "pr:"), "/")
	if !bounded(q) || q.Limit != 1 || q.Cursor != "" || !strings.HasPrefix(q.Text, "pr:") || len(parts) != 3 || !githubPathPart(parts[0]) || !githubPathPart(parts[1]) {
		return p, ErrInvalidQuery
	}
	number, e := strconv.Atoi(parts[2])
	if e != nil || number < 1 {
		return p, ErrInvalidQuery
	}
	base := a.BaseURL
	if base == "" {
		base = "https://api.github.com"
	}
	allowed := a.AllowedOrigins
	if len(allowed) == 0 {
		allowed = []string{"https://api.github.com", "https://github.com"}
	}
	endpoint := fmt.Sprintf("%s/repos/%s/%s/pulls/%d", strings.TrimRight(base, "/"), parts[0], parts[1], number)
	client, e := sourceClient(a.Client, allowed, func(u string) { p.RequestURLs = append(p.RequestURLs, u) }, endpoint)
	if e != nil {
		p.Failure = "ORIGIN_DENIED"
		return p, nil
	}
	body, ok, e := readGitHubJSON(ctx, client, endpoint, &p)
	if e != nil || !ok {
		return p, e
	}
	p.RawResponse, p.RawMediaType = body, "application/vnd.github+json"
	var pr struct {
		ID        int64      `json:"id"`
		Number    int        `json:"number"`
		URL       string     `json:"html_url"`
		State     string     `json:"state"`
		Merged    *bool      `json:"merged"`
		MergedAt  *time.Time `json:"merged_at"`
		CreatedAt time.Time  `json:"created_at"`
		UpdatedAt time.Time  `json:"updated_at"`
		Body      *string    `json:"body"`
		User      struct {
			Login string `json:"login"`
		} `json:"user"`
		Head struct {
			SHA string `json:"sha"`
		} `json:"head"`
		MergeCommit string `json:"merge_commit_sha"`
	}
	canonical := fmt.Sprintf("https://github.com/%s/%s/pull/%d", parts[0], parts[1], number)
	if json.Unmarshal(body, &pr) != nil || pr.ID <= 0 || pr.Number != number || pr.URL != canonical || pr.User.Login == "" || !githubSHA(pr.Head.SHA) || pr.CreatedAt.IsZero() || pr.UpdatedAt.IsZero() || pr.Body == nil || pr.Merged == nil {
		p.Failure = "INVALID_PR_DETAIL"
		return p, nil
	}
	state := ""
	switch pr.State {
	case "open":
		if !*pr.Merged && pr.MergedAt == nil {
			state = "OPEN"
		}
	case "closed":
		if *pr.Merged && pr.MergedAt != nil && githubSHA(pr.MergeCommit) {
			state = "MERGED"
		} else if !*pr.Merged && pr.MergedAt == nil {
			state = "CLOSED"
		}
	}
	if state == "" {
		p.Failure = "INCONSISTENT_PR_STATE"
		return p, nil
	}
	if !pr.CreatedAt.Before(q.To) {
		p.Failure = "WINDOW_UNSUPPORTED"
		return p, nil
	}
	if pr.CreatedAt.Before(q.From) {
		p.Complete = true
		return p, nil
	}
	// Original detail JSON retains empty authored bodies, state flags and commit
	// identity; it is a full provider detail document rather than an index snippet.
	p.Items = []Item{{SourceID: q.SourceID, CanonicalURL: canonical, UpstreamID: strconv.FormatInt(pr.ID, 10), Author: pr.User.Login, PublishedAt: pr.CreatedAt, ModifiedAt: &pr.UpdatedAt, UpstreamRevision: pr.Head.SHA, Body: body, MediaType: p.RawMediaType, Locator: "pull_request.body", ReadLevel: "BODY", PRState: state}}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	p.Complete = true
	return p, nil
}
