//go:build windows

package host

import (
	"context"
	"errors"
	"go/ast"
	"go/build"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"researchos.local/research-os/internal/domain"
)

// FreezeRuntimeCoding performs only bounded local reads. It never invokes Go,
// a shell, a model, a chooser, or a test program. Missing inputs are named and
// rejected, not discovered into a wider authorization behind the user's back.
func (h *Host) FreezeRuntimeCoding(ctx context.Context, b domain.WorkspaceBinding, in domain.RuntimeCodingIntent) (domain.Object, error) {
	if e := domain.ValidateRuntimeCodingIntent(in); e != nil {
		return nil, e
	}
	if _, e := h.reverify(); e != nil {
		return nil, e
	}
	if b.Access != AccessReadWrite || b.Status != domain.WorkspaceActive || b.AuthorizedRef != in.WorkspaceRef || b.PrincipalID != h.boundPrincipal() {
		return nil, toolDenied("coding scope is not the current Owner READ_WRITE workspace")
	}
	var binding *RootBinding
	for _, candidate := range h.roots.List() {
		if candidate.RealPath == b.RealPath {
			if binding != nil || candidate.Revoked || candidate.Access != AccessReadWrite {
				return nil, toolDenied("coding root is revoked, ambiguous or read-only")
			}
			binding = candidate
		}
	}
	if binding == nil {
		return nil, ErrRootUnknown
	}
	root, e := os.OpenRoot(binding.RealPath)
	if e != nil {
		return nil, e
	}
	defer root.Close()
	reads, writes := map[string]bool{}, map[string]bool{}
	for _, p := range in.ReadPaths {
		if CheckRelativePath(p) != nil || NormalizeRelative(p) != p {
			return nil, toolDenied("canonical coding read path required")
		}
		reads[p] = true
	}
	for _, p := range in.WritePaths {
		if !reads[p] || CheckRelativePath(p) != nil || NormalizeRelative(p) != p {
			return nil, toolDenied("canonical coding write path must also be explicitly readable")
		}
		writes[p] = true
	}
	initial := domain.Empty()
	var bytes int64
	for _, p := range in.ReadPaths {
		access := AccessReadOnly
		if writes[p] {
			access = AccessReadWrite
		}
		if _, e = h.ResolveWorkspace(binding.Ref, p, access); e != nil {
			return nil, e
		}
		if e = runtimeToolPlainPath(root, p, writes[p]); e != nil {
			return nil, e
		}
		raw, err := runtimeToolBytes(root, p)
		if errors.Is(err, fs.ErrNotExist) && writes[p] {
			initial = append(initial, domain.Object{"path": p, "sha256": nil, "size_bytes": 0})
			continue
		}
		if err != nil {
			return nil, err
		}
		bytes += int64(len(raw))
		if bytes > 32<<20 {
			return nil, toolDenied("coding read snapshot exceeds 32 MiB")
		}
		initial = append(initial, domain.Object{"path": p, "sha256": domain.Digest(raw), "size_bytes": len(raw)})
	}
	policy := domain.Object{"max_calls": in.MaxToolCalls, "read_paths": in.ReadPaths, "write_paths": in.WritePaths, "max_read_bytes": in.MaxReadBytes, "max_write_bytes": in.MaxWriteBytes, "checks": domain.Empty()}
	summaries := domain.Empty()
	for _, check := range in.Checks {
		if e = validateCodingCheckSources(ctx, root, b.RealPath, check); e != nil {
			return nil, e
		}
		tree, exe, _, err := checkTree(ctx, check.ToolchainRoot, "", true)
		if err != nil {
			return nil, err
		}
		vendor := ""
		if check.VendorRoot != "" {
			vendor, _, _, err = checkTree(ctx, check.VendorRoot, "", false)
			if err != nil {
				return nil, err
			}
		}
		sources := []runtimeCheckSource{}
		paths := domain.Empty()
		for _, p := range check.SourcePaths {
			if !reads[p] {
				return nil, toolDenied("check source outside explicit read list")
			}
			raw, err := runtimeToolBytes(root, p)
			if err != nil {
				return nil, err
			}
			expected := ""
			row := domain.Object{"path": p}
			if !writes[p] {
				expected = domain.Digest(raw)
				row["sha256"] = expected
			}
			paths = append(paths, row)
			sources = append(sources, runtimeCheckSource{p, expected})
		}
		manifest, err := runtimeCheckSnapshot(ctx, root, sources, "")
		if err != nil {
			return nil, err
		}
		argv := []any{"-C", "${SOURCE}", "test"}
		if vendor != "" {
			argv = append(argv, "-mod=vendor")
		}
		argv = append(argv, "-p=2", "-count=1", "-run", check.TestPattern, check.Package)
		row := domain.Object{"id": check.ID, "executable": "go", "build_hash": exe, "toolchain_root": check.ToolchainRoot, "toolchain_hash": tree, "argv": argv, "source_paths": paths, "resources": domain.Object{"timeout_seconds": check.TimeoutSeconds, "process_limit": check.ProcessLimit, "memory_mib": check.MemoryMiB, "max_text_bytes": check.MaxTextBytes}}
		if vendor != "" {
			row["vendor_root"], row["vendor_hash"] = check.VendorRoot, vendor
		}
		policy["checks"] = append(domain.Arr(policy, "checks"), row)
		// Reuse the actual execution parser; preparation cannot accept a registry
		// which the existing fixed runner would reinterpret differently.
		canonical, err := domain.Decode(domain.Bytes(policy))
		if err != nil {
			return nil, err
		}
		if _, err = parseFrozenRuntimeCheck(canonical, check.ID); err != nil {
			return nil, err
		}
		summaries = append(summaries, domain.Object{"id": check.ID, "package": check.Package, "test_pattern": check.TestPattern, "source_count": len(manifest), "source_bytes": runtimeCheckManifestBytes(manifest), "source_manifest_hash": domain.Hash(manifest), "toolchain_hash": tree, "build_hash": exe, "vendor_hash": vendor})
	}
	// Round-trip private structs/slices to their canonical JSON object shapes.
	return domain.Decode(domain.Bytes(domain.Object{"tool_policy": policy, "check_summaries": summaries, "initial_read_manifest_hash": domain.Hash(initial), "initial_read_bytes": bytes}))
}

