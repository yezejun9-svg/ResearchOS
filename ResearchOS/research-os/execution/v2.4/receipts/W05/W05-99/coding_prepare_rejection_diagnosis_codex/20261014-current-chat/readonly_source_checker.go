package main
import("context";"errors";"go/ast";"go/build";"go/parser";"go/token";"os";"path";"path/filepath";"regexp";"sort";"strconv";"strings";"io";"encoding/json";"fmt")
type RuntimeCodingCheck struct {SourcePaths []string; Package,TestPattern,ToolchainRoot,VendorRoot string}
const runtimeToolFileLimit=2<<20
func toolDenied(s string)error{return errors.New(s)}
var (
	ErrPathAbsolute     = errors.New("ABSOLUTE_PATH")
	ErrPathEscape       = errors.New("PATH_OUT_OF_SCOPE")
	ErrPathDrive        = errors.New("ABSOLUTE_PATH")
	ErrPathNull         = errors.New("INVALID_REQUEST")
	ErrPathEmpty        = errors.New("INVALID_REQUEST")
	ErrPathStream       = errors.New("INVALID_REQUEST")
	ErrPathUNC          = errors.New("ABSOLUTE_PATH")
	ErrPathReparsePoint = errors.New("PATH_OUT_OF_SCOPE")
	ErrRootRevoked      = errors.New("WORKSPACE_REVOKED")
	ErrRootUnknown      = errors.New("NOT_FOUND")
	ErrRootDenied       = errors.New("POLICY_DENIED")

	drivePrefix = regexp.MustCompile(`^[A-Za-z]:`)
)

// CheckRelativePath rejects everything the contract's RelativePath pattern rejects, plus the
// Windows-only escapes the pattern cannot express (alternate data streams and UNC prefixes),
// which the schema description explicitly assigns to the host.
func CheckRelativePath(rel string) error {
	if rel == "" {
		return ErrPathEmpty
	}
	if strings.ContainsRune(rel, 0) {
		return ErrPathNull
	}
	if strings.HasPrefix(rel, "/") || strings.HasPrefix(rel, "\\") {
		return ErrPathAbsolute
	}
	if drivePrefix.MatchString(rel) {
		return ErrPathDrive
	}
	// A drive-qualified path and an NTFS stream both use ':'; the second may appear later.
	if i := strings.Index(rel, ":"); i > 1 && i < len(rel)-1 {
		return ErrPathStream
	}
	segments := splitRel(rel)
	for _, seg := range segments {
		if seg == ".." {
			return ErrPathEscape
		}
	}
	return nil
}

func splitRel(rel string) []string {
	return strings.FieldsFunc(rel, func(r rune) bool { return r == '/' || r == '\\' })
}

// NormalizeRelative folds a published relative path to a single-separator form for comparison
// and joins it under a root without ever consulting the caller's idea of the current directory.
func NormalizeRelative(rel string) string {
	return strings.Join(splitRel(rel), "/")
}

func runtimeCheckPath(s string) bool {
	if s == "." || CheckRelativePath(s) != nil || NormalizeRelative(s) != s || strings.ContainsAny(s, "\\:") {
		return false
	}
	for _, segment := range strings.Split(s, "/") {
		if segment == "." || segment == "" {
			return false
		}
	}
	return true
}

func runtimeToolPlainPath(root *os.Root, rel string, allowMissingFinal bool) error {
	parts := strings.Split(rel, "/")
	for i := range parts {
		prefix := strings.Join(parts[:i+1], "/")
		info, err := root.Lstat(prefix)
		if errors.Is(err, os.ErrNotExist) && i == len(parts)-1 && allowMissingFinal {
			return nil
		}
		if err != nil {
			return err
		}
		if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() && !info.Mode().IsRegular() {
			return ErrPathReparsePoint
		}
		if i < len(parts)-1 && !info.IsDir() {
			return toolDenied("parent must be a plain directory")
		}
		if i == len(parts)-1 && !info.Mode().IsRegular() {
			return toolDenied("target must be a regular file")
		}
	}
	return nil
}

func runtimeToolBytes(root *os.Root, rel string) ([]byte, error) {
	f, err := root.Open(rel)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > runtimeToolFileLimit {
		return nil, toolDenied("tool file must be regular and at most 2 MiB")
	}
	data, err := io.ReadAll(io.LimitReader(f, runtimeToolFileLimit+1))
	if err != nil {
		return nil, err
	}
	if len(data) > runtimeToolFileLimit {
		return nil, toolDenied("tool file exceeded 2 MiB")
	}
	return data, nil
}

func codingMissing(p string) error {
	return toolDenied("coding check source inventory incomplete: " + p)
}

// Require all production Go members of every reached local package, and only
// the explicitly selected test members of the target package. This deliberately
// rejects omissions rather than invoking go list or copying unapproved files.
func validateCodingCheckSources(ctx context.Context, root *os.Root, workspace string, check RuntimeCodingCheck) error {
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

func main(){var in RuntimeCodingCheck;b,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if e=json.Unmarshal(b,&in);e!=nil{panic(e)};r,e:=os.OpenRoot(os.Args[2]);if e!=nil{panic(e)};defer r.Close();e=validateCodingCheckSources(context.Background(),r,os.Args[2],in);if e!=nil{fmt.Println("CHECKER_REJECTED: "+e.Error());os.Exit(2)};fmt.Println("CHECKER_ACCEPTED")}
