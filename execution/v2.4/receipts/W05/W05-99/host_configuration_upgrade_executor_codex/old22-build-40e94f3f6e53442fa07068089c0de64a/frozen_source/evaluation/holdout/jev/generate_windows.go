//go:build windows

package jev

import (
	"crypto/rand"
	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/svc"
)

// GenerateProtected has no caller-supplied seed, path, task, rubric or label.
// The check happens before entropy is read and before any corpus is produced.
// It cannot be used interactively by an ordinary developer or another Agent.
func GenerateProtected() (Batch, error) {
	if e := requireProtectedIdentity(); e != nil {
		return Batch{}, e
	}
	var seed [32]byte
	if _, e := rand.Read(seed[:]); e != nil {
		return Batch{}, ErrCorpus
	}
	return generate(seed, ProtectedSplit)
}

func requireProtectedIdentity() error {
	service, e := svc.IsWindowsService()
	if e != nil || !service {
		return ErrProtectedIdentity
	}
	sid, _, _, e := windows.LookupSID("", `NT SERVICE\`+ServiceName)
	user, err := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil || err != nil || user.User.Sid.String() != sid.String() {
		return ErrProtectedIdentity
	}
	return nil
}
