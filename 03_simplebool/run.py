from parser import parse

from context import Context
from nodes import (AbsNode, AppNode, ArrowTy, BindNode, BoolTy, FalseNode,
                   IfNode, Node, TrueNode, VarBinding, VarNode)


def typeof(node: Node, context: Context):
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
                    if ty11 == ty2:
                        return ty12
                    else:
                        raise TypeError("Parameter type mismatch")
                case _: raise TypeError("First term of abstraction should be arrow type")


def run(cmd, context):
    if isinstance(cmd, BindNode):
        context.add_binding(cmd.name, cmd.binding)
        print(cmd.name)
    else:
        ty = typeof(cmd, context)
        print(ty)


def main():
    cmds = parse(""" 
        y: Bool;
        if y then true else false;
        lambda x:Bool. x;
        (lambda x:Bool->Bool. if x false then true else false) 
            (lambda x:Bool. if x then false else true); 
        """)
    ctx = Context()
    for cmd in cmds:
        run(cmd, ctx)


if __name__ == '__main__':
    main()
