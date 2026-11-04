package main

import (
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
	"unicode/utf8"
)

const cliPromptMaxRunes = 16384
const cliPromptMaxFileBytes = 65536

// cliPromptText is local, validated input, never an authorization or write capability.
// Text crosses the normal authenticated HTTP protocol only as session.send.text.
type cliPromptText struct{ text string }
type cliPromptProblem struct {
	code           int
	reason, detail string
}

var cliPromptHostFlags = map[string]bool{
	"project": true, "session": true, "output": true,
	"expected-revision": true, "writer-epoch": true, "after-sequence": true,
}
var cliPromptLegacyValueFlags = map[string]bool{
	"dir": true, "file": true, "replace": true, "check": true, "repairs": true, "workspace": true,
	"job": true, "queue": true, "tick-file": true, "exe": true, "cancel-after": true, "settle": true, "observe-after": true,
}

func cliPromptOption(token string) (name, value string, equals bool) {
	name, value, equals = strings.Cut(strings.TrimPrefix(strings.TrimPrefix(token, "-"), "-"), "=")
	return
}

// Respect the old flag parser's value arity. A legacy value literally equal to
// --prompt is still a value, not permission to replace that invocation's mode.
func explicitCLIPromptRequested(args []string) bool {
	for i := 0; i < len(args); i++ {
		token := args[i]
		if token == "--" {
			return false
		}
		if !strings.HasPrefix(token, "-") {
			continue
		}
		name, _, equals := cliPromptOption(token)
		if strings.HasPrefix(token, "--") && (name == "prompt" || name == "prompt-file") {
			return true
		}
		if !equals && i+1 < len(args) {
			if cliPromptLegacyValueFlags[name] || cliPromptHostFlags[name] && !strings.HasPrefix(args[i+1], "--") {
				i++
			}
		}
	}
	return false
}

func cliPromptError(reason, detail string) *cliPromptProblem {
	return &cliPromptProblem{exitUsage, reason, detail}
}

func validateCLIPrompt(text string) *cliPromptProblem {
	if !utf8.ValidString(text) {
		return cliPromptError("PROMPT_INVALID_UTF8", "prompt must be valid UTF-8")
	}
	if strings.TrimSpace(text) == "" {
		return cliPromptError("PROMPT_EMPTY", "prompt must contain non-whitespace text")
	}
	if utf8.RuneCountInString(text) > cliPromptMaxRunes {
		return cliPromptError("PROMPT_TOO_LARGE", "prompt exceeds 16384 Unicode characters")
	}
	return nil
}

func readCLIPrompt(reader io.Reader) (string, *cliPromptProblem) {
	raw, err := io.ReadAll(io.LimitReader(reader, cliPromptMaxFileBytes+1))
	if err != nil {
		return "", &cliPromptProblem{exitFailed, "PROMPT_FILE_UNREADABLE", "cannot read prompt file"}
	}
	if len(raw) > cliPromptMaxFileBytes {
		return "", cliPromptError("PROMPT_FILE_TOO_LARGE", "prompt file exceeds 65536 bytes")
	}
	text := string(raw)
	if problem := validateCLIPrompt(text); problem != nil {
		return "", problem
	}
	return text, nil
}

func readCLIPromptFile(path string) (string, *cliPromptProblem) {
	file, err := os.Open(path)
	if err != nil {
		return "", &cliPromptProblem{exitFailed, "PROMPT_FILE_UNREADABLE", "cannot open prompt file"}
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() {
		return "", cliPromptError("PROMPT_FILE_NOT_REGULAR", "prompt file must be a regular file")
	}
	// Read a bounded snapshot once; do not re-open the file after Host admission.
	return readCLIPrompt(file)
}

// No discovery, credentials, HTTP, worker, or local check runs during parsing.
// Legacy-shaped invocations are returned untouched for their existing handler.
func parseExplicitCLIPrompt(args []string) (*cliPromptText, []string, *cliPromptProblem) {
	if !explicitCLIPromptRequested(args) {
		return nil, args, nil
	}
	hostArgs := []string{}
	source, value := "", ""
	seen := map[string]bool{}
	for i := 0; i < len(args); i++ {
		token := args[i]
		if !strings.HasPrefix(token, "--") || token == "--" {
			return nil, nil, cliPromptError("PROMPT_ARGUMENT_CONFLICT", "explicit prompt mode accepts only its prompt source and supported Host flags")
		}
		name, v, equals := cliPromptOption(token)
		if name != "prompt" && name != "prompt-file" && !cliPromptHostFlags[name] {
			return nil, nil, cliPromptError("PROMPT_ARGUMENT_UNSUPPORTED", "unsupported or legacy flag in explicit prompt mode")
		}
		if seen[name] {
			return nil, nil, cliPromptError("PROMPT_ARGUMENT_DUPLICATE", "an explicit prompt option was repeated")
		}
		seen[name] = true
		isSource := name == "prompt" || name == "prompt-file"
		if isSource && source != "" {
			return nil, nil, cliPromptError("PROMPT_SOURCE_CONFLICT", "--prompt and --prompt-file are mutually exclusive")
		}
		if !equals {
			if i+1 >= len(args) || !isSource && strings.HasPrefix(args[i+1], "--") {
				return nil, nil, cliPromptError("PROMPT_OPTION_VALUE_REQUIRED", "an explicit prompt option requires a value")
			}
			i++
			v = args[i]
		}
		if v == "" {
			return nil, nil, cliPromptError("PROMPT_OPTION_VALUE_REQUIRED", "an explicit prompt option requires a nonempty value")
		}
		if isSource {
			source, value = name, v
			continue
		}
		if name == "output" && v != "jsonl" {
			return nil, nil, cliPromptError("OUTPUT_FORMAT_UNSUPPORTED", "--output accepts only jsonl")
		}
		if name == "expected-revision" || name == "writer-epoch" || name == "after-sequence" {
			n, err := strconv.ParseInt(v, 10, 64)
			if err != nil || n < 0 {
				return nil, nil, cliPromptError("PROMPT_HOST_VALUE_INVALID", "revision, epoch and sequence must be exact nonnegative int64 protocol integers")
			}
		}
		hostArgs = append(hostArgs, "--"+name+"="+v)
	}
	if source == "prompt-file" {
		text, problem := readCLIPromptFile(value)
		if problem != nil {
			return nil, nil, problem
		}
		value = text
	} else if problem := validateCLIPrompt(value); problem != nil {
		return nil, nil, problem
	}
	return &cliPromptText{text: value}, hostArgs, nil
}

func taskDispatch(args []string) {
	prompt, hostArgs, problem := parseExplicitCLIPrompt(args)
	if problem != nil {
		fail("task", problem.code, problem.reason, problem.detail)
	}
	if prompt == nil {
		runCodingTask(args)
		return
	}
	cliHostCommandWithPrompt("task", hostArgs, prompt)
}

// The format is intentionally independent of prompt text, which can contain flags.
func (p *cliPromptProblem) Error() string { return fmt.Sprintf("%s: %s", p.reason, p.detail) }
