from context import Context
from nodes import ArrowTy, IdTy, uvargen
from parser import parse
from run import apply_substs_to_ty, recon, unify


def get_ty(program: str):
    cmds = parse(program)
    vargen = uvargen()
    ctx = Context(vargen)
    constraints = []
    principal_ty = None
    for cmd in cmds:
        ty = recon(cmd, ctx, constraints, vargen)
        substs = unify(constraints)
        principal_ty = apply_substs_to_ty(ty, substs)
    return principal_ty


# cases taken from https://okmij.org/ftp/ML/generalization/unsound.ml

prog = "lambda x. let y = lambda z.z in y;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(_), ArrowTy(IdTy(b), IdTy(c))) if b == c:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. let y = lambda z.z in (y x);"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(a), IdTy(b)) if a == b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. x x;"
print(prog)
try:
    get_ty(prog)
except Exception as e:
    print(e)
else:
    raise AssertionError(f"Should not be typable")
print()


prog = "let x = x in x;"
print(prog)
try:
    get_ty(prog)
except Exception as e:
    print(e)
else:
    raise AssertionError(f"Should not be typable")
print()


prog = "lambda y. y (lambda z. y z);"
print(prog)
try:
    get_ty(prog)
except Exception as e:
    print(e)
else:
    raise AssertionError(f"Should not be typable")
print()


id_ = "lambda x.x";
prog = f"let id = {id_} in id id;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(a), IdTy(b)) if a == b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


c1 = "lambda x. lambda y. x y";
prog = f"let x = {c1} in let y = (let z = (x ({id_})) in z) in y;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(a), IdTy(b)) if a == b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda z:Z. lambda y. (let x = (z y) in (lambda w. y w));"
print(prog)
match ty := get_ty(prog):
    case (ArrowTy(ArrowTy(ArrowTy(IdTy(a), IdTy(b)), IdTy(c)),
                  ArrowTy(ArrowTy(IdTy(d), IdTy(e)),
                          ArrowTy(IdTy(f), IdTy(g))))) if a == d == f and b == e == g and a != b != c:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. let y = x in y;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(a), IdTy(b)) if a == b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. let y = lambda z. x in y;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(a), ArrowTy(IdTy(b), IdTy(c))) if a == c != b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. let y = lambda z. (x z) in y;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(ArrowTy(IdTy(a), IdTy(b)),
                 ArrowTy(IdTy(c), IdTy(d))) if a == c and b == d and a != b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. lambda y. let x = (x y) in (x y);"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(ArrowTy(IdTy(a), ArrowTy(IdTy(b), IdTy(c))),
                 ArrowTy(IdTy(d), IdTy(e))) if a == b == d and c == e and a != c:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()


prog = "lambda x. let y = x in (y y);"
print(prog)
try:
    get_ty(prog)
except Exception as e:
    print(e)
else:
    raise AssertionError(f"Should not be typable")
print()


prog = "lambda x. let y = (let z = x in z) in y;"
print(prog)
match ty := get_ty(prog):
    case ArrowTy(IdTy(a), IdTy(b)) if a == b:
        print(ty)
    case _: raise AssertionError(f"Invalid type {ty}")
print()

