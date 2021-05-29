from parser import AbsNode, AppNode, BindNode, Node, VarNode, parse


class NoRuleApplies(Exception):
    pass


def shift(node: Node, d: int, c: int = 0):
    """Shift the terms in node by d
    d: Shift value
    c: Cutoff param
    """
    match node:
        case VarNode(idx, ctx_len):
            return VarNode(idx + (d if idx >= c else 0), ctx_len + d)
        case AbsNode(orig_name, body):
            return AbsNode(orig_name, shift(body, d, c + 1))
        case AppNode(c1, c2):
            return AppNode(shift(c1, d, c), shift(c2, d, c))
    raise Exception("Unreachable")


def subst(node: Node, j: int, s: Node, c: int = 0):
    """Substitute j with s in node
    j: Orig val
    s: Substitution
    c: Cutoff param
    """
    match node:
        case VarNode(idx, ctx_len):
            return shift(s, c) if idx == j + c else VarNode(idx, ctx_len)
        case AbsNode(orig_name, body):
            return AbsNode(orig_name, subst(body, j, s, c + 1))
        case AppNode(c1, c2):
            return AppNode(subst(c1, j, s, c), subst(c2, j, s, c))
    raise Exception("Unreachable")


def substTop(s: Node, node: Node):
    return shift(subst(node, 0, shift(s, 1)), -1)


def is_val(node: Node):
    return isinstance(node, AbsNode)


def eval_(node: Node, bindings: list):
    match node:
        case AppNode(AbsNode(_, body), c2) if is_val(c2):
            return substTop(c2, body)
        case AppNode(c1, c2) if is_val(c1):
            return AppNode(c1, eval_(c2, bindings))
        case AppNode(c1, c2):
            return AppNode(eval_(c1, bindings), c2)
        case _: raise NoRuleApplies


def pprint_tree(tree: Node, bindings, end=""):
    # print(tree)
    match tree:
        case AbsNode(orig_name, body):
            while orig_name in bindings:
                orig_name += "'"
            print(f"(lambda {orig_name}. ", end="")
            new_bindings = [orig_name, *bindings]
            pprint_tree(body, new_bindings)
            print(")", end="")
        case AppNode(c1, c2):
            print("(", end="")
            pprint_tree(c1, bindings, end=" ")
            pprint_tree(c2, bindings)
            print(")", end="")
        case VarNode(idx, cnt):
            if cnt != len(bindings):
                print("ERROR")
            else:
                print(bindings[idx], end="")
    print("", end=end)


def main():
    inp = """/* Examples for testing */
        x/;
        x;
        w/;
        z/;

        w (lambda x. x);
        (lambda x. lambda x. x);
        lambda x. (lambda y . y x) (x z);
    """

    t = parse(inp)
    bindings = []
    for node in t:
        if isinstance(node, BindNode):
            bindings.insert(0, node.name)
            print(node.name)
            continue
        while True:
            try:
                node = eval_(node, bindings)
            except NoRuleApplies:
                break
        pprint_tree(node, bindings, end="\n")


if __name__ == '__main__':
    main()
