"""
    WTF: Word Translation as in Forth
    (c) 2022 by Paolo Caressa <https://github.com/pcaressa>
"""

import random
random.seed(0)

# Error handling (brutal)
_ERRNO = 0
def error_on(cond, msg):
    global _ERRNO
    if cond:
        if _NLINE > 0:
            print(f"{_NAME}:{_NLINE}: WTF! ", end="")
        print(msg)
        _ERRNO += 1
        if _ERRNO > 100:
            print("That makes 100 errors: I give up!")
            exit(-1)
def exit_on(cond, msg):
    if cond:
        if _NLINE > 0:
            print(f"{_NAME}:{_NLINE}: WTF! ", end="")
        print(msg, "sorry, this is a fatal error!")
        exit(-1)

# Builtin stacks
_CSTK = []  # compiled code is pushed here
_DSTK = []  # temporary data, both at compile-time and at run-time
_PSTK = []  # used at compile-time to keep track of control structures nesting
_VSTK = []  # variables values are pushed here

# Stacks are implemented as lists.
def push(stk, elem):
    stk.append(elem)

def pop(stk):
    exit_on(len(stk) == 0, "Missing value (stack underflow)")
    return stk.pop()

#       Compile time stuff

# Lexical analyzer

# _CCODES[c] = -1, 0, 1 whether the ASCII character of code c is a
# word-character, a space character or a "letter" (part of a word).
_CCODES = [0]*33 + [1]*223  # A priori each printable is letter
_CCODES[ord("\n")] = -1
_CCODES[ord("\"")] = -1
_CCODES[ord("(")] = -1
_CCODES[ord(")")] = -1
_CCODES[ord("\\")] = -1
_CCODES[ord("[")] = -1
_CCODES[ord("]")] = -1

# Last character parsed, if any
_CLAST = ""

# Current source line under parsing (>= 1)
_NLINE = 0

def scan_char():
    """Scans a character from the _SRC file and returns it: if
    _CLAST != "" then it is returned as value and set to ""."""
    global _CLAST
    # The next character could have been already scanned
    # and in this case _CLAST contains it.
    if _CLAST != "":
        c = _CLAST
        _CLAST = ""
    else:
        c = _SRC.read(1)
    return c

def scan_word():
    """Scan a word from file _SRC and return it. A word is any sequence
    of consecutive non space character, or it is a single character
    marked with -1 in the CCODES[] table. Since the character following
    the word is also parsed, it is stored into _CLAST and used on the
    next call of scan_char()."""
    global _CLAST
    while (w := scan_char()) != '' and _CCODES[ord(w)] != -1:
        if _CCODES[ord(w)] == 1:
            while (c := scan_char()) != '' and _CCODES[ord(c)] == 1:
                w += c
            _CLAST = c
            break
    return w

# Source compilation

def compile_words(n):
    """Pop words (stored as triples (p,r,v)) from _DSTK with
    priorities >= n and compile them to _CSTK."""
    while len(_DSTK) >= 3 and _DSTK[-1] >= n:
        p = pop(_DSTK)
        r = pop(_DSTK)
        v = pop(_DSTK)
        push(_CSTK, r)
        push(_CSTK, v)

def compile(p, r, v):
    """Push the pair (r,v) on _DSTK or _CSTK according to the value
    of priority p. If p == 0 the word is executed. This is the core
    of the compiler."""
    if p == 0:
        r(v)
    elif p == 255:
        push(_CSTK, r)
        push(_CSTK, v)
    else:
        compile_words(p)
        push(_DSTK, v)
        push(_DSTK, r)
        push(_DSTK, p)

def find_word(w):
    """Look for w inside the dictionary: being the latter a stack,
    it is scanned from its topmost element downward. If w is found,
    the index in _DICT of the word (which starts a quadruple (w,p,r,v))
    is returned, else a negative number is returned."""
    for i in range(len(_DICT) - 4, -1, -4):
        if _DICT[i] == w:
            return i
    return -1

