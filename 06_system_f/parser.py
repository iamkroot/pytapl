from context import Context
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, Binding, BoolTy, ExisPackNode,
                   ExisTy, ExisUnpackNode, FalseNode, IfNode, IsZeroNode, LetNode,
                   NatTy, Node, PredNode, SuccNode, TrueNode, Ty, TyVar, TyVarBinding,
                   TypeAbsNode, TypeAppNode, UnivTy, VarBinding, VarNode, ZeroNode)

with open("grammar.lark") as f:
    grammar = f.read()


def _num_to_church(num: int):
    assert num >= 0
    if num == 0:
        return ZeroNode()
    return SuccNode(_num_to_church(num - 1))


def parse_type(tree: str | Tree, context: Context) -> Ty:
    match tree:
        case Tree(data="bool_ty"):
            return BoolTy()
        case Tree(data="nat_ty"):
            return NatTy()
        case Tree(data="arr_ty", children=[ty1, ty2]):
            return ArrowTy(parse_type(ty1, context), parse_type(ty2, context))
        case Tree(data="univ_ty", children=[name, body]):
            assert isinstance(name, Token)
            context.add_binding(name, TyVarBinding())
            ty = UnivTy(name, parse_type(body, context))
            context.pop_binding()
            return ty
        case Tree(data="exis_ty", children=[name, body]):
            assert isinstance(name, Token)
            context.add_binding(name, TyVarBinding())
            ty = ExisTy(name, parse_type(body, context))
            context.pop_binding()
            return ty
        case Tree(data="ty_var", children=[name]):
            assert isinstance(name, Token)
            try:
                idx, _ = context.find_binding(name)
            except ValueError:
                raise Exception(f"Unbound type variable {name}")
            return TyVar(idx, len(context))
    raise Exception("Unmatched", tree)


def parse_node(tree: str | Tree, context: Context) -> Node:
    match tree:
        case Tree(data="true"):
            return TrueNode()
        case Tree(data="false"):
            return FalseNode()
        case Tree(data="bind", children=[var_name, ty]):
            assert isinstance(var_name, Token)
            ty = parse_type(ty, context)
            context.add_binding(var_name, VarBinding(ty))
            return BindNode(var_name, context.top.binding)
        case Tree(data="abs", children=[name, ty, body]):
            assert isinstance(name, Token)
            ty = parse_type(ty, context)
            context.add_binding(name, VarBinding(ty))
            node = AbsNode(name, ty, parse_node(body, context))
            context.pop_binding()
            return node
        case Tree(data="let", children=[name, init, body]):
            assert isinstance(name, Token)
            init_node = parse_node(init, context)
            context.add_binding(name, Binding())
            node = LetNode(name, init_node, parse_node(body, context))
            context.pop_binding()
            return node
        case Tree(data="app", children=[c1, c2]):
            return AppNode(parse_node(c1, context), parse_node(c2, context))
        case Tree(data="var", children=[var_name]):
            assert isinstance(var_name, Token)
            try:
                idx, _ = context.find_binding(var_name)
            except ValueError:
                raise Exception(f"Unbound variable {var_name}")
            return VarNode(idx, len(context))
        case Tree(data="type_abs", children=[typename, body]):
            assert isinstance(typename, Token)
            context.add_binding(typename, TyVarBinding())
            node = TypeAbsNode(typename, parse_node(body, context))
            context.pop_binding()
            return node
        case Tree(data="type_app", children=[body, ty]):
            return TypeAppNode(parse_node(body, context), parse_type(ty, context))
        case Tree(data="exis_pack", children=[exis_ty, body, ty]):
            return ExisPackNode(parse_type(exis_ty, context),
                                parse_node(body, context),
                                parse_type(ty, context))
        case Tree(data="exis_unpack", children=[tyname, varname, init, body]):
            assert isinstance(tyname, Token)
            assert isinstance(varname, Token)
            init_node = parse_node(init, context)
            context.add_binding(tyname, TyVarBinding())
            context.add_binding(varname, Binding())
            node = ExisUnpackNode(tyname, varname, init_node, parse_node(body, context))
            context.pop_binding()
            context.pop_binding()
            return node
        case Tree(data="if_stmt", children=[cond, then, else_]):
            return IfNode(parse_node(cond, context),
                          parse_node(then, context),
                          parse_node(else_, context))
        case Tree(data="nat", children=[number]):
            assert isinstance(number, str)
            num = int(number)
            return _num_to_church(num)
        case Tree(data="succ", children=[child]):
            return SuccNode(parse_node(child, context))
        case Tree(data="pred", children=[child]):
            return PredNode(parse_node(child, context))
        case Tree(data="iszero", children=[child]):
            return IsZeroNode(parse_node(child, context))
    raise Exception("Unmatched", tree)


p = Lark(grammar, propagate_positions=True)


def parse(data: str):
    tree = p.parse(data)
    context = Context()
    return [parse_node(child, context) for child in tree.children]


if __name__ == '__main__':
    t = parse(""" 
        lambda a.a;
        lambda x:Bool. x;
         (lambda x:Bool->Bool. if x false then true else false) 
           (lambda x:Bool. if x then false else true); 
        lambda x:Nat. succ x;
        (lambda x:Nat. succ (succ x)) (succ 0); 
        lambda a: All X. All Y.X->X.a;
        lambda X.lambda x:X->X->(All Y.Y)->X.x;
        """)
    print(*t, sep="\n\n")
