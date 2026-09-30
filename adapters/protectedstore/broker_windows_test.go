//go:build windows

package protectedstore

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

func TestCanaryReopen(t *testing.T) {
	root := filepath.Join(t.TempDir(), "private")
	s, e := NewCanary(root)
	if e != nil {
		t.Fatal(e)
	}
	blob, e := s.CreateCanary(context.Background(), "synthetic", "text/plain", []byte("reopen canary"))
	if e != nil {
		t.Fatal(e)
	}
	s.Close()
	s, e = OpenCanary(root)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	b, e := s.Read(context.Background(), blob)
	if e != nil || string(b) != "reopen canary" {
		t.Fatal("restart body mismatch", e)
	}
	fmt.Println("BROKER_ASSERTION REOPEN_CURRENT_IDENTITY PASS CANARY_ONLY")
}

func TestCanaryServiceRejectsInteractive(t *testing.T) {
	if RunCanaryService("S-1-5-21-1-2-3-1001") == nil {
		t.Fatal("interactive service allowed")
	}
	fmt.Println("BROKER_ASSERTION INTERACTIVE_SERVICE_REFUSED PASS CANARY_ONLY")
}

func TestCanaryExplicitReaderRights(t *testing.T) {
	user, e := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil {
		t.Fatal(e)
	}
	name := fmt.Sprintf(`\\.\pipe\ResearchOSExplicitReader-%d-%d`, os.Getpid(), time.Now().UnixNano())
	// A service SID owns the full-access ACE, so the current reader cannot
	// accidentally succeed via the full-access identity used by other fixtures.
	sd, e := windows.SecurityDescriptorFromString("D:P(A;;FA;;;S-1-5-80-2827915021-3673354303-1056739677-2648886565-40618300)(A;;" + pipeClientACL + ";;;" + user.User.Sid.String() + ")")
	if e != nil {
		t.Fatal(e)
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	mode := uint32(windows.PIPE_TYPE_MESSAGE | windows.PIPE_READMODE_MESSAGE | windows.PIPE_NOWAIT | windows.PIPE_REJECT_REMOTE_CLIENTS)
	h, e := windows.CreateNamedPipe(windows.StringToUTF16Ptr(name), windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE, mode, 2, 4096, 64, 0, &sa)
	if e != nil {
		t.Fatal(e)
	}
	defer windows.CloseHandle(h)
	client, e := windows.CreateFile(windows.StringToUTF16Ptr(name), pipeClientRights, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED|windows.SECURITY_SQOS_PRESENT|windows.SECURITY_IDENTIFICATION, 0)
	if e != nil {
		t.Fatal("explicit reader could not open client endpoint", e)
	}
	windows.CloseHandle(client)
	second, e := windows.CreateNamedPipe(windows.StringToUTF16Ptr(name), windows.PIPE_ACCESS_DUPLEX, mode, 2, 4096, 64, 0, &sa)
	if e == nil {
		windows.CloseHandle(second)
		t.Fatal("reader could create a server instance")
	}
	if e != windows.ERROR_ACCESS_DENIED {
		t.Fatal("instance refusal was not the access boundary", e)
	}
	fmt.Println("BROKER_ASSERTION EXPLICIT_READER_OPENS_WITHOUT_SERVER_AUTHORITY PASS CANARY_ONLY")
}

func TestCanaryProbeUnresponsiveServer(t *testing.T) {
	name := fmt.Sprintf(`\\.\pipe\ResearchOSCanarySilentTest-%d-%d`, os.Getpid(), time.Now().UnixNano())
	h, e := windows.CreateNamedPipe(windows.StringToUTF16Ptr(name), windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE, windows.PIPE_TYPE_MESSAGE|windows.PIPE_READMODE_MESSAGE|windows.PIPE_NOWAIT|windows.PIPE_REJECT_REMOTE_CLIENTS, 1, 4096, 64, 0, nil)
	if e != nil {
		t.Fatal(e)
	}
	defer windows.CloseHandle(h)
	// This actual native server exists and accepts the client; it deliberately
	// never reads a request, emits a response or closes to rescue the client.
	client, e := windows.CreateFile(windows.StringToUTF16Ptr(name), pipeClientRights, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED|windows.SECURITY_SQOS_PRESENT|windows.SECURITY_IDENTIFICATION, 0)
	if e != nil {
		t.Fatal(e)
	}
	file := os.NewFile(uintptr(client), "silent-canary-pipe")
	defer file.Close()
	started := time.Now()
	_, e = requestCanarySummary(file, started.Add(75*time.Millisecond))
	elapsed := time.Since(started)
	if e == nil || elapsed < 50*time.Millisecond || elapsed > time.Second {
		t.Fatalf("deadline failed err=%v elapsed=%s", e, elapsed)
	}
	fmt.Println("BROKER_ASSERTION UNRESPONSIVE_SERVER_TIMEOUT PASS CANARY_ONLY")
}

func TestCanaryBrokerProtocol(t *testing.T) {
	for _, scenario := range []string{"summary", "invalid-request", "body-drift"} {
		t.Run(scenario, func(t *testing.T) {
			s, e := NewCanary(filepath.Join(t.TempDir(), "private"))
			if e != nil {
				t.Fatal(e)
			}
			defer s.Close()
			for _, name := range brokerFiles {
				if e = s.createFile(name, []byte("SYNTHETIC_SERVICE_CANARY_"+name)); e != nil {
					t.Fatal(e)
				}
			}
			if scenario == "body-drift" {
				if e = os.WriteFile(filepath.Join(s.root, brokerFiles[0]), []byte("tampered"), 0600); e != nil {
					t.Fatal(e)
				}
			}
			summary := SafeSummary{Schema: "researchos.protected-summary.v1", Status: "EXECUTION_REPORTED", Total: 4, Correct: 4, MaximumMode: "ADVISORY"}
			boundary, _ := s.Boundary(context.Background())
			sd, e := windows.SecurityDescriptorFromString("D:P(A;;FA;;;" + boundary.OwnerSID + ")")
			if e != nil {
				t.Fatal(e)
			}
			sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
			name := fmt.Sprintf(`\\.\pipe\ResearchOSCanaryTest-%d-%d`, os.Getpid(), time.Now().UnixNano())
			h, e := windows.CreateNamedPipe(windows.StringToUTF16Ptr(name), windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE, windows.PIPE_TYPE_MESSAGE|windows.PIPE_READMODE_MESSAGE|windows.PIPE_NOWAIT|windows.PIPE_REJECT_REMOTE_CLIENTS, 1, 4096, 64, 0, &sa)
			if e != nil {
				t.Fatal(e)
			}
			defer windows.CloseHandle(h)
			ctx, cancel := context.WithCancel(context.Background())
			done := make(chan struct{})
			go func() { defer close(done); serveCanaryPipe(ctx, h, summary, s) }()
			defer func() { cancel(); <-done }()
			client, e := windows.CreateFile(windows.StringToUTF16Ptr(name), pipeClientRights, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED|windows.SECURITY_SQOS_PRESENT|windows.SECURITY_IDENTIFICATION, 0)
			if e != nil {
				t.Fatal(e)
			}
			file := os.NewFile(uintptr(client), "protocol-canary-pipe")
			defer file.Close()
			if scenario == "invalid-request" {
				if e = file.SetDeadline(time.Now().Add(time.Second)); e != nil {
					t.Fatal(e)
				}
				if _, e = file.Write([]byte("read-private")); e != nil {
					t.Fatal(e)
				}
				buffer := make([]byte, 4096)
				n, e := file.Read(buffer)
				if e == nil || n != 0 {
					t.Fatal("arbitrary request accepted")
				}
			} else {
				result, e := requestCanarySummary(file, time.Now().Add(time.Second))
				if e != nil {
					t.Fatal(e)
				}
				if scenario == "body-drift" {
					if result.Status != "BLOCKED" || result.Total != 0 {
						t.Fatal("stale aggregate returned")
					}
				} else if result != summary {
					t.Fatal("summary mismatch")
				}
			}
			fmt.Println("BROKER_ASSERTION", scenario, "PASS CANARY_ONLY")
		})
	}
}