def compile_file():
    """Compile words from file _SRC until the file is ended."""
    global _NLINE
    _NLINE = 1
    while (w := scan_word()) != "":
        if (i := find_word(w)) >= 0:
            compile(_DICT[i+1], _DICT[i+2], _DICT[i+3])
        else:
            try:    # probe a number, the dirty way
                compile(255, PUSH, float(w))
            except ValueError:
                error_on(True, f"Unknown word {w}")
    compile_words(0)

# Code execution

_IP = 0     # index in _CSTK of the next instruction to execute

def execute():
    """Execute the content of _CSTK that contains 2n elements,
    where at even indexes we have routines and at odd indexes
    their arguments."""
    global _IP
    _IP = 0
    while _IP < len(_CSTK):
        _IP += 2
        _CSTK[_IP-2](_CSTK[_IP-1])

#       Run time stuff

# Primitive subroutines
def POP(): return pop(_DSTK)
def PUSH(v): push(_DSTK, v)
def JP(v):
    global _IP
    _IP = v
def JPZ(v):
    global _IP
    if POP() == 0:
        _IP = v
def CALL(v):
    global _IP, _CSTK
    push(_VSTK, _CSTK)
    push(_VSTK, _IP)
    _CSTK = v
    _IP = 0
def RET(v):
    global _IP, _CSTK
    _IP = pop(_VSTK)
    _CSTK = pop(_VSTK)
def VPUSH(v): push(_DSTK, _VSTK[v])
def VSTORE(v):
    global _VSTK
    _VSTK[v] = POP()
def VINCR(v):
    global _VSTK
    _VSTK[v] += 1
def VDECR(v):
    global _VSTK
    _VSTK[v] -= 1
def IPUSH(v):
    # expect _DSTK = [ ... s i ] where s is the stack and
    # i the index of the element to retrieve: both are
    # removed and s[i] is pushed instead.
    i = int(POP())
    s = POP()
    exit_on(i < -len(s) or i >= len(s), "Index out of range")
    PUSH(s[i])
def ISTORE(v):
    global _VSTK
    # expect _DSTK = [ ... i e ] where i is the index of the
    # element of the stack _VSTK[v] to modify and e the value
    # to write at it.
    e = POP()
    i = int(POP())
    exit_on(i < -len(_VSTK[v]) or i >= len(_VSTK[v]), "Index out of range")
    _VSTK[v][i] = e

# Implementation of built-in words

def ABS(v): PUSH(abs(POP()))
def ADD(v): PUSH(POP() + POP())
def DIV(v): PUSH((1.0 / POP()) * POP())
def MUL(v): PUSH(POP() * POP())
def NEG(v): PUSH(-POP())
def POW(v):
    e = POP()
    PUSH(POP() ** e)
def RAND(v): PUSH(random.random())
def ROUND(v): PUSH(round(POP()))
def SUB(v): PUSH(-POP() + POP())

# Notice: we want a Boolean to be a number
def EQ(v): PUSH(float(POP() == POP()))
def GEQ(v): PUSH(float(POP() <= POP()))
def GT(v): PUSH(float(POP() < POP()))
def LEQ(v): PUSH(float(POP() >= POP()))
def LT(v): PUSH(float(POP() > POP()))
def NEQ(v): PUSH(float(POP() != POP()))

def AND(v): PUSH(float(POP() != 0 and POP() != 0))
def NOT(v): PUSH(float(POP() == 0))
def OR(v): PUSH(float(POP() != 0 or POP() != 0))

def open_par(r):
    """Push on the stack a marker r that close_par will pop; the marker
    is stored as a triple so to be handles as operators are by the
    compile_*() functions. """
    PUSH(None)
    PUSH(r)
    PUSH(0)
def close_par(m):
    """Compile words from _DSTK into _CSTK until the marker m is found."""
    while len(_DSTK) >= 3:
        p = pop(_DSTK)
        r = pop(_DSTK)
        v = pop(_DSTK)
        if m == r:
            return
        push(_CSTK, r)
        push(_CSTK, v)
    error_on(True, f"Unmatched parenthesis '{m}'")

