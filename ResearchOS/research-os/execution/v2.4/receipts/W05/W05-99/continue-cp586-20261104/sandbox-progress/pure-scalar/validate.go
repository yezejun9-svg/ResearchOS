// Package deliverygate validates a deliberately small Go source language and
// binds a private copy of its exact bytes to SHA-256. It does not compile or run
// the submitted function, prove Clamp correctness, or grant product acceptance.
package deliverygate

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"go/ast"
	"go/parser"
	"go/scanner"
	"go/token"
	"go/types"
	"unicode/utf8"
)

const (
	PackageName    = "candidate"
	FunctionName   = "Clamp"
	MaxSourceBytes = 16 * 1024
	MaxTokens      = 512
	MaxASTNodes    = 256
	MaxASTDepth    = 32
	MaxStatements  = 64
)

var (
	ErrRejected       = errors.New("source is outside the pure-scalar v1 language")
	ErrDigestMismatch = errors.New("source bytes do not match the validated snapshot")
	ErrUninitialized  = errors.New("source snapshot has not been validated")
)

// ValidatedSource is a structural result for one exact byte snapshot, not a
// correctness or acceptance receipt. Its zero value is invalid. Callers must
// consume Bytes(), or Verify newly read bytes, rather than trust a mutable path.
type ValidatedSource struct {
	raw         []byte
	digest      [sha256.Size]byte
	initialized bool
}

// Bytes returns a separate copy, so a caller cannot mutate the bound snapshot.
func (s *ValidatedSource) Bytes() []byte {
	if s == nil || !s.initialized {
		return nil
	}
	return bytes.Clone(s.raw)
}

// SHA256 returns the lowercase digest of the actual submitted bytes. No
// normalization, formatting, filename, or caller-supplied digest is used.
func (s *ValidatedSource) SHA256() string {
	if s == nil || !s.initialized {
		return ""
	}
	return hex.EncodeToString(s.digest[:])
}

// Verify rejects replacement even when replacement has equivalent Go syntax.
// It does not read or execute files and cannot seal a later compiler's inputs.
func (s *ValidatedSource) Verify(source []byte) error {
	if s == nil || !s.initialized {
		return ErrUninitialized
	}
	if len(source) != len(s.raw) || !bytes.Equal(source, s.raw) {
		return ErrDigestMismatch
	}
	if sha256.Sum256(source) != s.digest {
		return ErrDigestMismatch
	}
	return nil
}

func rejected(rule string) error { return fmt.Errorf("%w: %s", ErrRejected, rule) }

// Validate accepts only package candidate and one Clamp function with three
// named int32 parameters and one unnamed int32 result. It never imports,
// compiles, or executes submitted code. Parsing, checking, and hashing all use
// the same owned copy, whose size is checked before allocation.
func Validate(source []byte) (*ValidatedSource, error) {
	if len(source) == 0 || len(source) > MaxSourceBytes {
		return nil, rejected("source byte limit")
	}
	raw := bytes.Clone(source)
	if !utf8.Valid(raw) {
		return nil, rejected("UTF-8 required")
	}
	fset := token.NewFileSet()
	if err := checkLexicalBudget(fset, raw); err != nil {
		return nil, err
	}
	file, err := parser.ParseFile(fset, "candidate.go", raw, parser.ParseComments|parser.AllErrors)
	if err != nil {
		return nil, rejected("Go syntax")
	}
	if file.Name.Name != PackageName || len(file.Comments) != 0 || len(file.Imports) != 0 || len(file.Decls) != 1 {
		return nil, rejected("fixed package, one declaration, no imports or comments")
	}
	if err := checkASTBudget(file); err != nil {
		return nil, err
	}
	fn, ok := file.Decls[0].(*ast.FuncDecl)
	if !ok || fn.Recv != nil || fn.Name.Name != FunctionName || fn.Type.TypeParams != nil || fn.Body == nil {
		return nil, rejected("fixed non-generic function required")
	}
	parameters, err := checkSignature(fn.Type)
	if err != nil {
		return nil, err
	}
	checker := bodyChecker{parameters: parameters}
	if err := checker.block(fn.Body); err != nil {
		return nil, err
	}
	info := &types.Info{Types: make(map[ast.Expr]types.TypeAndValue), Defs: make(map[*ast.Ident]types.Object), Uses: make(map[*ast.Ident]types.Object)}
	config := &types.Config{Sizes: types.SizesFor("gc", "amd64")}
	pkg, err := config.Check("researchos.local/pure-scalar-candidate", fset, []*ast.File{file}, info)
	if err != nil {
		return nil, rejected("Go type checking")
	}
	object, ok := pkg.Scope().Lookup(FunctionName).(*types.Func)
	if !ok {
		return nil, rejected("function type identity")
	}
	signature, ok := object.Type().(*types.Signature)
	if !ok || signature.Params().Len() != 3 || signature.Results().Len() != 1 || !types.Identical(signature.Results().At(0).Type(), types.Typ[types.Int32]) {
		return nil, rejected("fixed int32 signature")
	}
	parameterObjects := make(map[types.Object]bool)
	for i := 0; i < signature.Params().Len(); i++ {
		parameter := signature.Params().At(i)
		if !types.Identical(parameter.Type(), types.Typ[types.Int32]) {
			return nil, rejected("int32 parameter types")
		}
		parameterObjects[parameter] = true
	}
	for identifier, object := range info.Uses {
		if identifier.Pos() < fn.Body.Pos() {
			continue // Signature's predeclared int32 type names were checked above.
		}
		if parameterObjects[object] || object == types.Universe.Lookup("true") || object == types.Universe.Lookup("false") {
			continue
		}
		return nil, rejected("body identifiers must resolve to parameters or boolean constants")
	}
	return &ValidatedSource{raw: raw, digest: sha256.Sum256(raw), initialized: true}, nil
}

