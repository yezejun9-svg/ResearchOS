//go:build windows

package sandbox

import (
	"bytes"
	"context"
	"errors"
	"io"
	"os"
	"sync"
	"time"
)

const MaxStreamBytes = 4 * 1024 * 1024

// Identity is collected by the host while the process is still suspended.
// BeforeResume must durably bind it to the admitted dispatch before returning.
type Identity struct {
	PID              uint32 `json:"pid"`
	Created          int64  `json:"process_created_ns,string"`
	Job              string `json:"job"`
	SID              string `json:"appcontainer_sid"`
	Profile          string `json:"profile"`
	StagingDirectory string `json:"staging_directory"`
}

type StreamChunk struct {
	Stream string `json:"stream"`
	Offset int64  `json:"offset"`
	Data   []byte `json:"data"`
}

type StartOptions struct {
	BeforeResume func(Identity) error
	// OnStream must consume bounded chunks promptly. An error stops the Job;
	// the final receipt never treats a lost or truncated stream as drained.
	OnStream    func(StreamChunk) error
	Interactive bool
	// AllowCodingTurnTimeout is reserved for the trusted Mu coding bridge.
	// It raises only the per-process upper bound from 5 to 15 minutes;
	// Run and ordinary Start calls retain the 5-minute default.
	AllowCodingTurnTimeout bool
}

type Process struct {
	mu        sync.Mutex
	writeGate chan struct{}
	stopped   <-chan struct{}
	stdin     *os.File
	cancel    context.CancelFunc
	done      chan struct{}
	ready     chan error
	receipt   Receipt
	err       error
}

// Start returns after suspended identity persistence and ResumeThread succeed.
// It owns process termination, stream draining and staging cleanup until Wait.
func Start(ctx context.Context, c Command, options StartOptions) (*Process, error) {
	child, cancel := context.WithCancel(ctx)
	p := &Process{cancel: cancel, done: make(chan struct{}), ready: make(chan error, 1), writeGate: make(chan struct{}, 1), stopped: child.Done()}
	go func() {
		r, err := runSandbox(child, c, options, p)
		p.mu.Lock()
		p.receipt, p.err = r, err
		if p.stdin != nil {
			p.stdin.Close()
			p.stdin = nil
		}
		p.mu.Unlock()
		select {
		case p.ready <- err:
		default:
		}
		cancel()
		close(p.done)
	}()
	select {
	case err := <-p.ready:
		if err != nil {
			<-p.done
			return nil, err
		}
		return p, nil
	case <-ctx.Done():
		cancel()
		// The caller receives no Process handle on startup failure. Keep this
		// boundary until termination, stream closure and staging cleanup finish.
		<-p.done
		return nil, ctx.Err()
	}
}

func (p *Process) Write(ctx context.Context, frame []byte) error {
	if len(frame) == 0 || len(frame) > 64*1024 {
		return errors.New("bounded protocol frame required")
	}
	bounded, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if err := bounded.Err(); err != nil {
		return err
	}
	select {
	case p.writeGate <- struct{}{}:
	case <-bounded.Done():
		return bounded.Err()
	case <-p.stopped:
		return errors.New("process input closed")
	case <-p.done:
		return errors.New("process completed")
	}
	defer func() { <-p.writeGate }()
	if err := bounded.Err(); err != nil {
		return err
	}
	select {
	case <-p.stopped:
		return errors.New("process input closed")
	default:
	}
	frame = append([]byte(nil), frame...)
	p.mu.Lock()
	f := p.stdin
	p.mu.Unlock()
	if f == nil {
		return errors.New("process input closed")
	}
	// Windows anonymous pipes are synchronous and reject SetWriteDeadline.
	// On timeout cancel the Job, which closes the child's read handle and
	// releases this one pending write; never continue the protocol afterwards.
	done := make(chan error, 1)
	go func() {
		n, err := f.Write(frame)
		if err == nil && n != len(frame) {
			err = io.ErrShortWrite
		}
		done <- err
	}()
	select {
	case err := <-done:
		return err
	case <-bounded.Done():
		p.cancel()
		return bounded.Err()
	case <-p.stopped:
		return errors.New("process input closed")
	}
}

func (p *Process) CloseInput() error {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.stdin == nil {
		return nil
	}
	err := p.stdin.Close()
	p.stdin = nil
	return err
}

func (p *Process) Cancel() { p.cancel(); p.CloseInput() }

func (p *Process) Wait(ctx context.Context) (Receipt, error) {
	select {
	case <-p.done:
		p.mu.Lock()
		defer p.mu.Unlock()
		return p.receipt, p.err
	case <-ctx.Done():
		return Receipt{}, ctx.Err()
	}
}

type streamResult struct {
	bytes []byte
	err   error
}

func collectStream(reader *os.File, name string, callback func(StreamChunk) error, cancel context.CancelFunc, result chan<- streamResult) {
	defer reader.Close()
	var captured bytes.Buffer
	buffer := make([]byte, 16*1024)
	for {
		n, err := reader.Read(buffer)
		if n > 0 {
			if captured.Len()+n > MaxStreamBytes {
				cancel()
				result <- streamResult{captured.Bytes(), errors.New(name + " stream limit exceeded")}
				return
			}
			offset := captured.Len()
			captured.Write(buffer[:n])
			if callback != nil {
				if e := callback(StreamChunk{Stream: name, Offset: int64(offset), Data: append([]byte(nil), buffer[:n]...)}); e != nil {
					cancel()
					result <- streamResult{captured.Bytes(), e}
					return
				}
			}
		}
		if err != nil {
			capturedBytes := captured.Bytes()
			if errors.Is(err, io.EOF) {
				err = nil
				if capturedBytes == nil {
					capturedBytes = []byte{}
				}
			} else {
				cancel()
			}
			result <- streamResult{capturedBytes, err}
			return
		}
	}
}
