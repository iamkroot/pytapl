# PyTAPL

(WIP) Python implementations of various type checkers and interpreters as described in Types and Programming Languages by Benjamin Pierce.

## Components
Each subdirectory is a self-contained program, with `run.py` being the main entrypoint.
1. [`arith`](01_arith): A simple interpreter with basic numeric expressions to start things off.
2. [`untyped`](02_untyped): Implementation of the untyped lambda calculus, as covered in chapters 5-7.
3. [`simplebool`](03_simplebool): Simply-typed calculus supporting `Bool` and `Arrow` (function) types and `if-then-else` statements, from chapters 9-10.
4. [`rcdsub`](04_rcdsub): Calculus involving `Record` types and sub-typing relation between types. Supports both `Top` and `Bot` types. Covers chapters 15-17.
5. [`recon`](05_recon): Implementation of Hindley-Milner type inference algorithm on the simply-typed calculus by equality constraint generation, as described in chapter 22.
6. [`system_f`](06_system_f): Includes the typechecker for lambda calculus with parametric polymorphism (SystemF). Supports both universal, and existential types. 
7. ... TODO :)

## Notes
* Mostly stays close to the original implementation in OCaml
* Makes heavy use of Python 3.10's new `match` statements for pattern matching
* Parsing is done using `Lark`. Not focusing on efficiency of the parser
