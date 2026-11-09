# Pure scalar v1 pilot

This standalone `deliverygate` package is a C-workspace prototype. It is not applied to ResearchOS, does not open a LIVE gate, and provides no business-correctness or independent-acceptance result.

`Validate` accepts only `package candidate` containing exactly one non-generic, non-method `Clamp` function. It requires exactly three distinct, nonblank named `int32` parameters and one unnamed `int32` result. Parameter names may vary; grouped declarations are allowed. Source is valid UTF-8, at most 16 KiB, 512 lexical tokens, 256 AST nodes, depth 32 and 64 statements.

All comments are rejected, including compiler, build, cgo and line directives. Imports, `init`, other declarations, globals, local declarations, `:=`, named results, function literals, calls (including conversions and builtins), go/defer, loops, switches, selects, labels/goto, selectors, indexes, composites, pointers and channels are rejected.

The body may contain blocks, `if` without an initializer, `else`, explicit one-value returns, and single `=` assignments to parameters. Expressions may use parameters, boolean constants, short decimal integer literals, parentheses, unary `+ - ^ !`, and binary `+ - * & | ^ &^ == != < <= > >= && ||`. Go type checking still applies. Division, remainder and shifts are deliberately excluded. Int32 arithmetic retains Go's deterministic overflow behavior; the validator proves no mathematical bounds or Clamp semantics.

Validation uses one owned byte snapshot for parsing, type checking and SHA-256. `Bytes()` returns a copy. `Verify()` requires the exact bytes, including whitespace; nil and zero-value tokens are invalid. This protects the primitive against source substitution, but a future compiler/runner must independently consume those sealed bytes or reverify its own exact inputs. Merely validating a pathname earlier is insufficient.

The package never compiles or executes submitted code. Go tests compile this validator itself and inspect candidate source as data. `return 0` can pass the structural policy even though it is not a correct Clamp implementation.
