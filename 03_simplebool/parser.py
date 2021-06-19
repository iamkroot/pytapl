import abc
from collections import namedtuple
from dataclasses import dataclass
from typing import cast
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer

with open("grammar.lark") as f:
    grammar = f.read()


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
class Ty:
    pass


@dataclass
class BoolTy(Ty):
    pass


@dataclass
class ArrowTy(Ty):
    ty1: Ty
    ty2: Ty


@dataclass
class Binding:
    pass


@dataclass
class VarBinding(Binding):
    ty: Ty


Context = namedtuple("Context", "name, binding")


class TypeConv(Transformer):
    def bool_ty(self, _):
        return BoolTy()

    def arr_ty(self, children):
        return ArrowTy(children[0], children[1])


def find_binding(context: list[Context], name: str | Token):
    for i, binding in enumerate(reversed(context)):
        if binding.name == name:
            return i, binding
    raise ValueError


def parse_tree(tree: str | Tree, context: list[Context]) -> Node:
    match tree:
        case Tree(data="true"):
            return TrueNode()
        case Tree(data="false"):
            return FalseNode()
        case Tree(data="bind", children=[var_name, ty]):
            var_name = cast(Token, var_name)
            ty = cast(Ty, ty)
            context.append(Context(var_name, VarBinding(ty)))
            return BindNode(var_name, context[-1].binding)
        case Tree(data="abs", children=[name, ty, body]):
            name = cast(Token, name)
            ty = cast(Ty, ty)
            new_context = [*context, Context(name, VarBinding(ty))]
            return AbsNode(name, ty, parse_tree(body, new_context))
        case Tree(data="app", children=[c1, c2]):
            return AppNode(parse_tree(c1, context), parse_tree(c2, context))
        case Tree(data="var", children=[var_name]):
            var_name = cast(Token, var_name)
            try:
                idx, _ = find_binding(context, var_name)
            except ValueError:
                raise Exception(f"Unbound variable {var_name}")
            return VarNode(idx, len(context))
        case Tree(data="if_stmt", children=[cond, then, else_]):
            return IfNode(parse_tree(cond, context),
                          parse_tree(then, context),
                          parse_tree(else_, context))

    raise Exception("Unmatched", tree)


p = Lark(grammar, propagate_positions=True)


def parse(data: str):
    tree = p.parse(data)
    tree = TypeConv().transform(tree)
    context = []
    return [parse_tree(child, context) for child in tree.children]


if __name__ == '__main__':
    t = parse(""" 
        y: Bool;
        lambda x:Bool. x;
        (lambda x:Bool->Bool. if x false then true else false) 
            (lambda x:Bool. if x then false else true); 
        """)
    print(*t, sep="\n")
