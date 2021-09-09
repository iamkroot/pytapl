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
class Ty:
    pass


@dataclass
class BoolTy(Ty):
    pass


@dataclass
class NatTy(Ty):
    pass


@dataclass
class ArrowTy(Ty):
    ty1: Ty
    ty2: Ty


@dataclass
class IdTy(Ty):
    name: str


@dataclass
class Binding:
    pass


@dataclass
class VarBinding(Binding):
    ty: Ty
