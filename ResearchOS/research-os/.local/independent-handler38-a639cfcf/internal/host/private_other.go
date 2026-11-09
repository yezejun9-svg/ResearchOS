//go:build !windows

package host

import "errors"

var errNoSID = errors.New("no OS principal SID available")

// privateDir and privateFile refuse rather than degrading to 0700-only semantics: the product
// host is Windows, and a platform that cannot prove current-user isolation must not claim the
// protected boundary this card is about.
func privateDir(string) error  { return errNoSID }
func privateFile(string) error { return errNoSID }
