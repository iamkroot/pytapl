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
class RecordNode(Node):
    fields: dict[Token, Node]


@dataclass
class ProjNode(Node):
    rcd: Node
    label: Token


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
class Ty:
    pass


@dataclass
class BoolTy(Ty):
    pass


@dataclass
class RecordTy(Ty):
    fields: dict[Token, Ty]


@dataclass
class ArrowTy(Ty):
    ty1: Ty
    ty2: Ty


@dataclass
class TopTy(Ty):
    pass


@dataclass
class BotTy(Ty):
    pass


@dataclass
class Binding:
    pass


@dataclass
class VarBinding(Binding):
    ty: Ty
