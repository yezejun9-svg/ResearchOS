package domain

import "context"

// RuntimeToolRequest is an in-process host port. WorkspacePath and Policy are
// resolved from current session authority and frozen profile, never child input.
type RuntimeToolRequest struct {
	WorkspacePath string
	Access        string
	Name          string
	Arguments     Object
	Policy        Object
	IntentKey     string
	Revalidate    func(context.Context) error
}

// RuntimeToolFailure is a host witness, never a model-provided claim. Only a
// failure proved to precede side effects may carry NOT_APPLIED. Unclassified
// errors remain UNKNOWN at the broker boundary.
type RuntimeToolFailure struct {
	Err     error
	Outcome string
}

func (e *RuntimeToolFailure) Error() string { return e.Err.Error() }
func (e *RuntimeToolFailure) Unwrap() error { return e.Err }
