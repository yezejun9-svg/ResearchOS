//go:build windows

package domain

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/base64"
	"errors"
	"path/filepath"
	"strings"

	rt "researchos.local/research-os/adapters/runtime"
)

const runtimeModelMaxSSEBytes = 2 * 1024 * 1024

// Both first delivery and idempotent replay use this encoding. Durable receipts
// retain the original SSE for independent verification; compression changes only
// the bounded bridge frame, not model content or the SDK parser.
func runtimeEffectWireReply(frame rt.BridgeFrame, receipt Object) (Object, error) {
	payload := receipt["payload"]
	if receipt["model_transport"] == true && receipt["state"] == "CONFIRMED" {
		result, ok := payload.(map[string]any)
		if !ok {
			return nil, errors.New("model response payload missing")
		}
		raw := []byte(Str(result, "body"))
		if len(raw) > runtimeModelMaxSSEBytes {
			return nil, errors.New("model SSE exceeds decoding bound")
		}
		var compressed bytes.Buffer
		writer := gzip.NewWriter(&compressed)
		if _, err := writer.Write(raw); err != nil {
			return nil, err
		}
		if err := writer.Close(); err != nil {
			return nil, err
		}
		payload = Object{"status": result["status"], "content_type": result["content_type"], "body_encoding": "gzip+base64", "body_gzip_base64": base64.StdEncoding.EncodeToString(compressed.Bytes()), "body_sha256": Digest(raw)}
	}
	reply := Object{"sequence": frame.Sequence, "key": frame.Key, "state": receipt["state"], "payload": payload}
	if len(Bytes(reply)) > 64*1024 {
		return nil, errors.New("encoded effect reply exceeds bridge frame limit")
	}
	return reply, nil
}

func (c *RuntimeCoordinator) recordNotAppliedEffect(route RuntimeCoordinatorRoute, provider RuntimeProviderRoute, runID string, epoch int64, bridge *rt.Bridge, frame rt.BridgeFrame, intent, dispatch Object, code, reason string) (Object, error) {
	result := Object{"code": code, "reason": reason, "dispatched": false, "witness": "HOST_PRE_EFFECT_REFUSAL"}
	raw := Bytes(result)
	currency := Str(provider.UpperBound, "currency")
	if currency == "" {
		currency = "USD"
	}
	receipt := Object{"key": frame.Key, "epoch": epoch, "run_id": runID, "receipt_id": Digest(raw), "state": "NOT_APPLIED", "actual_cost": Object{"amount": "0", "currency": currency}, "payload": result}
	fact := Object{"version": 1, "project_id": route.ProjectID, "run_id": runID, "epoch": epoch, "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "effect_key": frame.Key, "request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "provider_response_hash": Digest(raw), "receipt": receipt}
	if err := writeRuntimeFact(filepath.Join(bridge.Directory(), "effect-"+strings.TrimPrefix(Digest([]byte(frame.Key)), "sha256:")+".json"), Bytes(fact)); err != nil {
		return nil, err
	}
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		return nil, err
	}
	return runtimeEffectWireReply(frame, receipt)
}
