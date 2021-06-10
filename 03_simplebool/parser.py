import lark

with open("grammar.lark") as f:
    grammar = lark.Lark(f.read())


t = grammar.parse(""" lambda x:Bool. x;
 (lambda x:Bool->Bool->Bool->Bool. x);
 (lambda x:(Bool->Bool)->Bool->Bool. x);
 (lambda x:Bool->(Bool->Bool)->Bool. if x false then true else false) 
   (lambda x:Bool. if x then false else true);""")

print(t.pretty())