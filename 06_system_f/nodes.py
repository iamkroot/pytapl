import abc
from dataclasses import dataclass

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
    ty: "Ty"
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
class BindNode(Node):
    name: Token
    binding: "Binding"


@dataclass
class ZeroNode(Node):
    pass


@dataclass
class SuccNode(Node):
    val: Node


@dataclass
class PredNode(Node):
    val: Node


@dataclass
class IsZeroNode(Node):
    val: Node


@dataclass
class TypeAbsNode(Node):
    name: str
    body: Node


@dataclass
class TypeAppNode(Node):
    body: Node
    ty: "Ty"


@dataclass
class ExisPackNode(Node):
    exis_ty: "Ty"
    body: Node
    ty: "Ty"


@dataclass
class ExisUnpackNode(Node):
    tyname: str
    varname: str
    init: Node
    body: Node


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
        return f"{ty1}→{self.ty2}"

    __repr__ = __str__


@dataclass
class TyVar(Ty):
    idx: int
    ctx_len: int = -1


@dataclass
class UnivTy(Ty):
    name: str
    body: Ty


@dataclass
class ExisTy(Ty):
    name: str
    body: Ty


@dataclass
class Binding:
    pass


@dataclass
class VarBinding(Binding):
    ty: Ty


@dataclass
class TyVarBinding(Binding):
    pass
