import abc
from dataclasses import dataclass
from typing import cast
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree

with open("grammar.lark") as f:
    grammar = f.read()


@dataclass
class Node(abc.ABC):
    pass


@dataclass
class VarNode(Node):
    idx: int
    ctx_len: int = -1


@dataclass
class AbsNode(Node):
    orig_name: str
    body: Node


@dataclass
class AppNode(Node):
    child1: Node
    child2: Node


@dataclass
class BindNode(Node):
    name: Token


def find_binding(bindings: list[Token], name: Token):
    for i, binding in enumerate(reversed(bindings)):
        if binding == name:
            return i
    raise ValueError


def parse_tree(tree: str | Tree, bindings: list[Token]) -> Node:
    match tree:
        case Tree(data="bind", children=[var_name]):
            var_name = cast(Token, var_name)
            # bindings.insert(0, var_name)
            bindings.append(var_name)
            return BindNode(var_name)
        case Tree(data="abs", children=[name, body]):
            name = cast(Token, name)
            # new_bindings = [name, *bindings]
            new_bindings = bindings.copy()
            new_bindings.append(name)
            return AbsNode(name, parse_tree(body, new_bindings))
        case Tree(data="app", children=[c1, c2]):
            return AppNode(parse_tree(c1, bindings), parse_tree(c2, bindings))
        case Tree(data="var", children=[var_name]):
            var_name = cast(Token, var_name)
            try:
                idx = find_binding(bindings, var_name)
            except ValueError:
                raise Exception(f"Unbound variable {var_name}")
            return VarNode(idx, len(bindings))

    raise Exception("Unmatched", tree)


p = Lark(grammar, propagate_positions=True)


def parse(data: str):
    tree = p.parse(data, )
    bindings = []
    return [parse_tree(child, bindings) for child in tree.children]


if __name__ == '__main__':
    t = parse("""/* Examples for testing */
    x/;
    x;
    w/;
    z/;

    w (lambda x. x);
    (lambda x. lambda x.x) (lambda x. x x);
    lambda x. (lambda y . y x) (x x);

    """)
    print(t)