func codingMissing(p string) error {
	return toolDenied("coding check source inventory incomplete: " + p)
}

// Require all production Go members of every reached local package, and only
// the explicitly selected test members of the target package. This deliberately
// rejects omissions rather than invoking go list or copying unapproved files.
func validateCodingCheckSources(ctx context.Context, root *os.Root, workspace string, check domain.RuntimeCodingCheck) error {
	selected := map[string]bool{}
	for _, p := range check.SourcePaths {
		selected[p] = true
	}
	if !selected["go.mod"] {
		return codingMissing("go.mod")
	}
	mod, e := runtimeToolBytes(root, "go.mod")
	if e != nil {
		return e
	}
	moduleMatch := regexp.MustCompile(`(?m)^module[ \t]+([^\s]+)[ \t]*$`).FindSubmatch(mod)
	if len(moduleMatch) != 2 {
		return toolDenied("explicit Go module declaration required")
	}
	module := strings.Trim(string(moduleMatch[1]), "\"")
	if _, err := root.Stat("go.sum"); err == nil && !selected["go.sum"] {
		return codingMissing("go.sum")
	}
	pattern, e := regexp.Compile(check.TestPattern)
	if e != nil || !strings.HasPrefix(check.TestPattern, "^") || !strings.HasSuffix(check.TestPattern, "$") {
		return toolDenied("anchored exact Go test selection required")
	}
	target := strings.TrimPrefix(check.Package, "./")
	if target == "." || strings.Contains(target, "...") {
		return toolDenied("one exact local check package required")
	}
	queue := []string{target}
	seen := map[string]bool{}
	testCount := 0
	buildCtx := build.Default
	buildCtx.GOOS = "windows"
	buildCtx.GOARCH = "amd64"
	buildCtx.CgoEnabled = false
	for len(queue) > 0 {
		if e = ctx.Err(); e != nil {
			return e
		}
		dir := queue[0]
		queue = queue[1:]
		if seen[dir] {
			continue
		}
		seen[dir] = true
		if dir != "." && !runtimeCheckPath(dir) {
			return toolDenied("invalid local Go package import")
		}
		full := filepath.Join(workspace, filepath.FromSlash(dir))
		entries, err := os.ReadDir(full)
		if err != nil {
			return err
		}
		files := []*ast.File{}
		names := map[string]bool{}
		production := 0
		for _, entry := range entries {
			name := entry.Name()
			if entry.IsDir() || !strings.HasSuffix(name, ".go") {
				continue
			}
			rel := path.Join(dir, name)
			isTest := strings.HasSuffix(name, "_test.go")
			if isTest && (dir != target || !selected[rel]) {
				continue
			}
			if !selected[rel] {
				return codingMissing(rel)
			}
			if e = runtimeToolPlainPath(root, rel, false); e != nil {
				return e
			}
			// MatchFile reads only a member already explicitly authorized above.
			active, err := buildCtx.MatchFile(full, name)
			if err != nil {
				return err
			}
			if !active {
				continue
			}
			raw, err := runtimeToolBytes(root, rel)
			if err != nil {
				return err
			}
			parsed, err := parser.ParseFile(token.NewFileSet(), rel, raw, parser.ParseComments)
			if err != nil {
				return err
			}
			files = append(files, parsed)
			if !isTest {
				production++
			}
			for _, decl := range parsed.Decls {
				switch d := decl.(type) {
				case *ast.FuncDecl:
					if d.Recv == nil {
						names[d.Name.Name] = true
					}
					if isTest && d.Recv == nil && (d.Name.Name == "TestMain" || d.Name.Name == "init") {
						return toolDenied("selected check tests cannot supply TestMain or init")
					}
					if isTest && d.Recv == nil && strings.HasPrefix(d.Name.Name, "Test") && pattern.MatchString(d.Name.Name) {
						testCount++
					}
				case *ast.GenDecl:
					for _, spec := range d.Specs {
						switch s := spec.(type) {
						case *ast.TypeSpec:
							names[s.Name.Name] = true
						case *ast.ValueSpec:
							for _, n := range s.Names {
								names[n.Name] = true
							}
						}
					}
				}
			}
			if e = validateCodingEmbeds(workspace, dir, parsed, selected); e != nil {
				return e
			}
			for _, imp := range parsed.Imports {
				value, err := strconv.Unquote(imp.Path.Value)
				if err != nil {
					return err
				}
				if imp.Name != nil && imp.Name.Name == "." {
					return toolDenied("selected check does not support implicit dot-import helper authority")
				}
				if value == "C" {
					return toolDenied("offline coding checks cannot use cgo")
				}
				if value == module {
					queue = append(queue, ".")
					continue
				}
				if strings.HasPrefix(value, module+"/") {
					queue = append(queue, strings.TrimPrefix(value, module+"/"))
					continue
				}
				if !runtimeCheckPath(value) {
					return toolDenied("invalid Go import path")
				}
				if info, err := os.Stat(filepath.Join(check.ToolchainRoot, "src", filepath.FromSlash(value))); err == nil && info.IsDir() {
					continue
				}
				if check.VendorRoot == "" {
					return toolDenied("offline vendor inventory required for import: " + value)
				}
				if info, err := os.Stat(filepath.Join(check.VendorRoot, filepath.FromSlash(value))); err != nil || !info.IsDir() {
					return toolDenied("frozen vendor missing imported package: " + value)
				}
			}
		}
		if production == 0 {
			return toolDenied("Go check inventory has no production source for package: " + dir)
		}
		// Detect direct helper calls which cannot be supplied by the selected
		// compilation unit. Full semantic correctness remains the real check's job.
		builtins := map[string]bool{"append": true, "cap": true, "clear": true, "close": true, "complex": true, "copy": true, "delete": true, "imag": true, "len": true, "make": true, "max": true, "min": true, "new": true, "panic": true, "print": true, "println": true, "real": true, "recover": true, "string": true, "bool": true, "byte": true, "rune": true, "int": true, "int8": true, "int16": true, "int32": true, "int64": true, "uint": true, "uint8": true, "uint16": true, "uint32": true, "uint64": true, "uintptr": true, "float32": true, "float64": true, "complex64": true, "complex128": true, "error": true}
		for _, file := range files {
			var missing string
			ast.Inspect(file, func(node ast.Node) bool {
				call, ok := node.(*ast.CallExpr)
				if !ok {
					return true
				}
				id, ok := call.Fun.(*ast.Ident)
				if ok && id.Obj == nil && !names[id.Name] && !builtins[id.Name] {
					missing = id.Name
				}
				return true
			})
			if missing != "" {
				return toolDenied("selected Go check is missing same-package helper: " + missing)
			}
		}
	}
	if testCount == 0 {
		return toolDenied("frozen check selector matches no explicitly included test")
	}
	return nil
}

