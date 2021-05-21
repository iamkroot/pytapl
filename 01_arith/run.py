from parser import parse
from lark import Tree

def is_numval(term: Tree | str):
    match term:
        case "zero": return True
        case Tree(data="zero"): return True
        case Tree(data="succ", children=[child]) if is_numval(child): return True
    return False

def is_val(term: Tree | str):
    match term:
        case "true" | "false": return True
        case t: return is_numval(t)

class NoRuleApplies(Exception):
    pass

def eval_(term):
    match term:
        case Tree(data="if_stmt", children=["true", t2, _]): return t2
        case Tree(data="if_stmt", children=["false", _, t3]): return t3
        case Tree(data="if_stmt", children=[t1, t2, t3]): 
            return Tree(data="if_stmt", children=[eval_(t1), t2, t3])
        case Tree(data="succ", children=[t1]):
            return Tree(data="succ", children=[eval_(t1)])
        case Tree(data="pred", children=[Tree(data="zero")]):
            return "zero"
        case Tree(data="pred", children=[Tree(data="succ", children=[t1])]) if is_numval(t1):
            return t1
        case Tree(data="iszero", children=[Tree(data="zero")]):
            return "true"
        case Tree(data="iszero", children=[Tree(data="succ", children=[t1])]) if is_numval(t1):
            return "false"
        case Tree(data="iszero", children=[t1]):
            return Tree(data="iszero", children=[eval_(t1)])
        case _: raise NoRuleApplies

inp = """true;
if false then true else false; 

0; 
succ (pred 0);
iszero (pred (succ (succ 0))); 
"""

t = parse(inp)
for c in t.children:
    while True:
        try:
            c = eval_(c)
        except NoRuleApplies:
            break
    print(c)
