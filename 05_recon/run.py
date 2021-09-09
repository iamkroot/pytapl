from dataclasses import dataclass
from itertools import count
from typing import Callable, Generator, cast

from parser import parse

from context import Context
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, BoolTy, FalseNode, IdTy, IfNode,
                   IsZeroNode, NatTy, Node, PredNode, SuccNode, TrueNode,
                   Ty, VarBinding, VarNode, ZeroNode)


class NoRuleApplies(Exception):
    pass


def node_map(on_var: Callable[[int, int, int], VarNode], node: Node, c: int):
    """Map over the node tree recursively, calling `on_var` for VarNode.

    c: Cutoff param
    """
    match node:
        case VarNode(idx, ctx_len):
            return on_var(c, idx, ctx_len)
        case AbsNode(orig_name, ty, body):
            return AbsNode(orig_name, ty, node_map(on_var, body, c + 1))
        case AppNode(t1, t2):
            return AppNode(node_map(on_var, t1, c), node_map(on_var, t2, c))
        case IfNode(cond, then, else_):
            return IfNode(node_map(on_var, cond, c),
                          node_map(on_var, then, c),
                          node_map(on_var, else_, c))
        case TrueNode() | FalseNode() | ZeroNode():
            return node
        case SuccNode(body) | PredNode(body) | IsZeroNode(body):
            return node.__class__(node_map(on_var, body, c))
    raise Exception(f"Unreachable {node}")


def shift(node: Node, d: int):
    """Shift the terms in node by d
    d: Shift value
    """
    def shift_var(c: int, idx: int, ctx_len: int) -> VarNode:
        return VarNode(idx + (d if idx >= c else 0), ctx_len + d)

    return node_map(shift_var, node, 0)


def subst(node: Node, j: int, s: Node):
    """Substitute j with s in node
    j: Orig val
    s: Substitution
    """
    def subst_var(c: int, idx: int, ctx_len: int) -> VarNode:
        return cast(VarNode, shift(s, c)) if idx == j + c else VarNode(idx, ctx_len)

    return node_map(subst_var, node, 0)


def subst_top(s: Node, node: Node):
    return shift(subst(node, 0, shift(s, 1)), -1)


def is_numval(node: Node):
    match node:
        case ZeroNode():
            return True
        case SuccNode(body):
            return is_numval(body)
    return False


def is_val(node: Node):
    if isinstance(node, (AbsNode, TrueNode, FalseNode)):
        return True
    if is_numval(node):
        return True
    return False


def eval_(node: Node, context: Context) -> Node:
    match node:
        case AppNode(AbsNode(_, _, body), t2) if is_val(t2):
            return subst_top(t2, body)
        case AppNode(t1, t2) if is_val(t1):
            return AppNode(t1, eval_(t2, context))
        case AppNode(t1, t2):
            return AppNode(eval_(t1, context), t2)
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


def uvargen():
    for n in count():
        yield IdTy(name=f"?X{n}")


@dataclass
class EqConstraint:
    lhs: Ty
    rhs: Ty


def recon(node: Node, context: Context, constraints: list[EqConstraint], vargen: Generator[IdTy, None, None]):
    match node:
        case VarNode(idx, _):
            return context.get_type(idx)
        case AbsNode(varname, ty, body):
            context.add_binding(varname, VarBinding(ty))
            ret_ty = recon(body, context, constraints, vargen)
            context.pop_binding()
            return ArrowTy(ty, ret_ty)
        case AppNode(t1, t2):
            ty1 = recon(t1, context, constraints, vargen)
            ty2 = recon(t2, context, constraints, vargen)
            ret_ty = next(vargen)
            constraints.append(EqConstraint(ty1, ArrowTy(ty2, ret_ty)))
            return ret_ty
        case ZeroNode():
            return NatTy()
        case SuccNode(body) | PredNode(body):
            ty = recon(body, context, constraints, vargen)
            constraints.append(EqConstraint(ty, NatTy()))
            return NatTy()
        case IsZeroNode(body):
            ty = recon(body, context, constraints, vargen)
            constraints.append(EqConstraint(ty, NatTy()))
            return BoolTy()
        case TrueNode() | FalseNode():
            return BoolTy()
        case IfNode(cond, then, else_):
            cond_ty = recon(cond, context, constraints, vargen)
            then_ty = recon(then, context, constraints, vargen)
            else_ty = recon(else_, context, constraints, vargen)
            constraints.append(EqConstraint(cond_ty, BoolTy()))
            constraints.append(EqConstraint(then_ty, else_ty))
            return then_ty
    raise Exception("Unreachable")


def run(cmd, context, constraints, vargen, mode="eval"):
    if isinstance(cmd, BindNode):
        context.add_binding(cmd.name, cmd.binding)
        print(cmd.name)
    elif mode == "eval":
        ty = recon(cmd, context, constraints, vargen)
        print(eval_node(cmd, context))
        print(ty)
        print(*constraints, sep="\n", end="\n\n")


def main():
    cmds = parse("""
        lambda x:Bool. x;
         (lambda x:Bool->Bool. if x false then true else false) 
           (lambda x:Bool. if x then false else true); 

        lambda x:Nat. succ x;
        (lambda x:Nat. succ (succ x)) (succ 0); 

        lambda x:A. x;

        (lambda x:X. lambda y:X->X. y x);
        (lambda x:X->X. x 0) (lambda y:Nat. y);
        """)
    ctx = Context()
    constraints = []
    vargen = uvargen()
    for cmd in cmds:
        run(cmd, ctx, constraints, vargen, "eval")


if __name__ == '__main__':
    main()
