from lark import Lark

with open("grammar.lark") as f:
    grammar = f.read()


p = Lark(grammar)

parse = p.parse

if __name__ == '__main__':
    t = parse("""/* Examples for testing */
    x/;
    x;

    lambda x. x;
    (lambda x. x) (lambda x. x x); 
    x y z;
    w (lambda x. (lambda y . y x) x z);
    """)

    print(t.pretty())
