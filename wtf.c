/** \file wft.c

    A single cell can contain a double number, an index or a pointer.

    Indexes are used to refer to stacks, which are contained in a table
    _stacks: for example 4 is the stack _stacks[4]
*/

typedef double NUM_t;
typedef unsigned long IND_t;
typedef void *ADDR_t;

typedef union {
    NUM_t n;
    IND_t i;
    ADDR_t p;
} CELL_t;

/*
    Error stuff
*/

char *_name = NULL; /**< source file name. */
int _nline = 0;     /**< line currently under parsing. */
int _ip = -1;       /**< instruction pointer. */
int _errno = 0;     /**< number of error so far. */

void exit_on(int cond, char *msg)
{
    if (cond) {
        if (_nline > 0) {
            printf("%s:%i: %s.\n", _name, _nline, msg);
        } else if (_ip >= 0) {
            printf("<code>:%i: %s.\n", _ip - 2, msg);
        } else {
            printf("WTF! %s.\n", msg);
        }
    }
}

void error_on(int cond, char *msg)
{
    if (cond) {
        if (_nline > 0) {
            printf("%s:%i: %s.\n", _name, _nline, msg);
        } else if (_ip >= 0) {
            printf("<code>:%i: %s.\n", _ip - 2, msg);
        } else {
            printf("WTF! %s.\n", msg);
        }
        _errno += 1
        exit_on(_errno >= 100, "That makes 100 errors: I give up")
    }
}

/*
    Stack implementation stuff
*/

typedef struct {
    IND_t size;
    IND_t len;
    CELL_t *s;
} STACK_t;

#define STACK_NUM (1024)    // number of available stacks

/** Stacks are stored into an array: they are determined as index in
    the array, since their actual addresses may change, due to the
    realloc behavior. The 0-th item is not available, while the first
    four are reserved to the compiler. The _stacks_next variable contains
    the index of the next free item in the _stacks[] list. Stacks may
    also be used as strings, in which case their sizes and lengths are
    to be multiplied by 8 = sizeof(CELL_t). */
static STACK_t _stacks[STACK_NUM] = {0};
#define _NIL  (0)   // NULL pointer
#define _DICT (1)   // Word dictionary
#define _DSTK (2)   // Data stack
#define _CSTK (3)   // Code stack
#define _TIB (4)    // Terminal input buffer
static IND_t _stacks_next = 5;  // _stacks[0] = null pointer.

void push(IND_t i, CELL_t c)
{
    STACK_t *s = _stacks + i;
    assert( i > 0 && i < STACK_NUM);
    if (s->size == s->len) {
        s->s = realloc(s->s, s->size += 1024);
        exit_on(s->s == NULL, "Out of memory");
    }
    s->s[s->len++] = c;
}

void pop(IND_t i, CELL_t *c)
{
    STACK_t *s = _stacks + i;
    assert( i > 0 && i < STACK_NUM);
    exit_on(s->len == 0, "Missing value (stack underflow))");
    *c = s->s[--s->len];
}

/*
    Lexical analyzer
*/

/** _ccodes[c] is -1, 0 or 1 whether the character of ASCII code c is
    a special one, a blank one or part of a word. */
char _ccodes[256] = {0};

void init(void)
{
    memset(_ccodes + 33, 1, 223);
    _ccodes['\n'] = -1;
    _ccodes['\\'] = -1;
    _ccodes['('] = -1;
    _ccodes[')'] = -1;
    _ccodes['['] = -1;
    _ccodes[']'] = -1;
    _ccodes['{'] = -1;
    _ccodes['}'] = -1;
}

/** Last character parsed, if any. */
char _clast = '\0';

/** Scans a character and returns it on the _DSTK. */
void scan_char(void)
{
    CELL_t c;
    if (_clast != '\0') {
        c->n = _clast;
        _clast = '\0';
    } else {
        c->n = fgetc(_src);
    }
    push(_DSTK, c);
}

void scan_word(void)
{
}

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
    _NLINE = 0


# Code execution

_IP = -1    # index in _CSTK of the next instruction to execute

def execute():
    """Execute the content of _CSTK that contains 2n elements,
    where at even indexes we have routines and at odd indexes
    their arguments."""
    global _IP
    _IP = 0
    while _IP < len(_CSTK):
        _IP += 2
        _CSTK[_IP-2](_CSTK[_IP-1])
    _IP = -1
