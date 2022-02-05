import abc
from dataclasses import dataclass
from itertools import count
from typing import Callable, Optional

from lark.lexer import Token


@dataclass
class Node(abc.ABC):
    pass


@dataclass
class TrueNode(Node):
    pass


@dataclass
class FalseNode(Node):
    pass


@dataclass
class VarNode(Node):
    idx: int
    ctx_len: int = -1


@dataclass
class AbsNode(Node):
    orig_name: str
    ty: Optional["Ty"]
    body: Node


@dataclass
class AppNode(Node):
    child1: Node
    child2: Node


@dataclass
class LetNode(Node):
    varname: str
    init: Node
    body: Node


@dataclass
class IfNode(Node):
    cond: Node
    then: Node
    else_: Node


@dataclass
class TupleNode(Node):
    fields: tuple[Node, ...]


@dataclass
class BindNode(Node):
    name: Token
    binding: "Binding"


@dataclass
class ZeroNode(Node):
    def __str__(self) -> str:
        return "0"
    __repr__ = __str__


@dataclass
class SuccNode(Node):
    val: Node

    def __str__(self) -> str:
        from parser import _church_to_num
        try:
            return str(_church_to_num(self))
        except TypeError:
            return f"SuccNode(val={self.val})"

    __repr__ = __str__


@dataclass
class PredNode(Node):
    val: Node


@dataclass
class IsZeroNode(Node):
    val: Node


@dataclass
class Ty:
    pass


@dataclass
class BoolTy(Ty):
    def __str__(self) -> str:
        return "Bool"

    __repr__ = __str__


@dataclass
class NatTy(Ty):
    def __str__(self) -> str:
        return "Nat"

    __repr__ = __str__


@dataclass
class ArrowTy(Ty):
    ty1: Ty
    ty2: Ty

    def __str__(self):
        if isinstance(self.ty1, ArrowTy):
            ty1 = f"({self.ty1})"
        else:
            ty1 = f"{self.ty1}"
        return f"{ty1}➔{self.ty2}"

    __repr__ = __str__


@dataclass
class IdTy(Ty):
    name: str

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


@dataclass
class TupleTy(Ty):
    types: tuple[Ty, ...]

    def __str__(self) -> str:
        return "(" + ", ".join(map(str, self.types)) + ")"

    __repr__ = __str__


def type_map(on_tyvar: Callable[[IdTy], IdTy], ty: Ty) -> Ty:
    match ty:
        case IdTy(_):
            return on_tyvar(ty)
        case ArrowTy(ty1, ty2):
            return ArrowTy(type_map(on_tyvar, ty1), type_map(on_tyvar, ty2))
        case BoolTy() | NatTy():
            return ty
    raise Exception(f"Unreachable {ty}")


def uvargen():
    for n in count():
        yield IdTy(name=f"?X{n}")


@dataclass
class EqConstraint:
    lhs: Ty
    rhs: Ty

    def __repr__(self) -> str:
        return f"({self.lhs}=={self.rhs})"

    __str__ = __repr__


@dataclass
class TypeSubst:
    src: IdTy
    tgt: Ty

    def __repr__(self) -> str:
        return f"{self.src.name}↦{self.tgt}"

    __str__ = __repr__


@dataclass
class Binding:
    def contains_ty(self, ty: IdTy):
        return False


class FoundException(Exception):
    pass


@dataclass
class VarBinding(Binding):
    ty: Ty

    def contains_ty(self, ty: IdTy):
        def ty_eq(id_ty: IdTy) -> IdTy:
            if id_ty == ty:
                raise FoundException()
            return id_ty
        try:
            type_map(ty_eq, self.ty)
        except FoundException:
            return True  # really ugly way to return true
        else:
            return False


@dataclass
class SchemeBinding(Binding):
    ty_vars: tuple[IdTy, ...]
    body_ty: Ty

    def __str__(self) -> str:
        inner = ", ".join(map(str, self.ty_vars))
        if len(self.ty_vars) > 1:
            inner = f"({inner})"
        return f"∀{inner}.{self.body_ty}"

    def contains_ty(self, ty: IdTy):
        assert ty not in self.ty_vars, "ty should not be present in ty_vars"
        def ty_eq(id_ty: IdTy) -> IdTy:
            if id_ty == ty:
                raise FoundException()
            return id_ty
        try:
            type_map(ty_eq, self.body_ty)
        except FoundException:
            return True  # really ugly way to return true
        else:
            return False