from parser import parse
from typing import Callable, cast

from context import Context
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, BoolTy, FalseNode,
                   IfNode, Node, ProjNode, RecordNode, RecordTy, TopTy, TrueNode, Ty,
                   VarBinding, VarNode)


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
        case TrueNode() | FalseNode():
            return node
        case RecordNode(fields):
            return RecordNode({lab: node_map(on_var, field, c)
                               for lab, field in fields.items()})
        case ProjNode(rcd, lab):
            return ProjNode(node_map(on_var, rcd, c), lab)
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


def is_val(node: Node):
    return isinstance(node, (AbsNode, TrueNode, FalseNode, RecordNode))


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
        case ProjNode(RecordNode(fields), label):
            try:
                return fields[label]
            except KeyError:
                raise Exception(f"No {label=} in {node.rcd}")
        case ProjNode(t1, label):
            return ProjNode(eval_(t1, context), label)
    raise NoRuleApplies


def eval_node(node: Node, context: Context):
    while True:
        try:
            node = eval_(node, context)
        except NoRuleApplies:
            return node


def subtype(tyS: Ty, tyT: Ty) -> bool:
    """Returns True if tyS is a subtype of tyT"""
    if tyS == tyT:
        return True
    match (tyS, tyT):
        case (_, TopTy()):
            return True
        case (RecordTy(fieldsS), RecordTy(fieldsT)):
            return all(fieldsS.get(lab) == tyT_i for lab, tyT_i in fieldsT.items())
        case (ArrowTy(tyS1, tyS2), ArrowTy(tyT1, tyT2)):
            return subtype(tyT1, tyS1) and subtype(tyS2, tyT2)

    return False


def typeof(node: Node, context: Context) -> Ty:
    match node:
        case TrueNode() | FalseNode(): return BoolTy()
        case IfNode(cond, then, else_):
            if typeof(cond, context) == BoolTy():
                ret_ty = typeof(then, context)
                if ret_ty == typeof(else_, context):
                    return ret_ty
                else:
                    raise TypeError("Mismatched types of if-arms")
            else:
                raise TypeError("If condition should be bool")
        case VarNode(idx, _):
            return context.get_type(idx)
        case AbsNode(var_name, ty, body):
            new_context = context.clone()
            new_context.add_binding(var_name, VarBinding(ty))
            ret_ty = typeof(body, new_context)
            return ArrowTy(ty, ret_ty)
        case AppNode(t1, t2):
            ty1, ty2 = typeof(t1, context), typeof(t2, context)
            match ty1:
                case ArrowTy(ty11, ty12):
                    if subtype(ty2, ty11):
                        return ty12
                    else:
                        raise TypeError("Parameter type mismatch")
                case _: raise TypeError("First term of abstraction should be arrow type")
        case RecordNode(fields):
            return RecordTy({lab: typeof(field, context) for lab, field in fields.items()})
        case ProjNode(rcd, label):
            match typeof(rcd, context):
                case RecordTy(fields):
                    return fields[label]
                case _ as unknown:
                    raise Exception(f"Expected RecordTy instead of {unknown}")
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
        y: Top;
        lambda x:Top. x;

        (lambda x:Top. x) (lambda x:Top. x);

        (lambda x:Top->Top. x) (lambda x:Top. x);
        {x=lambda z:Top.z}.x;
        {x=lambda z:Top.z, y=lambda z:Top.z, w={x1=lambda m:Top.m}}.w.x1; // nested record

        (lambda r:{x:Top->Top}. r.x r.x) 
          {x=lambda z:Top.z, y=lambda z:Top.z};
        """)
    ctx = Context()
    for cmd in cmds:
        run(cmd, ctx, "eval")


if __name__ == '__main__':
    main()
