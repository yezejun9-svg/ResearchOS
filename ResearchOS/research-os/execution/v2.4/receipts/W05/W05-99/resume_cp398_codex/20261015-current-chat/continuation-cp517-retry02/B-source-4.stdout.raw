//go:build windows

package runtime

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"os"
	"os/user"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/canonical"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

const qualificationRejectionFile = "qualification-rejection-00000000000000000003.json"

// qualificationPrivateDirectory checks an existing dispatch directory. A proof
// cannot make an already permissive or redirected directory trustworthy.
func qualificationPrivateDirectory(directory string) error {
	if !filepath.IsAbs(directory) {
		return errors.New("absolute qualification dispatch directory required")
	}
	clean := filepath.Clean(directory)
	for path := clean; ; path = filepath.Dir(path) {
		resolved, err := filepath.EvalSymlinks(path)
		if err != nil || !strings.EqualFold(filepath.Clean(resolved), path) {
			return errors.New("qualification directory has reparse ancestry")
		}
		if next := filepath.Dir(path); next == path {
			break
		}
	}
	info, err := os.Stat(clean)
	if err != nil || !info.IsDir() {
		return errors.New("qualification dispatch directory unavailable")
	}
	current, err := user.Current()
	if err != nil {
		return err
	}
	sd, err := windows.GetNamedSecurityInfo(clean, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION)
	if err != nil {
		return err
	}
	acl := sd.String()
	if !strings.Contains(acl, "D:P") || !strings.Contains(acl, current.Uid) {
		return errors.New("qualification dispatch directory is not private")
	}
	return nil
}

// PersistQualificationRejection is a create-new durable host fact, not a
// success flag. The domain gate holds its write reservation until this returns.
func PersistQualificationRejection(directory string, raw []byte) error {
	if len(raw) == 0 || len(raw) > 64*1024 {
		return errors.New("qualification rejection exceeds bound")
	}
	if err := qualificationPrivateDirectory(directory); err != nil {
		return err
	}
	path := filepath.Join(directory, qualificationRejectionFile)
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	n, writeErr := f.Write(raw)
	if writeErr == nil && n != len(raw) {
		writeErr = io.ErrShortWrite
	}
	err = errors.Join(writeErr, f.Sync(), f.Close())
	if err != nil {
		return err
	}
	return qualificationPrivateDirectory(directory)
}

// QualificationNativeFacts contains bounded source facts only. Callers must
// still validate the domain subject and effect/transaction history.
type QualificationNativeFacts struct {
	Journal        BridgeJournal
	RawJournalHash string
	StdoutHash     string
	StderrHash     string
	Frames         []BridgeFrame
	FrameHashes    []string
	AuxAfterThird  bool
	Rejection      []byte
}

func ReadQualificationNativeFacts(directory, manifestHash string) (QualificationNativeFacts, error) {
	var facts QualificationNativeFacts
	if err := qualificationPrivateDirectory(directory); err != nil {
		return facts, err
	}
	j, err := ReadBridgeTerminal(directory, manifestHash)
	if err != nil {
		return facts, err
	}
	if !j.Receipt.Stopped || !j.Receipt.StreamsDrained || !j.Receipt.CleanupComplete || !j.Receipt.OutputCopied || j.Ended == "" {
		return facts, errors.New("native qualification closure incomplete")
	}
	journalRaw, err := os.ReadFile(filepath.Join(directory, "bridge.json"))
	if err != nil || len(journalRaw) > 4*1024*1024 {
		return facts, errors.New("bounded native journal unavailable")
	}
	stdout, err := os.ReadFile(filepath.Join(directory, "stdout.raw"))
	if err != nil || len(stdout) > sandbox.MaxStreamBytes || Hash(stdout) != j.StdoutHash {
		return facts, errors.New("qualification stdout changed")
	}
	stderr, err := os.ReadFile(filepath.Join(directory, "stderr.raw"))
	if err != nil || len(stderr) > sandbox.MaxStreamBytes || Hash(stderr) != j.StderrHash {
		return facts, errors.New("qualification stderr changed")
	}
	rejection, err := os.ReadFile(filepath.Join(directory, qualificationRejectionFile))
	if err != nil || len(rejection) == 0 || len(rejection) > 64*1024 {
		return facts, errors.New("immutable qualification rejection unavailable")
	}
	for _, line := range bytes.Split(stdout, []byte{'\n'}) {
		if len(line) == 0 {
			continue
		}
		if len(line) > 64*1024 {
			return facts, errors.New("qualification frame exceeds bound")
		}
		canonicalLine, err := canonical.JSON(line)
		if err != nil {
			return facts, err
		}
		var shape map[string]json.RawMessage
		if err = json.Unmarshal(canonicalLine, &shape); err != nil {
			return facts, err
		}
		if _, auxiliary := shape["version"]; auxiliary {
			if len(facts.Frames) >= 3 {
				facts.AuxAfterThird = true
			}
			continue
		}
		var frame BridgeFrame
		// Preserve the payload bytes consumed by Bridge. Normalizing the line
		// changes RawMessage whitespace and breaks first-gate byte lineage.
		if err = json.Unmarshal(line, &frame); err != nil {
			return facts, err
		}
		facts.Frames = append(facts.Frames, frame)
		facts.FrameHashes = append(facts.FrameHashes, Hash(line))
	}
	facts.Journal = j
	facts.RawJournalHash = Hash(journalRaw)
	facts.StdoutHash = Hash(stdout)
	facts.StderrHash = Hash(stderr)
	facts.Rejection = rejection
	return facts, nil
}