func validateCodingEmbeds(workspace, dir string, file *ast.File, selected map[string]bool) error {
	for _, group := range file.Comments {
		for _, comment := range group.List {
			if !strings.HasPrefix(comment.Text, "//go:embed ") {
				continue
			}
			for _, pattern := range strings.Fields(strings.TrimPrefix(comment.Text, "//go:embed ")) {
				pattern = strings.TrimPrefix(pattern, "all:")
				if pattern == "" || strings.ContainsAny(pattern, "\\:\"`\x00") || strings.HasPrefix(pattern, "/") || strings.Contains(pattern, "..") {
					return toolDenied("unsupported or escaping Go embed pattern")
				}
				matches, e := filepath.Glob(filepath.Join(workspace, filepath.FromSlash(dir), filepath.FromSlash(pattern)))
				if e != nil || len(matches) == 0 {
					return toolDenied("frozen Go embed input missing")
				}
				sort.Strings(matches)
				for _, match := range matches {
					e = filepath.WalkDir(match, func(p string, entry os.DirEntry, walkErr error) error {
						if walkErr != nil {
							return walkErr
						}
						if entry.Type()&os.ModeSymlink != 0 {
							return toolDenied("reparse input in Go embed")
						}
						if entry.IsDir() {
							return nil
						}
						rel, err := filepath.Rel(workspace, p)
						if err != nil {
							return err
						}
						rel = filepath.ToSlash(rel)
						if !runtimeCheckPath(rel) || !selected[rel] {
							return codingMissing(rel)
						}
						return nil
					})
					if e != nil {
						return e
					}
				}
			}
		}
	}
	return nil
}
