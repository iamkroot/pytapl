from typing import Callable, cast

from parser import parse

from context import Context
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, BoolTy, ExisPackNode, ExisTy,
                   ExisUnpackNode, FalseNode, IfNode, IsZeroNode, LetNode, NatTy, Node,
                   PredNode, SuccNode, TrueNode, Ty, TyVar, TyVarBinding, TypeAbsNode, TypeAppNode,
                   UnivTy, VarBinding, VarNode, ZeroNode)


class NoRuleApplies(Exception):
    pass


def node_map(on_var: Callable[[int, int, int], VarNode],
             on_type: Callable[[Ty, int], Ty],
             node: Node, c: int):
    """Map over the node tree recursively, calling `on_var` for VarNode and
    `on_type` for types.

    c: Cutoff param, counts the length of context
    """

    def walk(node, c):
        match node:
            case VarNode(idx, ctx_len):
                return on_var(c, idx, ctx_len)
            case AbsNode(orig_name, ty, body):
                return AbsNode(orig_name, on_type(ty, c), walk(body, c + 1))
            case AppNode(t1, t2):
                return AppNode(walk(t1, c), walk(t2, c))
            case LetNode(name, init, body):
                return LetNode(name, walk(init, c), walk(body, c + 1))
            case TypeAbsNode(name, body):
                return TypeAbsNode(name, walk(body, c + 1))
            case TypeAppNode(body, ty):
                return TypeAppNode(walk(body, c), on_type(ty, c))
            case ExisPackNode(exis_ty, body, ty):
                return ExisPackNode(on_type(exis_ty, c), walk(body, c), on_type(ty, c))
            case ExisUnpackNode(tyname, varname, init, body):
                return ExisUnpackNode(tyname, varname, walk(init, c), walk(body, c + 2))
            case IfNode(cond, then, else_):
                return IfNode(walk(cond, c),
                              walk(then, c),
                              walk(else_, c))
            case TrueNode() | FalseNode() | ZeroNode():
                return node
            case SuccNode(body) | PredNode(body) | IsZeroNode(body):
                return node.__class__(walk(body, c))
        raise Exception(f"Unreachable {node}")
    return walk(node, c)


def type_map(on_tyvar: Callable[[int, int, int], TyVar], ty: Ty, c: int):
    match ty:
        case TyVar(idx, ctx_len):
            return on_tyvar(c, idx, ctx_len)
        case ArrowTy(ty1, ty2):
            return ArrowTy(type_map(on_tyvar, ty1, c), type_map(on_tyvar, ty2, c))
        case UnivTy(name, body) | ExisTy(name, body):
            return ty.__class__(name, type_map(on_tyvar, body, c + 1))
        case BoolTy() | NatTy():
            return ty
    raise Exception(f"Unreachable {ty}")


def node_shift(node: Node, d: int, c: int = 0):
    """Shift the terms in node by d
    d: Shift value
    """
    def shift_var(c: int, idx: int, ctx_len: int) -> VarNode:
        return VarNode(idx + (d if idx >= c else 0), ctx_len + d)

    def on_type(ty: Ty, c: int):
        return type_shift(ty, d, c)

    return node_map(shift_var, on_type, node, c)


def node_subst(node: Node, j: int, s: Node, c:int = 0):
    """Substitute j with s in node
    j: Orig val
    s: Substitution
    """
    def subst_var(c: int, idx: int, ctx_len: int) -> VarNode:
        return cast(VarNode, node_shift(s, c)) if idx == j + c else VarNode(idx, ctx_len)

    def on_type(ty: Ty, _: int):
        return ty

    return node_map(subst_var, on_type, node, c)


def node_subst_top(s: Node, node: Node):
    return node_shift(node_subst(node, 0, node_shift(s, 1)), -1)


def type_shift(ty: Ty, d: int, c: int = 0):
    def shift_tyvar(c:int, idx: int, ctx_len: int) -> TyVar:
        tyvar = TyVar(idx + (d if idx >= c else 0), ctx_len + d)
        if tyvar.idx < 0:
            raise TypeError("Scoping error!")
        return tyvar

    return type_map(shift_tyvar, ty, c)


def type_subst(ty: Ty, s: Ty, j: int):
    def subst_tyvar(c: int, idx: int, ctx_len: int) -> TyVar:
        return cast(TyVar, type_shift(s, c)) if idx == c else TyVar(idx, ctx_len)

    return type_map(subst_tyvar, ty, j)


def type_subst_top(ty: Ty, s: Ty):
    """Substitute top TyVar in ty with s"""
    return type_shift(type_subst(ty, type_shift(s, 1), 0), -1)


def type_node_subst(ty: Ty, node: Node, j: int):
    """Substitute all types at index j with ty in node"""
    def make_var(_: int, idx: int, ctx_len: int):
        return VarNode(idx, ctx_len)  # no change to node

    def subst_ty(orig_ty: Ty, c: int):
        return type_subst(orig_ty, ty, c)

    return node_map(make_var, subst_ty, node, j)


def type_node_subst_top(ty: Ty, node: Node):
    return node_shift(type_node_subst(type_shift(ty, 1), node, 0), -1)


def is_numval(node: Node):
    match node:
        case ZeroNode():
            return True
        case SuccNode(body):
            return is_numval(body)
    return False


def is_val(node: Node):
    if isinstance(node, (AbsNode, TrueNode, FalseNode, TypeAbsNode, ExisPackNode)):
        return True
    if is_numval(node):
        return True
    return False


