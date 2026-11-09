// Fixture-only explicit observation of a repeat real Host.New on a task-owned root.
package main
import (
  "encoding/json"
  "fmt"
  "os"
  "path/filepath"
  "researchos.local/research-os/internal/host"
  "researchos.local/research-os/internal/store"
)
func main() {
  if len(os.Args)!=3 { fmt.Fprintln(os.Stderr,"usage: host_probe <fixture-data-root> <pinned-repo>"); os.Exit(2) }
  data,repo:=os.Args[1],os.Args[2]
  db,err:=store.Open(filepath.Join(data,"researchos.sqlite")); if err!=nil { fmt.Fprintln(os.Stderr,err); os.Exit(1) }; defer db.Close()
  h,err:=host.New(host.Config{DB:db,Dir:filepath.Join(data,"host"),ContractsDir:filepath.Join(repo,"spec","v2.0","contracts"),MigrationFile:filepath.Join(repo,"migrations","sqlite","0002_domain.sql"),SchemaDir:filepath.Join(repo,"internal","api","contracts")})
  if err!=nil { fmt.Fprintln(os.Stderr,err); os.Exit(1) }
  _=json.NewEncoder(os.Stdout).Encode(map[string]any{"status":"HOST_NEW_OK","root_count":len(h.Roots())})
}
