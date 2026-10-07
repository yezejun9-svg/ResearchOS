//go:build windows

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
)

type localAPI struct {
	url, project string
	server       *http.Server
	listener     net.Listener
	client       *http.Client
}

func (s *setup) startAPI(ctx context.Context, coordinator domain.ClientSessionRuntime) (*localAPI, error) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	authority, _, scanner, err := s.authority()
	if err != nil {
		listener.Close()
		return nil, err
	}
	handler := api.HandlerWithLocalHost(s.db, s.repo+"/apps/web/dist", s.svc, coordinator, s.host.InstanceID(), authority, scanner)
	server := &http.Server{Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 20 * time.Second}
	endpoint := &localAPI{url: "http://" + listener.Addr().String(), project: s.state.ProjectID, server: server, listener: listener, client: &http.Client{Timeout: 25 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("local API redirect refused") }}}
	go func() { _ = server.Serve(listener) }()
	request, _ := http.NewRequestWithContext(ctx, http.MethodGet, endpoint.url+"/healthz", nil)
	response, err := endpoint.client.Do(request)
	if err != nil {
		endpoint.close()
		return nil, err
	}
	response.Body.Close()
	if response.StatusCode != 200 {
		endpoint.close()
		return nil, errors.New("local API readiness failed")
	}
	return endpoint, nil
}

func (a *localAPI) close() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = a.server.Shutdown(ctx)
	_ = a.listener.Close()
}

func (a *localAPI) path(tail string) string { return "/v1/projects/" + a.project + tail }

func (a *localAPI) call(ctx context.Context, token, method, path, tag string, body any, want int) (domain.Object, error) {
	var raw []byte
	if body != nil {
		if bytesBody, ok := body.([]byte); ok {
			raw = bytesBody
		} else {
			raw = domain.Bytes(body)
		}
	}
	request, err := http.NewRequestWithContext(ctx, method, a.url+path, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	request.Header.Set("Authorization", "Bearer "+token)
	if method != http.MethodGet {
		request.Header.Set("Idempotency-Key", domain.ID())
	}
	if tag != "" {
		request.Header.Set("If-Match", tag)
	}
	if body != nil {
		request.Header.Set("Content-Type", "application/json")
	}
	response, err := a.client.Do(request)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	data, err := io.ReadAll(io.LimitReader(response.Body, 4<<20))
	if err != nil {
		return nil, err
	}
	result := domain.Object{}
	if err = json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s %s invalid response: %w", method, path, err)
	}
	if response.StatusCode != want {
		return nil, fmt.Errorf("%s %s status %d want %d: %s: %s", method, path, response.StatusCode, want, domain.Str(result, "code"), domain.Str(result, "message"))
	}
	return result, nil
}

func (a *localAPI) get(ctx context.Context, token, path string) (domain.Object, error) {
	return a.call(ctx, token, http.MethodGet, path, "", nil, http.StatusOK)
}

func (a *localAPI) projectState(ctx context.Context, token string) (domain.Object, error) {
	return a.get(ctx, token, a.path("/state"))
}

func tag(o domain.Object) string {
	n, err := domain.Num(o, "revision")
	if err != nil {
		return ""
	}
	return `"r` + strconv.FormatInt(n, 10) + `"`
}

func (a *localAPI) postWithState(ctx context.Context, token, path string, body any, want int) (domain.Object, error) {
	state, err := a.projectState(ctx, token)
	if err != nil {
		return nil, err
	}
	if tag(state) == "" {
		return nil, errors.New("ProjectState has no revision")
	}
	return a.call(ctx, token, http.MethodPost, path, tag(state), body, want)
}

func (a *localAPI) postWithSubject(ctx context.Context, token, path string, subject domain.Object, body any, want int) (domain.Object, error) {
	if tag(subject) == "" {
		return nil, errors.New("subject has no revision")
	}
	return a.call(ctx, token, http.MethodPost, path, tag(subject), body, want)
}

func (a *localAPI) uploadJSON(ctx context.Context, token string, value any) (domain.Object, []byte, error) {
	raw := domain.Bytes(value)
	if len(raw) > 4<<20 {
		return nil, nil, errors.New("LIVE profile exceeds upload bound")
	}
	u, err := a.call(ctx, token, http.MethodPost, a.path("/content"), "", raw, http.StatusCreated)
	return u, raw, err
}

func checkPath(path string) error {
	if path == "" || strings.Contains(path, "..") || !strings.HasPrefix(path, "/v1/") {
		return errors.New("invalid local API path")
	}
	return nil
}
