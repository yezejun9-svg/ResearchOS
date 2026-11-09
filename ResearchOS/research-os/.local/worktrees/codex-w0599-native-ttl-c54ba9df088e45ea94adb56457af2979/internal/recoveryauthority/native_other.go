//go:build !windows

package recoveryauthority

import (
	"context"
	"errors"
)

type nativeSession struct{}

func (*nativeSession) check() error { return errors.New("AUTHORITY_WINDOWS_REQUIRED") }
func (*nativeSession) close() error { return nil }
func ReceiveInherited(context.Context) (Token, string, error) {
	return Token{}, "", errors.New("AUTHORITY_WINDOWS_REQUIRED")
}
func ReceiveMigrationInherited(context.Context) (MigrationToken, string, error) {
	return MigrationToken{}, "", errors.New("AUTHORITY_WINDOWS_REQUIRED")
}
