# WTF: Word Translation as in Forth

#### (c) 2022 by Paolo Caressa

WTF is a toy language implemented in a simple minded but easy-to-port non idiomatic Python as a sample of classic programming techniques as explained in the book by Chuck Moore [Programming a Problem Oriented Language](http://forth.org/POL.pdf).

The program `wtf.py` is an interpreter that compiles a source file into an inner threaded code which is then executed.

Currently the only documentation consists in slides presented at Codemotion Milan 2022.

Hope to put soon some more information, at least a reference to the language and its implementation: the next step is to implement the language in itself.

Enjoy,<br>
P

## Builtin words

### `(`

- Priority = 0
- Compile time: pushes on `_DSTK` a fake word (0, ")", NIL).
- Runtime: nothing.

### `)`

- Priority = 0
- Compile time: pops and compiles words from `_DSTK` to `_CSTK` until the fake word (0, ")", NIL) which is just removed. If no such fake word is found, an error is raised.
- Runtime: nothing.
