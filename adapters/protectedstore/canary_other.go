//go:build !windows

package protectedstore

import "context"

type CanaryStore struct{}

func NewCanary(string) (*CanaryStore, error)                    { return nil, ErrUnavailable }
func (*CanaryStore) Close() error                               { return nil }
func (*CanaryStore) Boundary(context.Context) (Boundary, error) { return Boundary{}, ErrUnavailable }
func (*CanaryStore) Ready(context.Context, string) error        { return ErrUnavailable }
func (*CanaryStore) CreateCanary(context.Context, string, string, []byte) (Blob, error) {
	return Blob{}, ErrUnavailable
}
func (*CanaryStore) Describe(context.Context, string, string) (Blob, error) {
	return Blob{}, ErrUnavailable
}
func (*CanaryStore) Read(context.Context, Blob) ([]byte, error) { return nil, ErrUnavailable }
