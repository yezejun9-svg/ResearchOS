package sources

import (
	"bytes"
	"context"
	"crypto/sha1"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// GitHubReadme captures a repository's README at the latest commit touching
// that file. The commit SHA pins the body; a moving default-branch URL does not.
type GitHubReadme struct {
	Client         *http.Client
	BaseURL        string
	AllowedOrigins []string
}

func (a GitHubReadme) Fetch(ctx context.Context, q Query) (Page, error) {
	p := Page{RequestedFrom: q.From, RequestedTo: q.To}
	if !bounded(q) || q.Limit != 1 || q.Cursor != "" || !strings.HasPrefix(q.Text, "readme:") {
		return p, ErrInvalidQuery
	}
	repo := strings.TrimPrefix(q.Text, "readme:")
	parts := strings.Split(repo, "/")
	if len(parts) != 2 || !githubPathPart(parts[0]) || !githubPathPart(parts[1]) {
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
	commitsURL := fmt.Sprintf("%s/repos/%s/%s/commits?path=README.md&per_page=1", strings.TrimRight(base, "/"), url.PathEscape(parts[0]), url.PathEscape(parts[1]))
	client, err := sourceClient(a.Client, allowed, func(v string) { p.RequestURLs = append(p.RequestURLs, v) }, commitsURL)
	if err != nil {
		p.Failure = "ORIGIN_DENIED"
		return p, nil
	}
	commitBody, ok, err := readGitHubJSON(ctx, client, commitsURL, &p)
	if err != nil || !ok {
		return p, err
	}
	var commits []struct {
		SHA    string `json:"sha"`
		Commit struct {
			Committer struct {
				Name string `json:"name"`
				Date string `json:"date"`
			} `json:"committer"`
		} `json:"commit"`
		Author struct {
			Login string `json:"login"`
		} `json:"author"`
	}
	commitBodyTrimmed := bytes.TrimSpace(commitBody)
	if len(commitBodyTrimmed) == 0 || commitBodyTrimmed[0] != '[' || json.Unmarshal(commitBody, &commits) != nil || len(commits) != 1 || !githubSHA(commits[0].SHA) {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	modified, err := time.Parse(time.RFC3339, commits[0].Commit.Committer.Date)
	if err != nil {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	author := commits[0].Author.Login
	if author == "" {
		author = commits[0].Commit.Committer.Name
	}
	if author == "" {
		p.Failure = "INCOMPLETE_ITEM"
		return p, nil
	}
	contentsURL := fmt.Sprintf("%s/repos/%s/%s/readme?ref=%s", strings.TrimRight(base, "/"), url.PathEscape(parts[0]), url.PathEscape(parts[1]), commits[0].SHA)
	if !sourceAllowed(allowed, contentsURL) {
		p.Failure = "ORIGIN_DENIED"
		return p, nil
	}
	contentsBody, ok, err := readGitHubJSON(ctx, client, contentsURL, &p)
	if err != nil || !ok {
		return p, err
	}
	var content struct {
		Type     string `json:"type"`
		Encoding string `json:"encoding"`
		Path     string `json:"path"`
		Content  string `json:"content"`
		Size     int    `json:"size"`
		SHA      string `json:"sha"`
	}
	if json.Unmarshal(contentsBody, &content) != nil || content.Type != "file" || content.Encoding != "base64" || !strings.EqualFold(content.Path, "README.md") || !githubSHA(content.SHA) {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	full, err := base64.StdEncoding.DecodeString(content.Content)
	if err != nil || len(full) == 0 || len(full) > 2<<20 || len(full) != content.Size {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	gitBlob := sha1.Sum(append([]byte(fmt.Sprintf("blob %d\x00", len(full))), full...))
	if fmt.Sprintf("%x", gitBlob) != content.SHA {
		p.Failure = "INVALID_RESPONSE"
		return p, nil
	}
	p.RawResponse, err = json.Marshal(map[string]json.RawMessage{"commits": commitBody, "readme": contentsBody})
	if err != nil {
		return p, err
	}
	p.RawMediaType = "application/vnd.github+json"
	if !modified.Before(q.To) {
		p.Failure = "WINDOW_UNSUPPORTED"
		return p, nil
	}
	if modified.Before(q.From) {
		p.Complete = true
		return p, nil
	}
	canonical := fmt.Sprintf("https://github.com/%s/%s/blob/%s/README.md", parts[0], parts[1], commits[0].SHA)
	p.Items = []Item{{SourceID: q.SourceID, CanonicalURL: canonical, UpstreamID: content.SHA, Author: author, PublishedAt: modified, UpstreamRevision: commits[0].SHA, Body: full, MediaType: "text/markdown; charset=utf-8", Locator: "README.md"}}
	p.ObservedFrom, p.ObservedTo = observed(p.Items)
	p.Complete = true
	return p, nil
}

func readGitHubJSON(ctx context.Context, client *http.Client, endpoint string, p *Page) ([]byte, bool, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, false, err
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "ResearchOS-source-adapter")
	p.RequestURLs = append(p.RequestURLs, endpoint)
	resp, err := client.Do(req)
	if err != nil {
		if errors.Is(err, ErrSourceOrigin) {
			p.Failure = "ORIGIN_DENIED"
			return nil, false, nil
		}
		p.Failure = "TIMEOUT_OR_NETWORK"
		return nil, false, err
	}
	defer resp.Body.Close()
	p.FinalURLs = append(p.FinalURLs, resp.Request.URL.String())
	p.FetchedAt = time.Now().UTC()
	p.HTTPStatus = resp.StatusCode
	if resp.StatusCode != http.StatusOK {
		p.Failure = classifyHTTP(resp.StatusCode, resp.Header)
		p.RetryAfter = retryTime(resp.Header, time.Now())
		return nil, false, nil
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, (3<<20)+1))
	if err != nil {
		return nil, false, err
	}
	if len(body) > 3<<20 {
		p.Failure = "TRUNCATED"
		return nil, false, nil
	}
	return body, true, nil
}

func githubSHA(value string) bool {
	if len(value) != 40 {
		return false
	}
	for _, c := range value {
		if !strings.ContainsRune("0123456789abcdef", c) {
			return false
		}
	}
	return true
}
