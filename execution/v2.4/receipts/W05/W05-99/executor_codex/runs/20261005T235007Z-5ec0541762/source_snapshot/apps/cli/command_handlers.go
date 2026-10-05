package main

// commandHandlers lets a platform-specific file add CLI verbs without the shared entry point naming
// symbols that only compile on one OS. A verb nobody registered still falls through to the existing
// NOT_IMPLEMENTED refusal with exit 3, so an unavailable platform can never invent a success.
var commandHandlers = map[string]func([]string){}