func checkLexicalBudget(fset *token.FileSet, raw []byte) error {
	var lexer scanner.Scanner
	lexicalError := false
	lexer.Init(fset.AddFile("candidate.go", -1, len(raw)), raw, func(token.Position, string) { lexicalError = true }, scanner.ScanComments)
	for count := 0; ; count++ {
		_, kind, _ := lexer.Scan()
		if lexicalError || kind == token.ILLEGAL {
			return rejected("Go lexical syntax")
		}
		// Reject all comments, including compiler, build, cgo and line directives.
		if kind == token.COMMENT {
			return rejected("comments and directives are forbidden")
		}
		if kind == token.EOF {
			return nil
		}
		if count >= MaxTokens {
			return rejected("token budget")
		}
	}
}

func checkASTBudget(file *ast.File) error {
	nodes, depth := 0, 0
	var failure error
	ast.Inspect(file, func(node ast.Node) bool {
		if node == nil {
			depth--
			return true
		}
		if failure != nil {
			return false
		}
		nodes++
		depth++
		if nodes > MaxASTNodes || depth > MaxASTDepth {
			failure = rejected("AST node or depth budget")
			depth-- // Returning false suppresses this node's nil callback.
			return false
		}
		return true
	})
	return failure
}

func checkSignature(signature *ast.FuncType) (map[string]bool, error) {
	parameters := make(map[string]bool)
	if signature.Params == nil || signature.Results == nil || len(signature.Results.List) != 1 {
		return nil, rejected("three parameters and one result required")
	}
	for _, field := range signature.Params.List {
		kind, ok := field.Type.(*ast.Ident)
		if !ok || kind.Name != "int32" || len(field.Names) == 0 {
			return nil, rejected("named int32 parameters required")
		}
		for _, name := range field.Names {
			if name.Name == "_" || parameters[name.Name] {
				return nil, rejected("distinct nonblank parameters required")
			}
			parameters[name.Name] = true
		}
	}
	result := signature.Results.List[0]
	kind, ok := result.Type.(*ast.Ident)
	if len(parameters) != 3 || !ok || kind.Name != "int32" || len(result.Names) != 0 {
		return nil, rejected("three int32 parameters and one unnamed int32 result required")
	}
	return parameters, nil
}

type bodyChecker struct {
	parameters map[string]bool
	statements int
}

func (c *bodyChecker) block(block *ast.BlockStmt) error {
	for _, statement := range block.List {
		if err := c.statement(statement); err != nil {
			return err
		}
	}
	return nil
}

func (c *bodyChecker) statement(statement ast.Stmt) error {
	c.statements++
	if c.statements > MaxStatements {
		return rejected("statement budget")
	}
	switch node := statement.(type) {
	case *ast.BlockStmt:
		return c.block(node)
	case *ast.IfStmt:
		if node.Init != nil {
			return rejected("if initializer forbidden")
		}
		if err := c.expression(node.Cond); err != nil {
			return err
		}
		if err := c.block(node.Body); err != nil {
			return err
		}
		if node.Else != nil {
			switch node.Else.(type) {
			case *ast.BlockStmt, *ast.IfStmt:
				return c.statement(node.Else)
			default:
				return rejected("else statement kind")
			}
		}
		return nil
	case *ast.AssignStmt:
		if node.Tok != token.ASSIGN || len(node.Lhs) != 1 || len(node.Rhs) != 1 {
			return rejected("only a single parameter assignment with = is permitted")
		}
		target, ok := node.Lhs[0].(*ast.Ident)
		if !ok || !c.parameters[target.Name] {
			return rejected("assignment target must be a parameter")
		}
		return c.expression(node.Rhs[0])
	case *ast.ReturnStmt:
		if len(node.Results) != 1 {
			return rejected("one explicit return value required")
		}
		return c.expression(node.Results[0])
	default:
		return rejected("statement kind")
	}
}

func (c *bodyChecker) expression(expression ast.Expr) error {
	switch node := expression.(type) {
	case *ast.Ident:
		if c.parameters[node.Name] || node.Name == "true" || node.Name == "false" {
			return nil
		}
		return rejected("expression identifier")
	case *ast.BasicLit:
		if node.Kind != token.INT || len(node.Value) == 0 || len(node.Value) > 10 || len(node.Value) > 1 && node.Value[0] == '0' {
			return rejected("short decimal integer literals required")
		}
		for _, digit := range node.Value {
			if digit < '0' || digit > '9' {
				return rejected("decimal integer literals required")
			}
		}
		return nil
	case *ast.ParenExpr:
		return c.expression(node.X)
	case *ast.UnaryExpr:
		switch node.Op {
		case token.ADD, token.SUB, token.XOR, token.NOT:
			return c.expression(node.X)
		default:
			return rejected("unary operator")
		}
	case *ast.BinaryExpr:
		switch node.Op {
		case token.ADD, token.SUB, token.MUL, token.AND, token.OR, token.XOR, token.AND_NOT,
			token.EQL, token.NEQ, token.LSS, token.LEQ, token.GTR, token.GEQ, token.LAND, token.LOR:
			if err := c.expression(node.X); err != nil {
				return err
			}
			return c.expression(node.Y)
		default:
			return rejected("binary operator")
		}
	default:
		return rejected("expression kind")
	}
}