def STRCONST(v):
    # Scans each character from the next until another double quote
    # is scanned, or the file is ended.
    s = ""
    while (c := scan_char()) != "\"":
        exit_on(c == "", "End of file inside string")
        s += c
    compile(255, PUSH, s)

def COMMENT(v):
    global _NLINE
    # Skip until the next '\n' which is skipped, too
    while (c := scan_char()) != '' and c != '\n':
        pass
    if c == '\n':
        _NLINE += 1
def NEWLINE(v):
    global _NLINE
    compile_words(0)
    _NLINE += 1

def PRINT(v): print(POP())

def insert_word(p, r, v):
    """Scan a word from _SRC and insert it into the dictionary with
    priority p, routine r and value v. Used by "defining words" to
    create a dictionary entry."""
    compile_words(1)    # compile everything before definition
    w = scan_word()
    #error_on(find_word(w) >= 0, f"Word {w} already defined")
    push(_DICT, w)
    push(_DICT, p)
    push(_DICT, r)
    push(_DICT, v)

def DEF(v):     # DEF word = ...
    # Allocate a new item on _VSTK to contain the value of the variable
    # and store the "address" of the item (i.e. its index in _VSTK) as
    # value of the word under definition
    i = len(_VSTK)      # index of the item to allocate
    push(_VSTK, 0.0)    # allocate item
    insert_word(255, VPUSH, i)
    error_on(scan_word() != "=", "'=' expected")
    # compile the assignment with priority 50, thus later than any
    # expression producing a value but earlier then instructions.
    compile(50, VSTORE, i)

def compile_assignment(r):  # LET w = ... | ... OF w = ...
    """Scan a word from _SRC, look for it inside the dictionary and check
    that its routine is VPUSH, check that it is followed by "=" and compile
    it with priority 50 (so that it'll be compiled later than any expression)
    and routine r (VSTORE, ISTORE, etc.). The index in _DICT of the variable
    or, if not found, a negative value is returned."""
    w = scan_word()
    i = find_word(w)
    if i < 0 or _DICT[i + 2] != VPUSH:
        error_on(True, f"Unknown variable {w}")
    else:
        error_on(scan_word() != "=", "'=' expected")
        compile(50, r, _DICT[i+3])
    return i

def STACK(v):     # STACK word
    i = len(_VSTK)      # index of the item to allocate
    push(_VSTK, [])     # allocate empty stack
    insert_word(255, VPUSH, i)
def SPUSH(v):   # PUSH(s v)
    v = POP()
    s = POP()
    push(s, v)
def SPOP(v):   # POP(s)
    s = POP()
    PUSH(pop(s))
def STOS(v):   # TOS(s)
    s = POP()
    exit_on(len(s) == 0, "Missing data (stack underflow)")
    PUSH(s[-1])
def SLEN(v):    # LEN(s)
    s = POP()
    PUSH(len(s))
def CLOSEBRA(r):
    close_par(r)
    # At runtime expect _DSTK = [ ... s i] and returns s[i]
    compile(255, IPUSH, None)

def BEGIN(p):   # BEGIN word ... END
    # parameter p is the priority of the new word
    global _CSTK, _DICT
    # Inserts a new definition in the dictionary and leaves the _PSTK
    # as: [ ... c d BEGIN] where d is the current limit of _DICT and
    # c is a reference to the current _CSTK. d is used to "undefine" all
    # definition defined inside the block, while c is used to restore
    # the stack where to compile the code surrounding the block.
    # The value of the new definition is the address of the block code
    # which will be compiled until the next END word. So we save _CSTK,
    # define a new empty _CSTK pointed by the new word and save also
    # a sentinel BEGIN expected by END
    push(_PSTK, _CSTK)
    _CSTK = []          # now code will be compiled here
    insert_word(p, CALL, _CSTK)
    push(_PSTK, len(_DICT))
    push(_PSTK, BEGIN)  # END expects this
