//go:build !windows

package jev

func GenerateProtected() (Batch, error) { return Batch{}, ErrProtectedIdentity }

func requireProtectedIdentity() error { return ErrProtectedIdentity }