def eval_(node: Node, context: Context) -> Node:
    match node:
        case AppNode(AbsNode(_, _, body), t2) if is_val(t2):
            return node_subst_top(t2, body)
        case AppNode(t1, t2) if is_val(t1):
            return AppNode(t1, eval_(t2, context))
        case AppNode(t1, t2):
            return AppNode(eval_(t1, context), t2)
        case LetNode(_, init, body) if is_val(init):
            return node_subst_top(init, body)
        case LetNode(name, init, body):
            return LetNode(name, eval_(init, context), body)
        case TypeAppNode(TypeAbsNode(_, body), ty):
            return type_node_subst_top(ty, body)
        case TypeAppNode(body, ty):
            return TypeAppNode(eval_(body, context), ty)
        case ExisUnpackNode(_, _, ExisPackNode(exis_ty, init_body, _), body) if \
            is_val(init_body):
            body = node_subst_top(node_shift(init_body, 1), body)
            return type_node_subst_top(exis_ty, body)
        case ExisUnpackNode(tyname, varname, init_body, body):
            return ExisUnpackNode(tyname, varname, eval_(init_body, context), body)
        case ExisPackNode(exis_ty, body, ty):
            return ExisPackNode(exis_ty, eval_(body, context), ty)
        case IfNode(TrueNode(), then, else_):
            return then
        case IfNode(FalseNode(), then, else_):
            return else_
        case IfNode(cond, then, else_):
            return IfNode(eval_(cond, context), then, else_)
        case SuccNode(PredNode(body)) | PredNode(SuccNode(body)) if is_numval(body):
            return body
        case PredNode(ZeroNode()):
            return ZeroNode()
        case SuccNode(body):
            return SuccNode(eval_(body, context))
        case PredNode(body):
            return PredNode(eval_(body, context))
        case IsZeroNode(ZeroNode()):
            return TrueNode()
        case IsZeroNode(SuccNode(body)) if is_numval(body):
            return FalseNode()
    raise NoRuleApplies


def eval_node(node: Node, context: Context):
    while True:
        try:
            node = eval_(node, context)
        except NoRuleApplies:
            return node


def typeof(node: Node, context: Context):
    match node:
        case TrueNode() | FalseNode():
            return BoolTy()
        case ZeroNode():
            return NatTy()
        case PredNode(node) | SuccNode(node):
            if typeof(node, context) != NatTy():
                raise TypeError("body should be NatTy")
            return NatTy()
        case IfNode(cond, then, else_):
            match typeof(cond, context):
                case BoolTy():
                    then_ty = typeof(then, context)
                    else_ty = typeof(else_, context)
                    if then_ty != else_ty:
                        raise TypeError("If arms should have same type")
                    return then_ty
                case _:
                    raise TypeError("If condition should be bool")
        case VarNode(idx, _):
            return context.get_type(idx)
        case AbsNode(var_name, ty, body):
            context.add_binding(var_name, VarBinding(ty))
            ret_ty = typeof(body, context)
            context.pop_binding()
            return ArrowTy(ty, ret_ty)
        case AppNode(t1, t2):
            ty1, ty2 = typeof(t1, context), typeof(t2, context)
            match ty1:
                case ArrowTy(ty11, ty12):
                    if ty11 == ty2:
                        return ty12
                    else:
                        raise TypeError("Parameter type mismatch")
                case _: raise TypeError("First term of abstraction should be arrow type")
        case TypeAbsNode(name, body):
            context.add_binding(name, TyVarBinding())
            body_ty = typeof(body, context)
            context.pop_binding()
            return UnivTy(name, body_ty)
        case TypeAppNode(body, ty):
            body_ty = typeof(body, context)
            match body_ty:
                case UnivTy(name, internal_ty):
                    return type_subst_top(internal_ty, ty)
                case _: raise TypeError("Type Application needs universal type")
        case ExisPackNode(exis_ty, body, ty):
            if not isinstance(ty, ExisTy):
                raise TypeError("Existential type expected")
            real_body_ty = typeof(body, context)
            subst_body_ty = type_subst_top(ty.body, exis_ty)
            if real_body_ty != subst_body_ty:
                raise TypeError("Doesn't match declared type")
            return ty
        case ExisUnpackNode(tyname, varname, init, body):
            init_ty = typeof(init, context)
            if not isinstance(init_ty, ExisTy):
                raise TypeError("Unpack needs existential type, got", init_ty)
            context.add_binding(tyname, TyVarBinding())
            context.add_binding(varname, VarBinding(init_ty.body))
            body_ty = typeof(body, context)
            context.pop_binding()
            context.pop_binding()
            return type_shift(body_ty, -2)

    raise Exception(f"Unknown node {node}")


def run(cmd, context, mode="eval"):
    if isinstance(cmd, BindNode):
        context.add_binding(cmd.name, cmd.binding)
        print(cmd.name)
    elif mode == "eval":
        print(eval_node(cmd, context))
    elif mode == "type":
        print(typeof(cmd, context))


def main():
    cmds = parse("""
        lambda x:Bool. x;
         (lambda x:Bool->Bool. if x false then true else false) 
           (lambda x:Bool. if x then false else true); 

        lambda x:Nat. succ x;
        (lambda x:Nat. succ (succ x)) (succ 0);
        lambda X. lambda x:X. x; 
        let {X,x}=({*Nat,0} as {Some X,X}) in 0; 
        """)
    ctx = Context()
    for cmd in cmds:
        run(cmd, ctx, "type")


if __name__ == '__main__':
    main()