def END(v):
    global _CSTK, _DICT
    compile_words(0)    # to be sure anything before END is compiled
    error_on(pop(_PSTK) != BEGIN, "'END' without 'BEGIN'")
    push(_CSTK, RET)
    push(_CSTK, 0)
    # deletes all definitions local to the ending one.
    d = pop(_PSTK)  # len(_DICT) when BEGIN was executed
    while len(_DICT) > d:
        # drop the last four entries on top of _DICT
        _DICT.pop()
        _DICT.pop()
        _DICT.pop()
        _DICT.pop()
    _CSTK = pop(_PSTK)

def IF(v):   # IF ... THEN ... ELIF ... THEN ... ... ELSE ... FI
    compile_words(1)    # compile almost everything before IF
    push(_PSTK, FI)     # FI expects this: above this ELIF will
                        # insert addresses unrolled by FI
    push(_PSTK, IF)     # THEN expects this
def THEN(v):
    error_on(pop(_PSTK) != IF, "'THEN' without 'IF'")
    # Compile expressions to _CSTK and next compile JP
    compile_words(1)
    push(_CSTK, JPZ)
    push(_CSTK, 1e20)   # changed later
    # mark where the jumping "address" will be written
    push(_PSTK, len(_CSTK) - 1)
    push(_PSTK, THEN)   # ELSE and FI expect this
def ELIF(v):
    ELSE(v)
    pop(_PSTK)
    push(_PSTK, IF)     # THEN expects this
def ELSE(v):
    error_on(pop(_PSTK) != THEN, "'ELSE' without 'THEN'")
    # Compile expressions to _CSTK and next compile JP
    compile_words(1)
    push(_CSTK, JP)
    push(_CSTK, 1e20)   # changed later
    i = pop(_PSTK)      # index where to write a jump address
    # mark where the jumping "address" will be written
    j = len(_CSTK) - 1
    push(_PSTK, j)
    _CSTK[i] = j + 1    # The JPZ compiled by THEN jumps here
    push(_PSTK, ELSE)   # FI expects this
def FI(v):
    m = pop(_PSTK)
    error_on(m != THEN and m != ELSE, "'FI' without 'THEN'/'ELSE'")
    # A list of addresses where to write a pointer to the next
    # compiled instruction are written above FI in _PSTACK: they
    # are n + 1, being n the number of ELIFs
    compile_words(1)
    while (i := pop(_PSTK)) != FI:
        _CSTK[i] = len(_CSTK)

def WHILE(v):   # WHILE ... DO ... OD
    compile_words(1)    # compile almost everything before WHILE
    # mark where to jump to repeat the loop
    push(_PSTK, len(_CSTK))
    push(_PSTK, WHILE)  # DO expects this
def DO(v):
    m = pop(_PSTK)
    error_on(m != WHILE and m != FOR, "'DO' without 'WHILE' or 'FOR'")
    # Compile expressions to _CSTK and next compile JP
    compile_words(1)
    push(_CSTK, JPZ)
    push(_CSTK, 1e20)   # changed later
    # mark where the jumping "address" will be written
    push(_PSTK, len(_CSTK) - 1)
    push(_PSTK, DO)   # OD expects this
def OD(v):
    error_on(pop(_PSTK) != DO, "'OD' without 'DO'")
    # now _PSTK = [..., a, b] where a is the address of the while
    # condition and b is the address of the argument of the JPZ
    # compiled by OD: in the latter we need to write the address
    # of the first item following the loop, the former will be the
    # argument of the JP compiled by OD to repeat the loop.
    b = pop(_PSTK)
    a = pop(_PSTK)
    compile_words(5)
    push(_CSTK, JP)
    push(_CSTK, a)
    _CSTK[b] = len(_CSTK)

def FOR(v):     # FOR w = e1 TO e2 DO ... NEXT
    i = compile_assignment(VSTORE)
    push(_PSTK, _DICT[i+3]) # index of the control variable, needed later
    push(_PSTK, FOR)        # TO expects this
def TO(v):      # TO expr DO
    compile_words(1)
    j = len(_CSTK)      # keep track of the location of the "TO condition"
                        # so that NEXT will jump here to repeat the loop
    error_on(pop(_PSTK) != FOR, "'TO' without 'FOR'")
    # compile the condition "loopvar < expr"
    i = pop(_PSTK)      # loop variable index in _VSTK
    compile(255, VPUSH, i)
    compile(50, LT, None)
    push(_PSTK, j)
    push(_PSTK, i)
    push(_PSTK, FOR)
