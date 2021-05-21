from lark import Lark

with open("grammar.lark") as f:
    grammar = f.read()


p = Lark(grammar)

parse = p.parse
