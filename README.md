# WTF: Word Translation as in Forth

#### (c) 2022 by Paolo Caressa

WTF is a toy language implemented in a simple minded but easy-to-port non idiomatic Python as a sample of classic programming techniques as explained in the book by Chuck Moore [Programming a Problem Oriented Language](http://forth.org/POL.pdf).

The program `wtf.py` is an interpreter that compiles a source file into an inner threaded code which is then executed.

Currently the only documentation consists in [slides presented at Codemotion Milan 2022](doc/Codemotion2022.pdf).

I hope to put soon some more information, at least a reference to the language and its implementation: the next step is to implement the language in itself.

Enjoy,<br>
P

## Builtin words

In the following, when describing the runtime operations, the term "stack" will mean `_DSTK`, TOS will refer to its topmost element, 2OS to the element below TOS, and so forth. When referring to other stacks, they will always be explicitly mentioned.

### `(`

- Priority = 0.
- Compile time: pushes a fake word (0, ")", NIL) on the stack.

### `)`

- Priority = 0.
- Compile time: pops and compiles words from `_DSTK` to `_CSTK` until the fake word (0, ")", NIL) which is just removed. If no such fake word is found, an error is raised.

### `*`

- Priority = 110.
- Runtime: removes TOS and 2OS, pushes 2OS * TOS.

### `**`

- Priority = 130.
- Runtime: removes TOS and 2OS, pushes 2OS raised to the power TOS.

### `+`

- Priority = 100.
- Runtime: removes TOS and 2OS, pushes 2OS + TOS.

### `-`

- Priority = 100.
- Runtime: removes TOS and 2OS, pushes 2OS - TOS.

### `<`

- Priority = 90.
- Runtime: removes TOS and 2OS, pushes 1 if 2OS < TOS else pushes 0.

### `<=`

- Priority = 90.
- Runtime: removes TOS and 2OS, pushes 1 if 2OS <= TOS else pushes 0.

### `<>`

- Priority = 90.
- Runtime: removes TOS and 2OS, pushes 1 if 2OS <> (not equal) TOS else pushes 0.

### `=`

- Priority = 90.
- Runtime: removes TOS and 2OS, pushes 1 if 2OS = TOS else pushes 0.

### `>`

- Priority = 90.
- Runtime: removes TOS and 2OS, pushes 1 if 2OS > TOS else pushes 0.

### `>=`

- Priority = 90.
- Runtime: removes TOS and 2OS, pushes 1 if 2OS >= TOS else pushes 0.

### `ABS`

- Priority = 200.
- Runtime: removes TOS, pushes TOS if TOS >= 0 else pushes -TOS.

### `AND`

- Priority = 70.
- Runtime: removes TOS and 2OS, pushes 1 if both TOS an 2OS are not 0, else pushes 0.

### `CMD`

- Priority = 0.
- Compile time: scans a word w and creates a new definition (w, 0, CMD, v) being v the address of a stack that will contain the code compiled until the matching `END`.

### `DEF` w `=` ...

- Priority = 0.
- Compile time: scans a word w and creates a new variable definition (w, 0, VPUSH, v) being v the address of a stack that will contain the code compiled until the matching `END`. Furthermore the `=` word is scanned, raising an error if not following w.
- Runtime: assigns to w the value of the expression following `=`.

### `DO`

- Priority = 0.
- Compile time: matches a previous `WHILE` or `TO` and prepare a match for the corresponding `DO`.
- Runtime: it the loop condition is not satisfied, jump after the matching `OD`.

    "ELIF", 0, ELIF, None,

    "ELSE", 0, ELSE, None,

    "END", 0, END, None,

    "FCLOSE", 10, FCLOSE, None,

    "FGET", 200, FGET, None,

    "FI", 0, FI, None,

    "FOPEN", 200, FOPEN, None,

    "FOR", 0, FOR, None,

    "FPUT", 10, FPUT, None,

    "FUNC", 0, BEGIN, 250,

    "IF", 0, IF, None,

    "INCLUDE", 0, INCLUDE, None,

    "LEN", 200, SLEN, None,


    "LET", 0, compile_assignment, VSTORE,

    "NEG", 120, NEG, None,

    "NEXT", 0, NEXT, None,

    "NIL", 255, PUSH, None,

    "NOT", 80, NOT, None,

    "OD", 0, OD, None,

    "OF", 0, compile_assignment, ISTORE,

    "OR", 60, OR, None,

    "POP", 200, SPOP, None,

    "PRINT", 10, PRINT, None,

    "PROC", 0, BEGIN, 10,

    "PUSH", 20, SPUSH, None,

    "RAND", 255, RAND, None,

    "ROUND", 200, ROUND, None,

    "STACK", 0, STACK, None,

    "THEN", 0, THEN, None,

    "TO", 0, TO, None,

    "TOS", 200, STOS, None,

    "WHILE", 0, WHILE, None,

    "[", 0, open_par, "]",

    "\"", 0, STRCONST, None,

    "\\", 0, COMMENT, None,

    "\n", 0, NEWLINE, None,

    "]", 0, CLOSEBRA, "]"
