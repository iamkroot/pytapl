from typing import cast

from context import Context
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, BoolTy, FalseNode, IdTy, IfNode,
                   IsZeroNode, NatTy, Node, PredNode, SuccNode, TrueNode, Ty,
                   VarBinding, VarNode, ZeroNode)

with open("grammar.lark") as f:
    grammar = f.read()


class TypeTransformer(Transformer):
    def bool_ty(self, _):
        return BoolTy()

    def nat_ty(self, _):
        return NatTy()

    def id_ty(self, children):
        return IdTy(children[0])

    def arr_ty(self, children):
        return ArrowTy(children[0], children[1])


def _num_to_church(num: int):
    assert num >= 0
    if num == 0:
        return ZeroNode()
    return SuccNode(_num_to_church(num - 1))


def parse_tree(tree: str | Tree, context: Context) -> Node:
    match tree:
        case Tree(data="true"):
            return TrueNode()
        case Tree(data="false"):
            return FalseNode()
        case Tree(data="bind", children=[var_name, ty]):
            var_name = cast(Token, var_name)
            ty = cast(Ty, ty)
            context.add_binding(var_name, VarBinding(ty))
            return BindNode(var_name, context.top.binding)
        case Tree(data="abs", children=[name, ty, body]):
            name = cast(Token, name)
            ty = cast(Ty, ty)
            new_context = context.clone()
            new_context.add_binding(name, VarBinding(ty))
            return AbsNode(name, ty, parse_tree(body, new_context))
        case Tree(data="app", children=[c1, c2]):
            return AppNode(parse_tree(c1, context), parse_tree(c2, context))
        case Tree(data="var", children=[var_name]):
            var_name = cast(Token, var_name)
            try:
                idx, _ = context.find_binding(var_name)
            except ValueError:
                raise Exception(f"Unbound variable {var_name}")
            return VarNode(idx, len(context))
        case Tree(data="if_stmt", children=[cond, then, else_]):
            return IfNode(parse_tree(cond, context),
                          parse_tree(then, context),
                          parse_tree(else_, context))
        case Tree(data="nat", children=[number]):
            assert isinstance(number, str)
            num = int(number)
            return _num_to_church(num)
        case Tree(data="succ", children=[child]):
            return SuccNode(parse_tree(child, context))
        case Tree(data="pred", children=[child]):
            return PredNode(parse_tree(child, context))
        case Tree(data="iszero", children=[child]):
            return IsZeroNode(parse_tree(child, context))
    raise Exception("Unmatched", tree)


p = Lark(grammar, propagate_positions=True)


def parse(data: str):
    tree = p.parse(data)
    tree = TypeTransformer().transform(tree)
    context = Context()
    return [parse_tree(child, context) for child in tree.children]


if __name__ == '__main__':
    t = parse(r""" 
        lambda x:Bool. x;
         (lambda x:Bool->Bool. if x false then true else false) 
           (lambda x:Bool. if x then false else true); 

        lambda x:Nat. succ x;
        (lambda x:Nat. succ (succ x)) (succ 0); 

        lambda x:A. x;

        (lambda x:X. lambda y:X->X. y x);
        (lambda x:X->X. x 0) (lambda y:Nat. y); 
        """)
    print(*t, sep="\n\n")
