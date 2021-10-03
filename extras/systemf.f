/* Run with fullomega checker */

Pair = lambda X. lambda Y. All R. (X->Y->R) -> R;

pair = lambda X.lambda Y.lambda x:X.lambda y:Y.lambda R.lambda p:X->Y->R.p x y;

f = lambda X.lambda Y.lambda f:Pair X Y. f;

fst = lambda X.lambda Y.lambda p:Pair X Y.p [X] (lambda x:X.lambda y:Y.x);
snd = lambda X.lambda Y.lambda p:Pair X Y.p [Y] (lambda x:X.lambda y:Y.y);

pr = pair [Nat] [Bool] 0 false;
fst [Nat] [Bool] pr;
snd [Nat] [Bool] pr;

List = lambda X. All R. (X->R->R) -> R -> R; 

diverge =
lambda X.
  lambda _:Unit.
  fix (lambda x:X. x);

nil = lambda X.
      (lambda R. lambda c:X->R->R. lambda n:R. n)
      as List X; 

cons = 
lambda X.
  lambda hd:X. lambda tl: List X.
     (lambda R. lambda c:X->R->R. lambda n:R. c hd (tl [R] c n))
     as List X; 

isnil =  
lambda X. 
  lambda l: List X. 
    l [Bool] (lambda hd:X. lambda tl:Bool. false) true; 

head = 
lambda X. 
  lambda l: List X. 
    (l [Unit->X] (lambda hd:X. lambda tl:Unit->X. lambda _:Unit. hd) (diverge [X]))
    unit; 

head2 = lambda X.lambda l:List X.lambda default:X.
  l[X] (lambda hd:X.lambda tl:X.hd) default;

tail =  
lambda X.  
  lambda l: List X. 
    (fst [List X] [List X] ( 
      l [Pair (List X) (List X)]
        (lambda hd: X. lambda tl: Pair (List X) (List X). 
          pair [List X] [List X] 
            (snd [List X] [List X] tl)  
            (cons [X] hd (snd [List X] [List X] tl))) 
        (pair [List X] [List X] (nil [X]) (nil [X]))))
    as List X; 

a = (cons[Nat] 1(cons[Nat] 2 ( cons[Nat] 4 (nil[Nat]))));
b = (cons[Nat] 3(cons[Nat] 6 ( cons[Nat] 7 (nil[Nat]))));
c = (cons[Nat] 8(cons[Nat] 6 ( cons[Nat] 7 (nil[Nat]))));


rev = 
lambda X.
  fix (
    lambda r: List X -> List X -> List X.
      (lambda l: List X.
        lambda res: List X.
          if isnil[X] l
            then res
            else (r (tail[X] l)) (cons[X] (head[X] l) res)
      )
  );
reverse = lambda X. lambda l:List X. rev[X] l (nil[X]);

/* merge two sorted lists */
merge = lambda X.lambda cmp: (X->X->Bool).
  fix(lambda m: List X->List X->List X.
    lambda l1: List X.lambda l2:List X.
      if (isnil[X] l1)
        then l2
      else 
        if (isnil[X] l2)
          then l1
          else
            if (cmp (head[X] l1) (head[X] l2))
              then (cons[X] (head[X] l2) (m l1 (tail[X] l2)))
              else (cons[X] (head[X] l1) (m (tail[X] l1) l2))
  );


/* return x == y */
eq = fix (lambda e: Nat->Nat->Bool.
  lambda x:Nat. lambda y:Nat.
    if iszero x
      then (iszero y)
      else if iszero y
        then false
        else e (pred x) (pred y));

/* return x > y */
gt = fix (lambda g: Nat->Nat->Bool.
  lambda x:Nat. lambda y:Nat.
    if iszero x
      then false
      else if iszero y
        then true
        else g (pred x) (pred y));

/* merge[Nat] gt a b; */

len = lambda X.fix(lambda len: List X->Nat.
  lambda l:List X.
  if isnil[X] l
    then 0
    else succ(len (tail[X] l)));

_splitat = lambda X. lambda n:Nat.
  fix (lambda s:List X -> Nat -> List X ->(Pair (List X) (List X)).
    lambda l:List X.
      lambda m:Nat.
        lambda firstpart:List X.
          if (eq m n)
            then ((pair [List X] [List X]) (reverse[X] firstpart) l)
            else (s (tail[X] l) (succ m) (cons[X] (head[X] l) firstpart))
    );

splitat = lambda X. lambda n:Nat. lambda l: List X. 
  if (gt n (len[X] l))
    then (diverge [Pair (List X) (List X)]) unit
    else _splitat[X] n l 0 (nil[X]);

by2 = lambda n:Nat.
  (fix (lambda f: Nat->Nat->Nat.
      lambda a:Nat.lambda b:Nat.
        if (gt b n)
          then a
          else f (succ a) (succ (succ b)))) 0 2;