def NEXT(v):
    global _CSTK
    # expect _PSTK = [ ... j i b FOR ] where j is the address
    # where the NEXT will jump to iterate the loop, i is the index
    # in _VSTK of the loop control variable, b is the address
    # of the argument of the JPZ compiled by DO where the address
    # of the first instruction following the loop needs to be stored.
    error_on(pop(_PSTK) != DO, "'NEXT' without 'DO'")
    b = pop(_PSTK)
    i = pop(_PSTK)
    j = pop(_PSTK)
    # compile the increment of the loop variable
    compile(255, VINCR, i)
    # compile a jump to the condition compiled by TO
    compile(255, JP, j)
    # compile the address of the next instruction at b
    _CSTK[b] = len(_CSTK)

def FOPEN(v):       # FOPEN(...)
    # Expect _DSTK = [ ... name mode ]: opens a file with that name and
    # mode and returns it on the stack. or NIL if no such file can be opened.
    mode = POP()
    name = POP()
    PUSH(open(name, mode))
def FCLOSE(v):
    try:
        f = POP()
        f.close()
    except:
        exit_on(True, "I/O error (closing a file)")
def FGET(v):
    try:
        f = POP()
        PUSH(f.read(1))
    except:
        exit_on(True, "I/O error (reading a file)")
def FPUT(v):
    try:
        f = POP()
        f.write(chr(int(POP)))
    except:
        exit_on(True, "I/O error (writing a file)")

def INCLUDE(v):     # INCLUDE ...
    global _NAME
    global _SRC
    global _NLINE
    push(_PSTK, _NAME)
    push(_PSTK, _SRC)
    push(_PSTK, _NLINE)
    PUSH(scan_word())
    PUSH("r")
    FOPEN(None)
    _SRC = POP()
    compile_file()
    _SRC.close()
    _NLINE = pop(_PSTK)
    _SRC = pop(_PSTK)
    _NAME = pop(_PSTK)

# Dictionary stack

_DICT = [
    "$PRINT", 10, PRINT, None,
    "(", 0, open_par, ")",
    ")", 0, close_par, ")",
    "*", 110, MUL, None,
    "**", 130, POW, None,
    "+", 100, ADD, None,
    "-", 100, SUB, None,
    "/", 110, DIV, None,
    "<", 90, LT, None,
    "<=", 90, LEQ, None,
    "<>", 90, NEQ, None,
    "=", 90, EQ, None,
    ">", 90, GT, None,
    ">=", 90, GEQ, None,
    "ABS", 200, ABS, None,
    "AND", 70, AND, None,
    "CMD", 0, BEGIN, 0,
    "DEF", 0, DEF, None,
    "DO", 0, DO, None,
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
]

# Main program

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dump-obj", action="store_true")
parser.add_argument("--dump-dict", action="store_true")
parser.add_argument("--dump-vars", action="store_true")
parser.add_argument("source")
args = parser.parse_args()

_NAME = args.source
with open(_NAME) as f:
    _SRC = f
    _NLINE = 1
    compile_file()
    _NLINE = 0

if args.dump_obj:
    print()
    print("Code dump")
    for i in range(0, len(_CSTK), 2):
        print(f"{i}: {_CSTK[i]} {_CSTK[i + 1]}")

if args.dump_dict:
    print()
    print("Dictionary dump")
    for i in range(0, len(_DICT), 4):
        print(_DICT[i], _DICT[i+1], _DICT[i+2], _DICT[i+3])

if args.dump_vars:
    print()
    print("Variables dump")
    for i, x in enumerate(_VSTK):
        print(f"{i}: {x}")

if _ERRNO == 0:
    error_on(len(_DSTK) > 0, "Some error occurred, cross your fingers")
    error_on(len(_PSTK) > 0, "Control structures mismatches")
    execute()

