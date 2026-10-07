//go:build windows

package domain

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

func stageRuntimeProgram(route RuntimeCoordinatorRoute, dispatch Object, inputs map[string][]byte) error {
	manifest := dispatch["manifest"].(map[string]any)
	profile := manifest["admission"].(map[string]any)["profile"].(map[string]any)
	if profile["backend"] != runtimeMuBackend {
		return nil
	}
	if e := validateRuntimeModelConfig(profile); e != nil {
		return e
	}
	if !filepath.IsAbs(route.BundleFile) {
		return errors.New("host Mu bundle binding required")
	}
	actual, e := filepath.EvalSymlinks(route.BundleFile)
	if e != nil || !strings.EqualFold(actual, filepath.Clean(route.BundleFile)) {
		return errors.New("Mu bundle reparse rejected")
	}
	info, e := os.Stat(actual)
	if e != nil || !info.Mode().IsRegular() || info.Size() > 32*1024*1024 {
		return errors.New("bounded Mu bundle required")
	}
	raw, e := os.ReadFile(actual)
	if e != nil || Digest(raw) != profile["bundle_hash"] {
		return errors.New("Mu bundle differs from frozen profile")
	}
	inputs["mu-worker.mjs"] = raw
	inputs["worker.json"] = Bytes(profile["model_config"])
	return nil
}

func (c *RuntimeCoordinator) brokerModel(ctx context.Context, route RuntimeCoordinatorRoute, provider RuntimeProviderRoute, runID, lease string, epoch int64, bridge *rt.Bridge, frame rt.BridgeFrame, payload, intent, dispatch Object) (Object, error) {
	body, e := validateRuntimeModelRequest(provider.ModelConfig, payload)
	if e != nil {
		return nil, e
	}
	var stream *rt.ModelStream
	unknown := func(reason string) (Object, error) {
		if stream != nil {
			stop, cancel := context.WithTimeout(context.Background(), time.Second)
			stream.Fail(stop)
			cancel()
		}
		if e := c.service.ObserveEffect(context.Background(), route.ProjectID, runID, frame.Key, "UNKNOWN", Object{"dispatch_key": dispatch["dispatch_key"], "epoch": epoch, "reason": reason}); e != nil {
			return nil, e
		}
		return nil, Fail(409, "STATE_CONFLICT", "model outcome UNKNOWN; automatic retry prohibited")
	}
	notDispatched := func() (Object, error) {
		// Credential resolution failed before HTTP request construction. This is a
		// known absent provider operation, unlike a transport failure after send.
		return c.recordNotAppliedEffect(route, provider, runID, epoch, bridge, frame, intent, dispatch, "CREDENTIAL_MISSING", "protected model credential unavailable; no provider request was sent")
	}
	if provider.CredentialRef != "" {
		if c.config.ModelCredential == nil {
			return notDispatched()
		}
		material, err := c.config.ModelCredential(ctx, provider)
		if err != nil || len(material) == 0 {
			return notDispatched()
		}
		provider.BearerToken = string(material)
		for i := range material {
			material[i] = 0
		}
	}
	req, e := http.NewRequestWithContext(ctx, http.MethodPost, provider.Endpoint, bytes.NewReader(Bytes(body)))
	if e != nil {
		return c.recordNotAppliedEffect(route, provider, runID, epoch, bridge, frame, intent, dispatch, "INVALID_REQUEST", "model request construction failed before dispatch")
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	if provider.BearerToken != "" {
		req.Header.Set("Authorization", "Bearer "+provider.BearerToken)
	}
	client := &http.Client{Timeout: 90 * time.Second, Transport: &http.Transport{Proxy: nil, DisableKeepAlives: true}, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("model redirect prohibited") }}
	defer client.CloseIdleConnections()
	response, e := client.Do(req)
	if e != nil {
		return unknown("model transport ended without complete response")
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK || !strings.HasPrefix(response.Header.Get("Content-Type"), "text/event-stream") {
		return unknown("model returned invalid SSE headers")
	}
	var raw, withheld []byte
	if bridge.Read().QueueRequired {
		binding, err := c.modelStreamBinding(ctx, route, runID, lease, epoch, bridge, frame, intent)
		if err != nil {
			return unknown("model stream initialization authority unavailable")
		}
		stream, err = bridge.OpenModelStream(ctx, binding)
		if err != nil {
			return unknown("model stream could not open")
		}
		quarantine, err := newModelSSEQuarantine(provider.BearerToken, c.config.SchedulerToken, route.ExecutorToken)
		if err != nil {
			return unknown("model quarantine unavailable")
		}
		chunk := make([]byte, 8192)
		for {
			n, readErr := response.Body.Read(chunk)
			if n > 0 {
				released, gateErr := quarantine.Feed(chunk[:n])
				if gateErr != nil {
					return unknown("model response rejected by quarantine")
				}
				if len(released) > 0 {
					if err = stream.Send(ctx, released, false); err != nil {
						return unknown("model stream transport failed")
					}
				}
			}
			if readErr == io.EOF {
				break
			}
			if readErr != nil {
				return unknown("model transport interrupted")
			}
		}
		raw, withheld, err = quarantine.Finish()
		if err != nil {
			return unknown("model returned no complete bounded SSE response")
		}
	} else {
		raw, e = io.ReadAll(io.LimitReader(response.Body, runtimeModelMaxSSEBytes+1))
		if e != nil || len(raw) > runtimeModelMaxSSEBytes || !completeRuntimeModelSSE(raw) {
			return unknown("model returned no complete bounded SSE response")
		}
		for _, secret := range []string{provider.BearerToken, c.config.SchedulerToken, route.ExecutorToken} {
			if secret != "" && bytes.Contains(raw, []byte(secret)) {
				return unknown("model response contained host credential material")
			}
		}
	}
	result := Object{"status": response.StatusCode, "content_type": "text/event-stream", "body": string(raw)}
	// A received response proves the operation completed, not what it cost.
	// Retain the original upper-bound reservation until a real billing fact arrives.
	receipt := Object{"key": frame.Key, "epoch": epoch, "run_id": runID, "receipt_id": Digest(raw), "state": "CONFIRMED", "model_transport": true, "actual_cost": nil, "payload": result}
	var reply Object
	if stream == nil {
		reply, e = runtimeEffectWireReply(frame, receipt)
	}
	if e != nil {
		return unknown("encoded model response exceeds bridge frame limit")
	}
	fact := Object{"version": 1, "project_id": route.ProjectID, "run_id": runID, "epoch": epoch, "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "effect_key": frame.Key, "request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "provider_response_hash": Digest(raw), "receipt": receipt}
	if e = writeRuntimeFact(filepath.Join(bridge.Directory(), "effect-"+strings.TrimPrefix(Digest([]byte(frame.Key)), "sha256:")+".json"), Bytes(fact)); e != nil {
		return unknown("model response persistence failed")
	}
	if e = c.ingestEffectFact(context.Background(), fact); e != nil {
		return nil, e
	}
	// Late responses may update billing/effect facts, but never regain execution authority.
	tx, _, _, e := c.dispatchGate(ctx, route, runID, lease, epoch)
	if e != nil {
		return nil, e
	}
	tx.Rollback()
	if stream != nil {
		if e = stream.Send(ctx, withheld, true); e != nil {
			return nil, e
		}
		summary, err := stream.Terminal(ctx, Digest(raw))
		if err != nil {
			return nil, err
		}
		reply = Object{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": summary}
	}
	return reply, nil
}