sort = lambda X. lambda cmp: (X->X->Bool).
  fix (lambda s: List X -> List X.
    lambda l: List X.
      if (isnil[X] l)
        then l
        else if (eq 1 (len[X] l)) then l
        else 
        (lambda parts: Pair (List X) (List X).
          merge[X] 
            cmp
            (s (fst[List X][List X] parts))
            (s (snd[List X][List X] parts))
        )
        (splitat[X] (by2 (len[X] l)) l)
  );


CBool = All X. X->X->X;
tru = (lambda X.lambda t:X.lambda f:X.t) as CBool;
fls = (lambda X.lambda t:X.lambda f:X.f) as CBool;
cbool2bool = lambda b:CBool. b[Bool] true false;

/* Exercise 23.4.5 */
/* solution 1 */
and = lambda l:CBool.lambda r:CBool.(
  lambda X.lambda t:X.lambda f:X.
    (l[X] (r[X] t f) f)
  ) as CBool;

/* solution 2 */
and = lambda l:CBool.lambda r:CBool.(lambda X.(l[X->X->X])(r[X])(fls[X])) as CBool;

cbool2bool(and tru fls);

CNat = All X. (X->X) -> X -> X;
c0 = (lambda X. lambda s:X->X.lambda z: X. z) as CNat;
c1 = (lambda X. lambda s:X->X.lambda z: X. s z) as CNat;
c2 = (lambda X. lambda s:X->X.lambda z: X. s (s z)) as CNat;

csucc = lambda n: CNat.(lambda X.lambda s: X->X.lambda z:X. s (n[X] s z)) as CNat;
cplus = lambda m: CNat.lambda n:CNat.(lambda X.lambda s:X->X.lambda z:X. n[X] s (m[X] s z)) as CNat;

cnat2nat = lambda n:CNat. n[Nat] (lambda x:Nat.succ x) 0; 

/* Exercise 23.4.6 */
isczero = lambda n:CNat. (n[CBool]) (lambda x:CBool.fls) tru;

/* Exercise 23.4.8 */
PairNat = All X. (CNat -> CNat -> X) -> X;

pairNat = lambda m:CNat.lambda n:CNat.(
  lambda X.lambda f: CNat->CNat->X.f m n) as PairNat;

fstNat = lambda p:PairNat.(p[CNat]) (tru[CNat]);
sndNat = lambda p:PairNat.(p[CNat]) (fls[CNat]);

/* Exercise 23.4.9 */
_predf = lambda p:PairNat. (lambda fst:CNat. pairNat (csucc fst) fst)(fstNat p);
cpred = lambda n:CNat. sndNat (n[PairNat] _predf (pairNat c0 c0));
cnat2nat (cpred c2);

tru[Nat] 1;
/* Exercise 23.4.10 */
id = lambda X.lambda x:X.x;
/* vpred = λn. λs. λz. n (λp. λq. q (p s)) ((λx. λy. x)z) (λx. x) */

vpred = lambda n:CNat.
  (lambda X.lambda s:X->X.lambda z:X.
    (n[(X->X)->X]
      (lambda p: (X->X)->X.lambda q:X->X. q (p s))
      (lambda y:X->X. z))
    (lambda x:X.x))
  as CNat;
cnat2nat(vpred c2);

not = lambda b:Bool.if b then false else true;

/* Exercise 23.4.12 */
/* this insert is O(n^2) due to tail */
insert = lambda X. lambda cmp: X->X->Bool.lambda l:List X.lambda x:X.
  (l[List X]
    (lambda hd: X.lambda tl:List X.
      if cmp hd (head[X] tl) /* if hd > head(tl) */
        then (cons[X] (head[X] tl) (cons[X] hd (tail[X] tl))) /* head(tl)::hd::tail(tl) */
        else (cons[X] hd tl) /* hd::tail */
      )
    (cons[X] x (nil[X]))
  );

/* O(n) insert by keeping tail around */
insert = lambda X. lambda cmp: X->X->Bool.lambda l:List X.lambda x:X.
  fst[List X][List X](l[Pair (List X) (List X)]
    (lambda hd: X.lambda ltl:Pair (List X) (List X).
      if cmp hd (head[X] (fst[List X][List X] ltl)) /* if hd > head(tl) */
        then (pair[List X][List X]
          (cons[X] (head[X] (fst[List X][List X] ltl)) (cons[X] hd (snd[List X][List X] ltl))) /* head(tl)::hd::tail(tl) */
          (cons[X] hd (snd[List X][List X] ltl))
        )
        else (pair[List X][List X]
          (cons[X] hd (fst[List X][List X] ltl)) /* hd::tail */
          (fst[List X][List X] ltl)
        )
    )
    (pair [List X][List X] (cons[X] x (nil[X])) (nil[X]))
  );

sort = lambda X.lambda cmp: X->X->Bool.lambda l:List X.
  (l[List X]
    (lambda hd:X.lambda tl:List X.
      ((insert[X]) cmp tl hd))
    ((nil[X]) as (List X))
  );

c;
sort[Nat] gt c;