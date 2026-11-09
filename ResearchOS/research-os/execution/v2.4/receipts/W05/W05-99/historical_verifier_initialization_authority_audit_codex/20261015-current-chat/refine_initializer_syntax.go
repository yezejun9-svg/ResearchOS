// Analysis-only parser. It never imports or executes audited packages.
package main

import (
 "bytes"
 "encoding/json"
 "fmt"
 "go/ast"
 "go/format"
 "go/parser"
 "go/token"
 "os"
 "strconv"
 "strings"
)

type File struct { Path string `json:"path"`; Import string `json:"import_path"`; Standard bool `json:"standard"`; Kind string `json:"kind"` }
type Input struct { Files []File `json:"source_files"` }
type Parsed struct { Meta File; Tree *ast.File; Imports map[string]string }
type Call struct { Target string `json:"target"`; Line int `json:"line"`; Kind string `json:"kind"` }
type Entry struct {
 Import string `json:"import_path"`; File string `json:"file"`; Standard bool `json:"standard"`
 Kind string `json:"kind"`; Name string `json:"name"`; Line int `json:"line"`; End int `json:"end_line"`
 Calls []Call `json:"eager_call_syntax"`; DeferredLiteralBodies int `json:"uninvoked_function_literal_bodies"`
 Go int `json:"go_statements"`; Defer int `json:"defer_statements"`
}
var fs=token.NewFileSet()
var types=map[string]bool{}
func repr(n ast.Node) string { var b bytes.Buffer; if n!=nil { format.Node(&b,fs,n) }; return b.String() }
func typeExpr(n ast.Expr,p Parsed) bool {
 switch t:=n.(type) {
 case *ast.ParenExpr: return typeExpr(t.X,p)
 case *ast.StarExpr: return typeExpr(t.X,p)
 case *ast.ArrayType,*ast.MapType,*ast.StructType,*ast.InterfaceType,*ast.ChanType,*ast.FuncType: return true
 case *ast.Ident:
  return types[p.Meta.Import+"."+t.Name] || strings.Contains(" bool byte rune string int int8 int16 int32 int64 uint uint8 uint16 uint32 uint64 uintptr float32 float64 complex64 complex128 "," "+t.Name+" ")
 case *ast.SelectorExpr:
  x,ok:=t.X.(*ast.Ident); return ok && types[p.Imports[x.Name]+"."+t.Sel.Name]
 }
 return false
}
func inspect(n ast.Node,p Parsed,e *Entry) {
 if n==nil{return}
 ast.Inspect(n,func(n ast.Node)bool {
  if n==nil{return false}
  switch t:=n.(type) {
  case *ast.FuncLit:
   e.DeferredLiteralBodies++;return false
  case *ast.CallExpr:
   k:="call_or_dynamic_dispatch"
   if typeExpr(t.Fun,p){k="type_conversion_candidate"}
   if id,ok:=t.Fun.(*ast.Ident);ok && strings.Contains(" append cap clear close complex copy delete imag len make max min new panic print println real recover "," "+id.Name+" "){k="builtin"}
   f:=t.Fun
   for {q,ok:=f.(*ast.ParenExpr);if !ok{break};f=q.X}
   if lit,ok:=f.(*ast.FuncLit);ok {
    e.Calls=append(e.Calls,Call{"immediately_invoked_function_literal",fs.Position(t.Pos()).Line,"immediate_literal_call"})
    for _,a:=range t.Args{inspect(a,p,e)}
    inspect(lit.Body,p,e);return false
   }
   e.Calls=append(e.Calls,Call{repr(t.Fun),fs.Position(t.Pos()).Line,k})
  case *ast.GoStmt: e.Go++
  case *ast.DeferStmt: e.Defer++
  }
  return true
 })
}
func main(){
 if len(os.Args)!=2 {panic("source-map argument required")}
 b,err:=os.ReadFile(os.Args[1]);if err!=nil{panic(err)}
 var input Input;if err=json.Unmarshal(b,&input);err!=nil{panic(err)}
 var parsed []Parsed
 for _,m:=range input.Files {
  if !strings.HasSuffix(m.Path,".go"){continue}
  f,err:=parser.ParseFile(fs,m.Path,nil,0);if err!=nil{panic(err)}
  p:=Parsed{m,f,map[string]string{}}
  for _,i:=range f.Imports {v,_:=strconv.Unquote(i.Path.Value);n:=v[strings.LastIndex(v,"/")+1:];if i.Name!=nil{n=i.Name.Name};p.Imports[n]=v}
  for _,d:=range f.Decls {g,ok:=d.(*ast.GenDecl);if !ok{continue};for _,s:=range g.Specs {if t,ok:=s.(*ast.TypeSpec);ok{types[m.Import+"."+t.Name.Name]=true}}}
  parsed=append(parsed,p)
 }
 var out []Entry
 for _,p:=range parsed {
  for _,d:=range p.Tree.Decls {
   if f,ok:=d.(*ast.FuncDecl);ok && f.Recv==nil && f.Name.Name=="init" {
    e:=Entry{Import:p.Meta.Import,File:p.Meta.Path,Standard:p.Meta.Standard,Kind:"init_function",Name:"init",Line:fs.Position(f.Pos()).Line,End:fs.Position(f.End()).Line,Calls:[]Call{}}
    inspect(f.Body,p,&e);out=append(out,e)
   }
   g,ok:=d.(*ast.GenDecl);if !ok || g.Tok!=token.VAR{continue}
   for _,s:=range g.Specs {
    v,ok:=s.(*ast.ValueSpec);if !ok{continue}
    names:=[]string{};for _,n:=range v.Names{names=append(names,n.Name)}
    e:=Entry{Import:p.Meta.Import,File:p.Meta.Path,Standard:p.Meta.Standard,Kind:"package_variable_initializer",Name:strings.Join(names,","),Line:fs.Position(v.Pos()).Line,End:fs.Position(v.End()).Line,Calls:[]Call{}}
    for _,n:=range v.Values {inspect(n,p,&e)}
    out=append(out,e)
   }
  }
 }
 enc:=json.NewEncoder(os.Stdout);enc.SetIndent("","  ")
 if err=enc.Encode(map[string]any{"schema":"researchos.eager-initializer-syntax-refinement.v1","parsed_files":len(parsed),"entries":out,"limits":[]string{"Syntax refinement only, not type checking or control-flow/callgraph proof.","Uninvoked function literal bodies excluded; callback may execute if the receiving callee invokes it.","Conversion candidates use declared type names; local shadowing and dynamic calls need manual audit.","Go statements enumerate asynchronous startup; every branch is retained conservatively."}});err!=nil{panic(err)}
 fmt.Fprintln(os.Stderr,"analysis parser completed; no audited package executed")
}
