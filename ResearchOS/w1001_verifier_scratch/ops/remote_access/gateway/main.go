// Package main is an optional, explicitly started loopback gateway for a
// reviewed HTTPS tunnel. The control service's default listener is unchanged.
package main

import (
	"errors"
	"flag"
	"fmt"
	"log"
	"mime"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"path"
	"strings"
	"time"
)

func loopbackAddress(address string) bool {
	h, _, e := net.SplitHostPort(address)
	ip := net.ParseIP(h)
	return e == nil && ip != nil && ip.IsLoopback()
}

// Security-sensitive request fields must never silently select the first of
// several values. Absent optional headers remain distinguishable from blanks.
func oneHeader(header http.Header, name string) (string, bool) {
	values := header.Values(name)
	if len(values) == 0 {
		return "", true
	}
	if len(values) != 1 || values[0] == "" {
		return "", false
	}
	return values[0], true
}
func gateway(upstream, publicOrigin string) (http.Handler, error) {
	target, e := url.Parse(upstream)
	if e != nil || target.Scheme != "http" || !loopbackAddress(target.Host) || target.Path != "" || target.User != nil || target.RawQuery != "" || target.Fragment != "" {
		return nil, errors.New("upstream must be an explicit loopback HTTP origin")
	}
	origin, e := url.Parse(publicOrigin)
	if e != nil || origin.Scheme != "https" || origin.Host == "" || origin.User != nil || origin.Path != "" || origin.RawQuery != "" || origin.Fragment != "" || strings.Contains(origin.Host, "*") {
		return nil, errors.New("public-origin must be one exact HTTPS origin")
	}
	proxy := &httputil.ReverseProxy{Rewrite: func(p *httputil.ProxyRequest) {
		p.SetURL(target)
		p.Out.Host = origin.Host
		// No ambient browser authentication or client-supplied proxy identity.
		for k := range p.Out.Header {
			if strings.HasPrefix(strings.ToLower(k), "x-forwarded-") || strings.HasPrefix(strings.ToLower(k), "cf-") {
				p.Out.Header.Del(k)
			}
		}
		p.Out.Header.Del("Cookie")
		p.Out.Header.Del("Forwarded")
		p.Out.Header.Set("X-ResearchOS-Remote-Access", "device")
	}, FlushInterval: -1, ErrorHandler: func(w http.ResponseWriter, r *http.Request, e error) {
		http.Error(w, "control service unavailable", 502)
	}}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
		remote, _, err := net.SplitHostPort(r.RemoteAddr)
		proto, protoOK := oneHeader(r.Header, "X-Forwarded-Proto")
		requestOrigin, originOK := oneHeader(r.Header, "Origin")
		fetchSite, siteOK := oneHeader(r.Header, "Sec-Fetch-Site")
		contentType, typeOK := oneHeader(r.Header, "Content-Type")
		authorization, authOK := oneHeader(r.Header, "Authorization")
		if !protoOK || !originOK || !siteOK || !typeOK || !authOK {
			http.Error(w, "ambiguous request headers rejected", 403)
			return
		}
		if err != nil || net.ParseIP(remote) == nil || !net.ParseIP(remote).IsLoopback() || r.Host != origin.Host || proto != "https" {
			http.Error(w, "HTTPS tunnel origin required", 403)
			return
		}
		if requestOrigin != "" && requestOrigin != publicOrigin {
			http.Error(w, "same origin required", 403)
			return
		}
		if fetchSite != "" && fetchSite != "same-origin" && fetchSite != "same-site" && fetchSite != "none" {
			http.Error(w, "cross-site request rejected", 403)
			return
		}
		if r.URL.RawPath != "" || strings.Contains(r.URL.Path, "\\") || path.Clean(r.URL.Path) != r.URL.Path {
			http.NotFound(w, r)
			return
		}
		if r.Method != "GET" && r.Method != "HEAD" {
			media, _, parseError := mime.ParseMediaType(contentType)
			if requestOrigin != publicOrigin || parseError != nil || media != "application/json" {
				http.Error(w, "same-origin JSON required", 403)
				return
			}
		}
		if r.URL.Path == "/remote-info" && r.Method == "GET" {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprint(w, `{"remote":true,"events":"poll","public_origin":"`+publicOrigin+`"}`)
			return
		}
		if strings.HasPrefix(r.URL.Path, "/v1/") {
			proof := r.URL.Path == "/v1/device-pairings/redeem" || r.URL.Path == "/v1/device-sessions/refresh"
			project := r.URL.Path == "/v1/projects" && r.Method == "GET" || strings.HasPrefix(r.URL.Path, "/v1/projects/")
			if (!proof && !project) || strings.HasSuffix(r.URL.Path, "/events/stream") {
				http.NotFound(w, r)
				return
			}
			if !proof && !strings.HasPrefix(authorization, "Bearer ") {
				http.Error(w, "device credential required", 401)
				return
			}
			proxy.ServeHTTP(w, r)
			return
		}
		// Expose only the built UI, never filesystem listings, health or admin paths.
		static := r.URL.Path == "/" || r.URL.Path == "/pair" || strings.HasPrefix(r.URL.Path, "/p/") || strings.HasPrefix(r.URL.Path, "/assets/") && (strings.HasSuffix(r.URL.Path, ".js") || strings.HasSuffix(r.URL.Path, ".css"))
		if !static || (r.Method != "GET" && r.Method != "HEAD") {
			http.NotFound(w, r)
			return
		}
		for key, values := range r.URL.Query() {
			if !strings.HasPrefix(r.URL.Path, "/p/") || key != "focus" || len(values) != 1 {
				http.NotFound(w, r)
				return
			}
		}
		proxy.ServeHTTP(w, r)
	}), nil
}
func main() {
	listen := flag.String("listen", "127.0.0.1:8790", "loopback gateway listener")
	upstream := flag.String("upstream", "http://127.0.0.1:8787", "control loopback origin")
	origin := flag.String("public-origin", "", "exact reviewed HTTPS tunnel origin")
	flag.Parse()
	if !loopbackAddress(*listen) {
		log.Fatal("gateway listener must remain loopback")
	}
	handler, e := gateway(*upstream, *origin)
	if e != nil {
		log.Fatal(e)
	}
	server := &http.Server{Addr: *listen, Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 15 * time.Second, IdleTimeout: 30 * time.Second, MaxHeaderBytes: 16 * 1024}
	log.Print("remote gateway listening on loopback; request bodies and headers are not logged")
	if e = server.ListenAndServe(); e != nil && !errors.Is(e, http.ErrServerClosed) {
		log.Fatal("remote gateway stopped")
	}
}
