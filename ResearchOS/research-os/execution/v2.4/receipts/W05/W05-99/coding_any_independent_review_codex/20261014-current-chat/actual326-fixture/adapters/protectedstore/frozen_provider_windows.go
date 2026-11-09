//go:build windows

package protectedstore

import "context"

// FrozenProvider exposes only the fixed service descriptor. Project mapping is
// host registration metadata; it grants no arbitrary service path or body read.
type FrozenProvider struct{}

func (*FrozenProvider) terminal(ctx context.Context) (SafeSummary, error) {
	if ctx.Err() != nil {
		return SafeSummary{}, ErrUnavailable
	}
	s, err := QueryFrozenService("aggregate")
	if err != nil {
		return SafeSummary{}, err
	}
	if ctx.Err() != nil || s.Frozen == nil || s.Frozen.RunState != "COMPLETED" || s.Frozen.Dataset == nil || s.Frozen.Dataset.MeasurementMode != "LIVE" {
		return SafeSummary{}, ErrUnavailable
	}
	return s, nil
}
func (p *FrozenProvider) Boundary(ctx context.Context) (Boundary, error) {
	if _, err := p.terminal(ctx); err != nil {
		return Boundary{}, err
	}
	return Boundary{Mode: "INDEPENDENT_VERIFIER", OwnerSID: "S-1-5-80-2827915021-3673354303-1056739677-2648886565-40618300", IndependentIdentity: true, UnrestrictedSameUserCanRead: false}, nil
}
func (p *FrozenProvider) Ready(ctx context.Context, mode string) error {
	if mode != "LIVE" {
		return ErrBoundary
	}
	_, err := p.terminal(ctx)
	return err
}
func (p *FrozenProvider) Describe(ctx context.Context, project, ticket string) (Blob, error) {
	if project == "" || !ValidTicket(ticket) {
		return Blob{}, ErrBoundary
	}
	s, err := p.terminal(ctx)
	if err != nil {
		return Blob{}, err
	}
	blob := *s.Frozen.Dataset
	if blob.Ticket != ticket {
		return Blob{}, ErrNotFound
	}
	blob.Project = project
	return blob, nil
}
func (*FrozenProvider) Read(context.Context, Blob) ([]byte, error) { return nil, ErrIsolation }
