// Analysis helper: parses pinned Go source as data. It never imports product packages.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"os"
	"strings"
)

type inputFile struct {
	Path       string `json:"path"`
	SHA256     string `json:"sha256"`
	ImportPath string `json:"import_path"`
	Kind       string `json:"kind"`
	Standard   bool   `json:"standard"`
}

type input struct {
	Files []inputFile `json:"source_files"`
}

type calls struct {
	Names   []string `json:"calls"`
	GoCount int      `json:"go_statements"`
	Defers  int      `json:"defer_statements"`
}

type declaration struct {
	Package  string `json:"import_path"`
	Standard bool   `json:"standard"`
	File     string `json:"file"`
	Line     int    `json:"line"`
	EndLine  int    `json:"end_line"`
	Kind     string `json:"kind"`
	Name     string `json:"name"`
	Text     string `json:"text,omitempty"`
	Calls    calls  `json:"call_syntax"`
	Imports  map[string]string `json:"import_aliases,omitempty"`
}

func render(fset *token.FileSet, node any) string {
	var b bytes.Buffer
	if err := format.Node(&b, fset, node); err != nil {
		panic(err)
	}
	return b.String()
}

func scan(fset *token.FileSet, node ast.Node) calls {
	result := calls{Names: []string{}}
	ast.Inspect(node, func(node ast.Node) bool {
		switch n := node.(type) {
		case *ast.CallExpr:
			result.Names = append(result.Names, render(fset, n.Fun))
		case *ast.GoStmt:
			result.GoCount++
		case *ast.DeferStmt:
			result.Defers++
		}
		return true
	})
	return result
}

func main() {
	if len(os.Args) != 2 {
		panic("exact selected-source map argument required")
	}
	raw, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	var in input
	if err := json.Unmarshal(raw, &in); err != nil {
		panic(err)
	}
	fset := token.NewFileSet()
	initializers := []declaration{}
	functions := []declaration{}
	fileCount := 0
	for _, row := range in.Files {
		if row.Kind != "GoFiles" && row.Kind != "CgoFiles" {
			continue
		}
		data, err := os.ReadFile(row.Path)
		if err != nil {
			panic(err)
		}
		sum := sha256.Sum256(data)
		if hex.EncodeToString(sum[:]) != row.SHA256 {
			panic("source digest drift: " + row.Path)
		}
		file, err := parser.ParseFile(fset, row.Path, data, parser.AllErrors)
		if err != nil {
			panic(err)
		}
		fileCount++
		aliases := map[string]string{}
		for _, spec := range file.Imports {
			path := strings.Trim(spec.Path.Value, "\"")
			name := path[strings.LastIndex(path, "/")+1:]
			if spec.Name != nil {
				name = spec.Name.Name
			}
			aliases[name] = path
		}
		for _, decl := range file.Decls {
			switch n := decl.(type) {
			case *ast.FuncDecl:
				name := n.Name.Name
				if n.Recv != nil {
					name = "(" + render(fset, n.Recv.List[0].Type) + ")." + name
				}
				entry := declaration{Package: row.ImportPath, Standard: row.Standard, File: row.Path, Line: fset.Position(n.Pos()).Line, EndLine: fset.Position(n.End()).Line, Kind: "function", Name: name, Calls: scan(fset, n), Imports: aliases}
				if n.Name.Name == "init" && n.Recv == nil {
					entry.Kind = "init_function"
					entry.Text = render(fset, n)
					initializers = append(initializers, entry)
				}
				functions = append(functions, entry)
			case *ast.GenDecl:
				if n.Tok != token.VAR {
					continue
				}
				for _, spec := range n.Specs {
					value := spec.(*ast.ValueSpec)
					if len(value.Values) == 0 {
						continue
					}
					names := []string{}
					for _, name := range value.Names {
						names = append(names, name.Name)
					}
					initializers = append(initializers, declaration{Package: row.ImportPath, Standard: row.Standard, File: row.Path, Line: fset.Position(value.Pos()).Line, EndLine: fset.Position(value.End()).Line, Kind: "package_variable_initializer", Name: strings.Join(names, ","), Text: render(fset, value), Calls: scan(fset, value), Imports: aliases})
				}
			}
		}
	}
	output := map[string]any{"schema": "researchos.verifier-initializer-syntax-index.v1", "parsed_go_files": fileCount, "initializers": initializers, "functions": functions, "limits": []string{"AST syntax index only; no type resolution, dynamic dispatch, assembly behavior or complete callgraph proof.", "Function literal calls in package values may be deferred until later use; syntax calls are not automatically executed initializers.", "No product source was imported or run; raw source digests were checked before parsing."}, "source_writes": 0, "actual_product_actions": 0, "formal_increment": 0}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(output); err != nil {
		panic(err)
	}
	fmt.Fprintln(os.Stderr, "parsed", fileCount, "Go files; initializer entries", len(initializers), "functions", len(functions))
}
