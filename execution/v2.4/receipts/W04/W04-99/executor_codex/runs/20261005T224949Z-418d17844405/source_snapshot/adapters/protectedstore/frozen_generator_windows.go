//go:build windows

package protectedstore

import (
	"context"
	"net/http"
	"researchos.local/research-os/adapters/decision"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
	"time"
)

func protectedGenerator() frozenGenerator {
	convert := func(batch holdout.Batch) (frozenBatch, error) {
		if batch.Split != holdout.ProtectedSplit || holdout.Validate(batch) != nil {
			return frozenBatch{}, ErrIntegrity
		}
		out := frozenBatch{Raw: decision.Encode(batch)}
		for _, c := range batch.Cases {
			out.Cases = append(out.Cases, frozenCase{ID: c.ID, Scope: c.Scope, Request: c.Request, Expected: c.Expected, Critical: c.Critical})
		}
		return out, nil
	}
	return frozenGenerator{
		Generate: func() (frozenBatch, error) {
			batch, e := holdout.GenerateProtected()
			if e != nil {
				return frozenBatch{}, ErrIsolation
			}
			return convert(batch)
		},
		Restore: func(raw []byte) (frozenBatch, error) {
			var batch holdout.Batch
			if decision.Strict(raw, &batch) != nil {
				return frozenBatch{}, ErrIntegrity
			}
			return convert(batch)
		},
	}
}

func serviceCallFactory(store *CanaryStore) func() (frozenCall, error) {
	return func() (frozenCall, error) {
		token, e := store.loadServiceCredential()
		if e != nil {
			return nil, e
		}
		defer wipe(token)
		transport := http.DefaultTransport.(*http.Transport).Clone()
		transport.DisableKeepAlives = true // Each budget slot uses a fresh connection; no reused-connection replay.
		transport.Proxy = nil              // No environment-selected proxy or alternate endpoint.
		client := decision.Client{Token: string(token), URL: decision.Endpoint, Timeout: 60 * time.Second, HTTP: &http.Client{Transport: transport}}
		return func(ctx context.Context, b decision.Binding, r decision.Request) (decision.Envelope, error) {
			return client.Call(ctx, b, r)
		}, nil
	}
}
