//go:build !windows

package protectedstore

import "context"

type FrozenProvider struct{}

func (*FrozenProvider) Boundary(context.Context) (Boundary, error) { return Boundary{}, ErrUnavailable }
func (*FrozenProvider) Ready(context.Context, string) error        { return ErrUnavailable }
func (*FrozenProvider) Describe(context.Context, string, string) (Blob, error) {
	return Blob{}, ErrUnavailable
}
func (*FrozenProvider) Read(context.Context, Blob) ([]byte, error) { return nil, ErrIsolation }
func QueryFrozenService(string) (SafeSummary, error)               { return SafeSummary{}, ErrUnavailable }
