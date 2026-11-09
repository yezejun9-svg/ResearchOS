//go:build windows
package host
import("testing";"os";"path/filepath";"encoding/json";"researchos.local/research-os/internal/domain")
func TestIndependentActualRebuiltCandidateLoader(t *testing.T){
 root:=os.Getenv("RESEARCHOS_REVIEW_CANDIDATE_ROOT");if root==""{t.Fatal("explicit independent root required")}
 raw,e:=os.ReadFile(filepath.Join(root,"mu-worker.mjs.build.json"));if e!=nil{t.Fatal(e)}
 var m map[string]any;if json.Unmarshal(raw,&m)!=nil{t.Fatal("metadata")}
 node,e:=os.ReadFile(filepath.Join(root,"node.exe"));if e!=nil{t.Fatal(e)}
 p:=TrustedCandidatePolicy{AssetRoot:root,ManifestHash:"sha256:"+m["candidate_manifest_sha256"].(string),BundleHash:"sha256:"+m["bundle_sha256"].(string),SourceHash:"sha256:"+m["source_sha256"].(string),NodeHash:domain.Digest(node)}
 a,e:=LoadTrustedCandidateRuntimeSetupAssets(p);if e!=nil{t.Fatal(e)}
 if a.BundleHash!=p.BundleHash||a.BuildHash!=p.NodeHash||a.Executable!=filepath.Join(root,"node.exe"){t.Fatal("actual artifact binding")}
 if _,e=LoadRuntimeSetupAssets(root);e==nil{t.Fatal("legacy loader accepted candidate metadata")}
 p.BundleHash=domain.Digest([]byte("other"));if _,e=LoadTrustedCandidateRuntimeSetupAssets(p);e==nil{t.Fatal("changed policy accepted")}
 t.Logf("Actual independent bundle accepted by explicit candidate policy; legacy loader rejects; node=%s bundle=%s",a.BuildHash,a.BundleHash)
}
