from typing import cast

from context import Context
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, BoolTy, FalseNode, ProjNode,
                   IfNode, Node, RecordNode, RecordTy, TopTy, BotTy, TrueNode, Ty,
                   VarBinding, VarNode)

with open("grammar.lark") as f:
    grammar = f.read()


class TypeTransformer(Transformer):
    def top_ty(self, _):
        return TopTy()

    def bot_ty(self, _):
        return BotTy()

    def bool_ty(self, _):
        return BoolTy()

    def rcd_ty(self, fields):
        field_types = {}
        for field in fields:
            match field:
                case Tree(data="field_ty", children=[label, ty]):
                    field_types[label] = ty
                case _ as unknown:
                    raise Exception(f"Expected field_ty instead of {unknown}")
        return RecordTy(field_types)

    def arr_ty(self, children):
        return ArrowTy(children[0], children[1])


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
        case Tree(data="record", children=fields):
            subnodes: dict[Token, Node] = {}
            for field in fields:
                match field:
                    case Tree(data="rcd_field", children=[label, value]):
                        parsed = parse_tree(value, context)
                        assert isinstance(label, Token)
                        subnodes[label] = parsed
                    case _:
                        raise Exception("Unmatched", field)
            return RecordNode(subnodes)
        case Tree(data="proj", children=[rcd, label]):
            assert isinstance(label, Token)
            return ProjNode(parse_tree(rcd, context), label)

    raise Exception("Unmatched", tree)


p = Lark(grammar, propagate_positions=True)


def parse(data: str):
    tree = p.parse(data)
    tree = TypeTransformer().transform(tree)
    context = Context()
    return [parse_tree(child, context) for child in tree.children]


if __name__ == '__main__':
    t = parse(r""" 
        y: Top;
        lambda x:Top. x;
        
        (lambda x:Top. x) (lambda x:Top. x);
        
        (lambda x:Top->Top. x) (lambda x:Top. x);

        if y then (lambda w:Bool.{x=w}.x)y else true;

        {x=lambda z:Top.z, y=lambda z:Top.z, w={x1=lambda m:Top.m}}; // nested record

        (lambda r:{x:Top->Top}. r.x r.x) 
          {x=lambda z:Top.z, y=lambda z:Top.z}; 

        lambda x:Bot. x;
        lambda x:Bot. x x; 
        """)
    print(*t, sep="\n\n")
