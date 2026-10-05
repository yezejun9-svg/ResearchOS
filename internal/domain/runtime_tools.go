package domain

// RuntimeToolRequest is an in-process host port. WorkspacePath and Policy are
// resolved from current session authority and frozen profile, never child input.
type RuntimeToolRequest struct {
	WorkspacePath string
	Access        string
	Name          string
	Arguments     Object
	Policy        Object
}
