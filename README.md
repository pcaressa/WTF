# WTF: Word Translation as in Forth

## A Python commentary to Chuck Moore's unpublished book

### (c) by Paolo Caressa

#### v 1.0, Oct 2022

## Introduction

WTF (at least in this document) means *Word Translation as in Forth*: indeed, WTF draws inspiration from the classic Forth language, essentially described by its creator Charles Moore in an unpublished book available online [Programming a Problem Oriented Language](http://forth.org/POL.pdf): if you still haven't read this book then stop reading me and follow the link! The simplicity, elegance and versatility of Forth are the ideal pursued by WTF, whose design draws inspiration from Moore's book to provide:

- A procedural language with an Algol-like syntax.
- A compiler that, up to a bootstrap and efficiency considerations, could be written in the language itself.
- An interpreter without opcodes but with indirect calls to machine code routines.
- Last, but not least, leisure and fun to its author.

The only data structure I'll use to implement that is the stack: stacks were invented by Alan Turing in 1946 report [Proposals for Development in the Mathematics Division of an Automatic Computing Engine](https://en.wikisource.org/wiki/Proposed_Electronic_Calculator) to handle subroutines calls even if, in 1957, Klaus Samelson and Friedrich Bauer, unaware of Turing contribution, filed a patent for it. In the 60s, stack-based interpreters for the Algol-60 language emerged (see E.W. Dijkstra [A simple mechanism modelling some features of Algol 60](https://archive.computerhistory.org/resources/text/algol/ACM_Algol_bulletin/1060960/p14-dijkstra.pdf) and in 1971 Niklaus Wirth programmed the first Pascal compiler translating to a byte-code for a stack VM (see e.g. [Pascal-S: A Subbet and its Implementation](https://sysovl.info/pages/blobs/ethz/Wirth-PascalS.pdf)). In the same year Moore finished his book, containing ideas developed in the 60s and exerting a great influence in the 1970s/1980s. From 1990s on, most languages used stack virtual machine as byte-code: Java, C\#, Python etc.

WTF current implementation is written in a simple minded but easy-to-port non idiomatic Python. The program [wtf.py](wtf.py) is an interpreter that compiles a source file into an inner threaded code which is then executed. Use it as

```bash
    $ python wtf.py source
```

The program was coded to provide a practical explanation of Moore ideas I presented at the Milan 2022 Codemotion Conference [slides here](doc/Codemotion2022.pdf). However, this is just an imperfect version of what I have in mind: the next steps will be to engine a core language and to provide means to write all WTF language extensions in WTF itself. It'll be probably written in C.

Enjoy,  
Paolo

---

## 1. Interpreters and virtual machines

Briefly speaking: an interpreted language translates the source code into a bytecode, that is, a sequence of numerical codes that represent operations and sometimes their operands, which is executed by a virtual machine. In a real processor, the bytecode is the object code formed by machine language instructions, which usually have different shapes and a more or less complicated structure depending on the architecture of the processor.

A virtual machine emulates a processor, typically for reasons of portability or ease of implementation, and therefore its bytecode is not machine code for a CPU but a sequence of codes that the virtual machine executes by scanning them one by one from a portion of memory.

While the CPU of a real machine has inner memory areas (registers, caches etc.) whose access is much faster than access to RAM and which are used for temporary operations etc., a virtual machine uses only the RAM memory and therefore does not use registers for temporary operations but a stack. The operations then take the input values from the stack and deposit the output values into it, too.

Since a stack, the most fundamental data structure in computing, allows only two operations namely *pushing* an element on its top *popping* an element from its top, operations are performed *after* the operands have been pressed on the stack: for example,

```text
1 2 +
```

instead of the usual "infix" algebraic notation `1 + 2`. This "postfixed" sequence is typically compiled by an interpreter in the following bytecode as postfixed (or Polish) form from the name of its first proponent, the great Polish logician and philosopher Jan Łukasiewicz):

```text
PUSH 1
PUSH 2
ADD
```

where `PUSH` is a special bytecode that corresponds to the instruction that takes its operand not from the stack but from the following bytecode, which is then interpreted as a numeric constant. The effect is to press sequentially on the stack `1` and then `2`. The `ADD` bytecode corresponds instead to the instruction that removes two elements from the top of the stack, finding first the `2` and then, below, the `1`, and adds them, pressing the result always on the stack.

The archetype of stack machines languages, such as PDF or the bytecode used by Java and Python since the mid-90s, is Forth, a programming language 25 years older than them, in which the order of the operators is the Polish one: in fact `1 2 +` is a valid sequence of Forth instructions that precisely leaves `3` on the stack.

This postfixed notation is the opposite of the prexixed notation used by Lisp, where operations are written in functional form:

```lisp
(+ 1 2)
```

Therefore, the prefixed form of the Lisp requires a translation that is different from the stack-based one, because the operation is parsed first and its parameters must be stored somewhere (in registers or memory locations) before they can be operated.

This is also the form of the machine code instructions in real CPUs, where the previous operation would be something like

```asm
MOV EAX, 1
MOV EBX, 2
ADD EAX, EBX
```

The first two instructions load operands into two registers, the third is the equivalent of `(+ 1 2)` where `ADD` is the sum operation and `EAX` and `EBX` are the operands, in the form of registers. However, the `ADD` instruction needs to come after the instructions which load data inside the registers involved in the addition.

Let's go back to the postfixed instruction `1 2 +` and see how it is actually compiled: using bytecodes, and assuming that 100 is the bytecode of `PUSH` and 200 the bytecode of `+`, we would have the sequence of codes:

```text
100, 1, 100, 2, 200
```

An interpreter for this program is very simple to write: suppose the program is stored in a list `c[]`. A naïve version in Python (understandable even to those who do not know it) is as follows: it uses an `ip` index to scan the list with bytecode and a stack, always in the form of a list, to keep track of the operands of the instructions.

```python
c = [100, 1, 100, 2, 200]
ip = 0
stack = []
while ip < len(c):
    if c[ip] == 100:    # PUSH
        ip = ip + 1
        stack.append(c[ip])
    elif c[ip] == 200:  # ADD
        x = stack[-1]
        y = stack[-2]
        stack = stack[:-2] + [x+y]
    else:
        print("Error")
    ip = ip + 1
print(stack)
```

Of course this interpreter knows only the two bytecodes indicated, but it is clear how to extend it to include as many as we want. If you try to run it will print `[3]` that is the stack after processing.

However, from the point of view of programming, it is a solution both inelegant and difficult to maintain: it is better to provide a table that associates each bytecode with the corresponding action at run time; each of these actions is encoded in a function that is executed when the corresponding opcode is found in the object code:

```python
def PUSH():
    global c, ip, stack
    ip = ip + 1
    stack.append(c[ip])

def ADD():
    global c, ip, stack
    x = stack[-1]
    y = stack[-2]
    stack = stack[:-2] + [x+y]

OPTABLE = {100: PUSH, 200: ADD}

c = [100, 1, 100, 2, 200]
ip = 0
stack = []
while ip < len(c):
    opcode = c[ip]
    if opcode in OPTABLE:
        OPTABLE[opcode]()
    else:
        print("Error")
    ip = ip + 1
print(stack)
```

Notice that the associative array `OPTABLE` has bytecodes as keys representing an instruction and functions that implement that statement as values: within the `while` loop that executes the object code in the `c` array, the statement `OPTABLE[opcode]()` calls the function obtained as a value from the `opcode` key. In this way, to expand the instruction set of our virtual machine, it will be enough to finish new functions and leave the interpretation loop unchanged. Also note that we do not use a `for` loop over `ip` as this variable can be changed in the subroutines that implement virtual machine operations (as happens in `PUSH`).

On closer inspection, as bytecode for a statement we could directly use references to the Python functions that implement it:

```python
def PUSH():
    global c, ip, stack
    ip = ip + 1
    stack.append(c[ip])

def ADD():
    global c, ip, stack
    x = stack[-1]
    y = stack[-2]
    stack = stack[:-2] + [x+y]

c = [PUSH, 1, PUSH, 2, ADD]
ip = 0
stack = []
while ip < len(c):
    opcode = c[ip]
    if callable(opcode):    # Is opcode a Python function?
        opcode()
    else:
        print("Error")
    ip = ip + 1
print(stack)
```

This second solution is more efficient than the first, as we do not have to retrieve the reference to the function from an associative table. If we wrote in a language closer to the machine, such as C, the advantage would be smaller: traditional Forth compilers used the first type of encoding, called *threaded code*, especially for reasons of greater compactness of the object code, in an era when RAM was measured in Kbytes and not Gbytes as today.

The idea of WTF is to provide a virtual machine similar to the one we have just described but that makes visible to the language itself all the objects used to program it. That is, both the stack `stack`, the array `c` and the functions `PUSH`, `ADD` and the same loop that interprets the code are all native objects of the language, treated as the stuff that the programmer can define on his own.

This higher level of generality is paid for at the price of a greater complexity of the compiler and the interpreter, which however still remain extremely simple compared to a traditional compiler for any language, but in the end we will get a very flexible language, which can be reprogrammed in different forms and which to a large extent is programmed in itself: WTF!

---

## 2. WTF as both a compiler and an interpreter

The virtual machine we just sketched is the analogue of a CPU and its language analogous to the machine language: but in addition to this, WTF offers a high-level language that is compiled into the code of this machine. The point is that the compiled code corresponds to the source code transparently, in the sense that the compilation takes place using the same tools as the virtual machine.

### 2.1. How a source file is parsed

Since the only methodological driver of WTF is to keep things simple, we will consider a programming language without grammar: thus, tokens of the language are, a priori, all interpreted or compiled with the same device. The semantics of the language will lie in words used to express it and not in the textual relationship among them.

Thus, for us a source program is a text file, whom our interpreter will parse *words* to be executed/compiled: a word is a sequence of non blanks characters delimited by blanks (some characters count as a single word, more on that later). For example

```wtf
PRINT 1 + 2 * 3
```

consists in six words: `PRINT`, `1`, `+`, `2`, `*` and `3`. Notice that, had we written,

```wtf
PRINT 1+2*3
```

words would have been two: `PRINT`, `1+2*3`.

However, some special characters are allowed, which are both words in themselves and word delimiters: by default parentheses are such characters, so that

```wtf
PRINT(1 + 2)* 3
```

will result in the following words: `PRINT`, `(`, `1`, `+`, `2`, `)`, `*` and `3`.

### 2.2. How a source file is compiled

The compiling technique Moore's describes in his book and I'll repeat here is a smart bottom-up operator precedence algorithm, discussed for example as early as in 1959 by H. Kanner *An Algebraic Translator*, CACM 2(10), 19-22. However my approach will be so elementary that no notion on formal languages nor compiling theory will be needed.

Instead, we will need the following stacks, during the compiling process:

- `_DICT`, the *dictionary*, used to store quadruples *(w, p, r, v)*.
- `_DSTK`, the *stack*, used to store temporary single data (numbers/references).
- `_CSTK`, the *code stack*, used to store "compiled code" thus pairs *(r,v)* where *r* is the address of a subroutine and *v* a value passed it as parameter.

Those stacks will be also available at run-time and they are, at start, empty, except for `_DICT` which contains built-in words.

The compilation process scans words from the source file and compiles them to the `_CSTK` stack, using the `_DSTK` as store for words not yet to be compiled but already scanned. Indeed, once a word *w* has been parsed we look for it inside the dictionary whose elements are quadruples *(w, p, r, v)* where:

- *p* is an unsigned byte, the *priority* of the word.
- *r* is the address of a machine language subroutine, the *routine* of the word.
- *v* is a the *word value* which is passed to the subroutine as parameter.

The higher *p* the sooner the word will be compiled, while the subroutine call *r(v)* represents the operational semantics of the word.

Namely, suppose we parsed *w* and found it in `_DICT` as *(w,p,r,v)*:

- If *p* = 0 we call subroutine *r* with parameter *v*: a word with priority 0 is not compiled but executed at compile time.
- If *p* = 255 we immediately compile the word, thus we push the pair *(r,v)* on the stack `_CSTK`.
- Otherwise, we push the triple *(p,r,v)* on the auxiliary `_DSTK`, possibly immediately compiling on `_CSTK` words already pushed on `_DSTK` if their priorities are higher or equal to *p*. In particular:
    - If the stack `_DSTK` is empty or its topmost element has priority < *p* then we push *(p,r,v)* on `_DSTK`.
    - Else we keep on popping a triple *(p',r',v')* from `_DSTK` and push *(r',v')* on `_CSTK` until we are brought back to the previous case, thus *p'* < *p* (or there are no more elements in `_DSTK`). Finally, we push *(p,r,v)* on `_DSTK`.

Thus, we keep aside words into `_DSTK` to compile them (i.e. push them on `_CSTK`) at the right moment.

Notice that we push on `_CSTK` pairs *(r,v)* even if the routine does not use its parameter: on doing this we waste space but we speed the execution process. This is slightly different from the explanation in the previous section, and may be easily changed.

Now we consider the case that the parsed word is not in the dictionary: then we try to interpret it as a number, and if we succeed we compile it else we print an error message but we keep on parsing.

To compile a number *N* means to compile it as if the following definition would be associated to it:
*("N", 255, `PUSH`, N)*. Since it has priority 255, the pair *(`PUSH`, N)* is immediately compiled into `_CSTK`.


When at runtime the `PUSH(N)` subroutine will be executed, it'll push its argument *N* on the `_DSTK`, where runtime words parameters and results are stored.

### 2.3. Example of compilation

Suppose the source file is

```
PRINT 1 + 2 * 3 - 4
```

and that the dictionary contains at least the items

```
    ("PRINT", 10, PRINT, NIL)
    ("+", 100, ADD, NIL)
    ("-", 100, SUB, NIL)
    ("*", 110, MUL, NIL)
```


We’ll explain in a moment what the subroutines `PRINT`, `ADD`, `SUB` and `MUL` do, although you can make an educated guess: `NIL` is the null pointer.

Remember: we assume that at start both stacks `_CSTK` and `_DSTK` are empty, we'll represent them as lists whose topmost parts are on the right, for example `[... 2 1 0]` denotes a stack whose top element is 0, with 1 beneath it, 2 beneath it etc.

The first word we parse is  *w=`PRINT`* and we find it in the dictionary with value *(p=10, r=`PRINT`, v=`NIL`)*: since `_DSTK` is empty we push the word on this stack, getting:

```
_CSTK = []
_DSTK = [(10, PRINT, NIL)]
```

Next, we parse *w=`1`* that is not in the dictionary but it is a number, so we push the pair `(PUSH,1)` on `_CSTK`.

```
_CSTK = [(PUSH, 1)]
_DSTK = [(10, PRINT, NIL)]
```

Next, we parse *w=`+`* and find it in the dictionary with value *(p_w=100, r_p=`ADD`, v_w=`NIL`)*: since the topmost word on `_DICT` has priority 10 < 100 we push *w* on `_DSTK`:

```
_CSTK = [(PUSH, 1)]
_DSTK = [(10, PRINT, NIL) (100, ADD, NIL)]
```

Next, we parse *w=`2`* that is not in the dictionary but it is a number, so we push the pair `(PUSH,2)` on `_CSTK`.

```
_CSTK = [(PUSH, 1) (PUSH, 2)]
_DSTK = [(10, PRINT, NIL) (100, ADD, NIL)]
```

Next, we parse *w=`*`* and find it in the dictionary with value *(p=110, r=`MUL`, v=`NIL`)*: again, since its priority is greater than the one of the topmost word in `_DSTK`, we push *w* on it.

```
_CSTK = [(PUSH, 1) (PUSH, 2)]
_DSTK = [(10, PRINT, NIL) (100, ADD, NIL) (110, MUL, NIL)]
```

Next, we parse *w=`3`* that is not in the dictionary but it is a number, so we push the pair `(PUSH,2)` on `_CSTK`.

```
_CSTK = [(PUSH, 1) (PUSH, 2) (PUSH, 3)]
_DSTK = [(10, PRINT, NIL) (100, ADD, NIL) (110, MUL, NIL)]
```

Next, we parse *w=`-`* and find it in the dictionary with value *(p_w=100, r_p=`SUB`, v_w=`NIL`)*. This time, its priority is not greater than the priority of the topmost word on `_DSTK`, so we pop words from the latter and push them on `_CSTK` until we find a word with priority less than 100 or `_DSTK` is empty:

```
_CSTK = [(PUSH, 1) (PUSH, 2) (PUSH, 3) (110, MUL, NIL) (100, ADD, NIL)]
_DSTK = [(10, PRINT, NIL)]
```

Then we push *w=-* on `_DSTK` getting

```
_CSTK = [(PUSH, 1) (PUSH, 2) (PUSH, 3) (110, MUL, NIL) (100, ADD, NIL)]
_DSTK = [(10, PRINT, NIL) (100, SUB, NIL)]
```

Finally, we parse *w=`4`* that is not in the dictionary but it is a number, so we push the pair `(PUSH,4)` on `_CSTK`.

```
_CSTK = [(PUSH, 1) (PUSH, 2) (PUSH, 3) (MUL, NIL) (ADD, NIL) (PUSH, 4)]
_DSTK = [(10, PRINT, NIL) (100, SUB, NIL)]
```

The text line is ended, and the newline (or the end of file) has the effect to pop elements from `_DSTK` and to push them to `_CSTK` until `_DSTK` is empty, so that we finally get

```
_CSTK = [(PUSH, 1) (PUSH, 2) (PUSH, 3) (MUL, NIL) (ADD, NIL) (PUSH, 4) (100, SUB, NIL) (10, PRINT, NIL)]
_DSTK = []
```

### 2.4. How compiled code is executed

After a source file has been compiled as described, `_CSTK` contains a sequence of machine code calls *(r,v)* which can be easily executed, from the bottomost to the topmost one. We use a global variable `_IP` to keep track of the next instruction to execute and perform the following execution algorithm which in Python would be

```Python
_IP = 0
while _IP < len(_CSTK):
    _IP += 2
    _CSTK[_IP-2](_CSTK[_IP-1])
_IP = -1
```

Notice that `_IP` always contains the address (in this case the index to an element of `_CSTK`) of the next instruction to be executed. Altering `_IP` means to perform a jump.

For example, let us execute the previous compiled code:

```
[
    PUSH, 1,
    PUSH, 2,
    PUSH, 3,
    MUL, NIL,
    ADD, NIL,
    SUB, NIL,
    PRINT, NIL
]
```

Of course to do that we need the subroutines `PUSH`, `MUL`, `ADD`, `SUB` and `PRINT`: they are runtime routines and uses the stack `_DSTK` to fetch parameters and store results, namely:

- `PUSH` pushes its argument on the stack.
- `MUL` pops two numbers from the stack and pushes their product on it.
- `ADD` pops two numbers from the stack and pushes their sum on it.
- `SUB` pops two numbers from the stack and pushes the difference of the second one minus the topmost one on the stack.
- `PRINT` pops a number from the stack and prints it.


Therefore, executing the previous code goes as follows:

- After `PUSH(1)` we have `_DSTK = [1]`.
- After `PUSH(2)` we have `_DSTK = [1 2]`.
- After `PUSH(3)` we have `_DSTK = [1 2 3]`.
- After `MUL(NIL)` we have `_DSTK = [1 6]`.
- After `ADD(NIL)` we have `_DSTK = [7]`.
- After `PUSH(4)` we have `_DSTK = [7 4]`.
- After `SUB(NIL)` we have `_DSTK = [3]`.
- After `PRINT(NIL)` we have `_DSTK = []` and 3 printed on the screen.

## 3. The making of a language

Until now, we have described a "compiler skeleton", where the flesh are built-in words in a programming language still to be defined: once we populate the dictionary with those words, we'll have an implementation of it on top of our virtual machine.

The syntax of the language will be encoded in words priorities, while the corresponding machine code routines that implement them are executed in Polish reverse notation, since they operates on the data stack, as we have seen.

In some sense, the compiled code is a typical stack machine code, but instead of bytecodes we use pairs *(r,v)*.

Of course this wastes space and can be optimized in different ways: to compile just *r* and possibly *v* to save space, to compile machine code to save time, etc. But in this first version of WTF we keep things simple!

We could implement a purely interpreted language by modifying the previous compilation algorithm so that a word is not compiled into `_CSTK` but executed instead. On the other hand we could allow only words with positive priorities and get compiled code only, more efficient. Or we can do both: words with priority 0 are compile-time word such as definitions, declarations, package inclusions, etc., while words with priority > 0 gives rise to executable code at runtime.

The WTF Python implementation provided in this package is just an example of an Algol-like language.

### 3.1. Handling algebraic expressions

To begin with let us introduce a set of words to handle algebraic expressions in the usual infix form, which will be compiled into the Polish form to be executed by the virtual machine.

| Priority | Words              |
|----------|--------------------|
|     0    | `( )`              |
|    10    | `PRINT`            |
|    60    | `OR`               |
|    70    | `AND`              |
|    80    | `NOT`              |
|    90    | `= < > <> >= <=`   |
|    100   | `+ -`              |
|    110   | `* /`              |
|    120   | `NEG`              |
|    130   | `**`               |
|    250   | `ABS ROUND`        |
|    255   | any number         |


Notice that the parentheses, which are also special characters, have priority 0: this means that they are not compiled but rather they do something during compile time. Namely, since they alter the priority of compilation, making all stuff enclosed between them with highest priority, they do the following:

- `(` pushes on `_DSTK` a fake word `(0, NIL, NIL)` which has priority 0 (no compiled word has it!).
- `)` pops items from `_DSTK` and compiles them on `_CSTK` until the fake element `(0, NIL, NIL)` is found (and removed).

Since `_DSTK` is a stack, parentheses nesting is guaranteed to work in the expected way!

Notice also that the minus sign is reserved for difference, so that the negation of a number needs a different symbol, we choose `NEG` so that `NEG x` is the same as `0 - x`.

The `**` power operator has priority greater than `NEG` since we want `NEG 2 ** 4` to result in -16 and not in 16.

We also add two more special characters, the newline and the backslash, with priorities 0 and associated to routines

- `COMMENT` which scans each character until the next newline: its effect is to ignore all text on the right of the backslash, we use it for comments or to continue an expression to the following line.
- `NEWLINE` which pops everything on the `_DSTK` into the `_CSTK`, so that with the end of the line all "suspended" words waiting to be compiled will be. In this way, grosso modo a statement is contained in a single line: to continue it on the next, use the backslash.

### 3.2. Remarks on the (lack of) syntax

Let me make an important remark: WFT trades simplicity for ambiguity. By that I mean that words in a WTF program are aware only of themselves: this is different from most languages in which a token may have different semantics according to the context. For example the minus sign may represent the negation or the subtraction: to see which is which, one should know if, say, the minus is between two operands or just before only one, to decide how to translate it.

One could introduce a WTF device to accomplish that, by means of a state: for example, each word could set or reset a flag whether it gives rise to an operand or not, so that the minus word could check it, at compile time, and compile the appropriated code for negation or minus. But this would have impact on all words.

The general rules upon which WTF design relies are:

- Keep the compiler simple.
- Keep words independents.
- Avoid states if possible.

Therefore we stick to this annoying `NEG` operator for the unary minus.

Another interesting remark is the following one: since the actual order of compilation for a word is dictated by its priority, we can use for algebraic operators either the infix notation, either the postfix or the prefix one.

For example the following three lines will both print 9:

```
    PRINT (1 + 2) * 3
    (PRINT (* (+ 1 2) 3))
    (1 2 +) 3 * PRINT
```

The first one is the "Fortran-like", the second one the "Lisp-like" and the third one the "Forth-like": so, you can write WTF you want. Since words are reordered according to priorities (but beware that constants are immediately compiled!) the syntax of WTF algebraic expressions, and more, is a matter of taste.


### 3.3. Variables

Until now, the only way to add new words to the dictionary is to modify the WTF interpreter: let us remedy by introducing words to define variables. I won't provide the most general way to do that, perhaps in future WTF versions. We will store che value of variables inside a new stack `_VSTK`, whose elements are addressed by word values (thus the value of a word containing a variable will be an index to `_VSTK`. Namely, each variable's value will have a unique "address" (an index) *i* such that the value of the variable is `_VLIST[i]`. Such a value may be a number, a stack (in the Python implementation a list) or even a string.

Also, we'll need some runtime routine to fetch and store data inside this stack:

- `VPUSH(i)` which pushes on `_DSTK` the content of the variable of index *i* in `_VLIST`.
- `VSTORE(i)` which pops a value *v* from `_DSTK` and sets the *i*-th element of `_VLIST` to *v*.

To define and initialize a variable use the word `DEF`, which does the following:

- At compile time:
    - Push 0 on `_VSTK` and get the address *i* of it.
    - Scan a word *w* and insert a definition (*w*, 255, `VPUSH`, *i*) on `_DICT`.
    - Scan a word raising an error if is not `=`.
    - Compile the instruction `VSTORE(i)` with priority 50, thus pushes (50, `VSTORE`, *i*) on `_DSTK`.
- Runtime effects:
    - Pop the result of the evaluation of the expression following `=` and store it at `_VSTK[i]`.

For example the sequence `DEF x = 1` performs the following at compile time:

- The `DEF` word is executed and does the following
    - Pushes 0 on `_VSTK`.
    - Parses the word "x".
    - Creates an entry ("x", 255, `VPUSH`, `len(_VSTK)-1`).
    - Pushes (50, `VSTORE`, *i*) on `_DSTK`.
    - Parses the word "=".
- The `1` word immediately pushes `(PUSH,1)`on `_CSTK`.

Finally all words from `_DSTK` are pushed on `_CSTK` so that the latter results in `[(PUSH,1) (VSTORE,i)]`. So, the variable is defined during compile time, and its value is initialized at run time.

Notice that a variable may be defined time and again: being both the dictionary `_DICT` and `_VSTK` stacks, a new definition shadows but not deletes the previous ones: this feature will be useful for local variables.

To modify an existing variable to a new value use the word `LET` which has priority 0 and does the following.

- At compile time
    - Scan a word *w* and looks for it inside the dictionary.
    - If *w* is not found an error is raised.
    - Scan a word raising an error if is not `=`.
    - Compile the instruction `VSTORE(i)` with priority 50, thus pushes (50, `VSTORE`, *i*) on `_DSTK`.
- Runtime effects:
    - Pop the result of the evaluation of the expression following `=` and store it at `_VSTK[i]`.

For example the following sequence of instructions

```
    DEF x = 1
    LET x = x + 1
    PRINT x
    LET x = x * 2
    PRINT x
```

will print 2 and 4.

You could be annoyed by the fact that we need the keyword `LET` before the actual assignment, but to do otherwise would mean to complicate things quite enough.

For example, we could introduce a state variable `_STATE` such that the system is by default in the state 0 in which, say, mentioning variables means to push their *address* on the stack, while after the `=` sign th esystem would enter in a state in which mentioning variables means to push their value on the stack; next we would define a word to restore the 0 state, say ";". For example we could write `x = x + 1 ;` so that the `x` on the left of `=`, in the 0 state, pushes the address of `x`, the `=` word compiles a `VSTORE1` routine which pops a value and an address from the stack and stores the value at the address; moreover the word `=` would set `_STATE` to 1 so that the next parsed `x` would result in compiling `VPUSH`, while the ending `;` would reset `_STATE` to 0.

The same state change should occur elsewhere, wherever the value of a variable needs to be retrieved and not its value to be changed.

States are not a bad idea in themselves, but they introduce complexity and the temptation to use a same word with different meaning in different states; to do all that just not to write `LET` seems excessive to me: as Alan Perlis remarked, *syntactic sugar causes cancer of the semicolon*.

Variables defined by means of `DEF` can contain a memory cell value, thus a floating point number or an address: for example we can store strings into variables, by means of a curios word, the double quote, which is a special character: it does the following.

- At compile time:
    - Scans characters until the next double quote is found and stores them into a buffer, returning its address a.
    - If no double quote follows the opeining one, a *End of file inside string* error is raised and execution is stopped.
    - Compiles `PUSH`(a).
-  At runtime:
    - The address of the string is pushed on the stack

In this toy WTF Python implementation we may take advantage of the fact that operators are overloaded to manipulate strings. For example the following shall work:

```
    DEF s1 = "alpha"
    DEF s2 = "numerical"
    PRINT s1 + s2   \ This prints "alphanumerical"
    LET s1 = "semi"
    PRINT s1 + s2   \ This prints "seminumerical"
```

However this is more a bug than a feature: future versions of the language will provide specific words for string manipulation.

Atomic variables aside, WTF provides just one structured data type, of course the stack one. To define a new stack variable use the `STACK` declaration, which allocates a new empty stack and assigns it to a new variable.

The `STACK` word:

- At compile time:
    - Pushes `[]` on `_VSTK` and get the address *i* of it.
    - Scan a word *w* and insert a definition (*w*, 255, `VPUSH`, *i*) on `_DICT`.
- At runtime: it does nothing!

To handle a stack one needs just two words, one to push and the other to pop data: WTF provides

- `POP`, a word with priority 200 which pops the topmost element of a stack and returns it on the `_DSTK`: if the stack is empty an error is raised.
- `PUSH`, a word with priority 10 which accepts two parameters, taking the first as a stack and the second as an element to push on that stack.
- `TOS` which acts like `POP` but does not remove the top from the stack.
- `LEN`, a word with priority 200, which returns the number of elements in a stack (0 if the stack is empty)

For example:

```
    STACK s         \ At start s = []
    PUSH(s 1)       \ Now s = [1]
    s PUSH 2        \ Now s = [1 2]
    (PUSH s 3)      \ Now s = [1 2 3]
    s 4 PUSH        \ Now s = [1 2 3 4]
    PRINT s         \ Nice to have: it prints the stack
    PRINT TOS s     \ Prints 4
    PRINT LEN s     \ Prints 4
```

However WTF allows to use stacks as lists: to get the *i*-th element of a stack (where the bottomest element has index 0) use the classical notation *s*`[`*i*`]`, for example:

```
    STACK s
    PUSH s 1 PUSH s 2 PUSH s 3 PUSH s 4
    PRINT s[LEN(s) - 1]     \ Prints 4
    PRINT s[NEG 1]          \ Prints 4
    PRINT s[0]              \ Prints 1
```

Notice that brackets are special characters just as parentheses. Notice also that negative indexes are added to `LEN s` so we have the same effect as in Python.

To change an element of a stack we cannot use this same notation, unless we introduce states, so we stick to the classical Algol-68 notation by means of the `OF` word, which is used as *index* `OF` *stack* `=` *value*.

`OF` has priority 0, parses the word following it, expects it to be a stack variable and parses the `=` following it. Next it compiles a subroutines which pops from the stack the index, the value to assign and stores the latter inside the appropriate element of the stack.

Example:

```
    DEF i = 0
    STACK s
    PUSH(s 1) PUSH(s 2) PUSH(s 3)
    PRINT s[1]      \ Print 2
    1 OF s = 10     \ Now s = [1 10 3]
    PRINT s[1]      \ Print 10
```

To provide meaningful examples we need control structures such as `if`, `while` and `for` of other languages. Let's add them.

### 3.4. Control structures

Once pairs *(r,v)* have been compiled in the `_CSTK` the latter is be executed by means of the following function:

```Python
_IP = -1    # index in _CSTK of next instruction to execute

def execute():
    global _IP
    _IP = 0
    while _IP < len(_CSTK):
        _IP += 2
        _CSTK[_IP-2](_CSTK[_IP-1])
    _IP = -1
```

The `_IP` global variable contains the index of the next pair *(r,v)* to execute: by defining routines that mess with the `_IP` during execution we can easily implement control structures, as words which are executed during compilation and that compile jumps etc. writing jump addresses after the jump instruction has been compiled.

Let us consider conditionals first: we borrow from Algol-68 the following conditional structure:

```
    IF e THEN s
    ELIF e_1 THEN s_1
    ...
    ELIF e_n THEN s_n
    ELSE t
    FI
    ...
```

No need to explain it: maybe it is of some interest how it can be compiled. Each word `IF THEN ELIF ELSE FI` has priority 0, this it is executed at compile time, and it communicates with other words, that cannot be avoided, by means of a stack `_PSTK`(I do not remember anymore what the *P* stands for).

The compiled code resulting from the previous snippet should go as follows (labels on the left are indexes to `_CSTK`)

```
    i_0:    e
    i_1:    JPZ(i_2+2)  \ Compiled by THEN
    i_1+2:  s
    i_2:    JP(i_8)     \ Compiled by ELIF
    i_2+2:  e_1
    i_3:    JPZ(i_4+2)  \ Compiled by THEN
    i_3+2:  s_1
    i_4:    JP(i_8)     \ Compiled by ELIF
    i_4+2:  ...
    i_5:    e_n
    i_6:    JPZ(i_7+2)  \ Compiled by THEN
    i_6+2:  s_n
    i_7:    JP(i_8)     \ Compiled by ELSE
    i_7+2:  t
    i_8     ...
```

The `JP(i)` routine sets `_IP = i` and the `JPZ(i)` does it only if the top of `_DSTK`(which is removed) is zero. A moment of Zen meditation should convince the reader that indeed this sequence does what it should.

The only difficulty in compiling this code is that, say, the argument of `JP` compiled by `ELIF` will be known only when `FI` will be interpreted, so the location in che code where to store this address must be stored on the `_PSTK` so that `FI` could retrieve it: this is done by each `ELIF` word, so that actually a list of such addresses is maintaned (see the implementation in [wtf.py](wtf.py) for more information and the complete implementation).

For example, the code

```
    DEF x = 20
    IF x = 1 THEN
        PRINT 1
    ELIF x = 2 THEN
        PRINT 2
    ELIF x = 3 THEN
        PRINT 2
    ELIF x >= 0 THEN
        PRINT 10
    ELSE
        PRINT -10
    FI
```

is compiled as (we mark with a comment the instruction followed by the compiled code: indexes on the left are indexes to `_CSTK` elements; jumps to 64 are out of range and makes execution to stop).

```
\ DEF x = 20
    00: PUSH(20.0)
    02: VSTORE(0)       \ Pop 20 and store it into x
    04: VPUSH(0)        \ Push the value of x
\ IF x = 1
    06: PUSH(1.0) 
    08: EQ(None)        \ x = 1?
    10: JPZ(18)         \ If not jump to 18
\ THEN PRINT 1
    12: PUSH(1.0)
    14: PRINT(None)
    16: JP(64)          \ Jump outside code stack = END
\ ELIF x = 2  
    18: VPUSH(0)        \ Push the value of x
    20: PUSH(2.0)
    22: EQ(None)        \ x = 2?
    24: JPZ(32)         \ If not jump to 32
\ THEN PRINT 2
    26: PUSH(2.0)
    28: PRINT(None)
    30: JP(64)          \ Jump outside code stack = END
\ ELIF x = 3
    32: VPUSH(0)
    34: PUSH(3.0)
    36: EQ(None)        \ x = 3?
    38: JPZ(46)         \ If not jump to 46
\ THEN PRINT 3
    40: PUSH(3.0)
    42: PRINT(None)
    44: JP(64)          \ Jump outside code stack = END
\ ELIF x >= 0
    46: VPUSH(0)
    48: PUSH(0.0)
    50: GEQ(None)       \ x >= 0?
    52: JPZ(60)         \ If not jump to 60
\ THEN PRINT 10
    54: PUSH(10.0)
    56: PRINT(None)
    58: JP(64)          \ Jump outside code stack = END
\ ELSE PRINT -10
    60: PUSH(-10.0)
    62: PRINT(None)
\FI
```

Next we come to loops: I've inserted two classical loop structures into the language, more can be easily added. The first one is the undefined loop based on the `WHILE` word, which is used as `WHILE e DO s OD`.

The effect is to execute *s* if and as long as the condition *e* is not zero: the words `WHILE DO` and `OD` cooperates to compile the following code:

```
    i_0:    e
    i_1:    JPZ(i_2+2)  \ Compiled by DO
    i_1+2:  s
    i_2:    JP(i_0)     \ Compiled by OD
    i_2+2:  ...
```

The `WHILE` words mark where `OD` should compile the backward jump. For example,

```
    DEF x = 10
    WHILE x >= 0 DO
        PRINT x
        LET x = x - 1
    OD
```

is compiled as

```
\ DEF x = 10
    00: PUSH(10.0)
    02: VSTORE(0)       \ Pop 0 and stores it into x
\ WHILE x >= 0
    04: VPUSH(0)
    06: PUSH(0.0)
    08: GEQ(None)       \ x >= 0?
    10: JPZ(26)         \ If not jump to 26
\ DO
\ PRINT x
    12: VPUSH(0)
    14: PRINT(None)
\ LET x = x - 1
    16: VPUSH(0)
    18: PUSH(1.0)
    20: SUB(None)
    22: VSTORE(0)
\ OD
    24: JP(4)
```

While the syntax of the while-loop resembles Algol-68, the for-loop is taken from BASIC:

```
    FOR w = e1 TO e2 DO
        s
    NEXT
```

In this case, `FOR` defines a new variable and initializes it to *e1* (so it is equivalent to `DEF w = e1`), while `TO` compiles a while-condition which is true until *w < e2* (beware, if *e1 = e2* the loop is not iterated anymore!) and `NEXT` compiles the code which increases the loop variable (it would be possible let `DO` do this with a little more effort).

So the compiled code is as follows:

```
    i_0:    e_1
    i_0+2:  VSTORE(v)
    i_0+4:  VPUSH(v)
    i_0+6:  e_2
    i_0+8:  LT(NIL)
    i_0+10: JPZ(i_1+4)
    i_0+12: s
    i_1:    VINCR(v)
    i_1+2:  JP(i_0+4)
    i_1+4:  ...

```

For example consider the loop to find an element in a stack by a linear search:

```
    STACK s
        PUSH(s 3)
        PUSH(s -1)
        PUSH(s 0)
        PUSH(s 2)
    
    DEF to-find = 0
    FOR i = 0 TO LEN(s) DO
        IF s[i] = to-find THEN
            PRINT i
        FI
    NEXT
```

This is compiled as (the 0-th element of `_VSTK` contains the value of `s`, the 1-th element of `_VSTK` contains the value of `to-find` and the 2-th of `_VSTK` contains the value of `i`):

```
\ STACK s
\ PUSH(s 3)
    00: VPUSH(0)
    02: PUSH(3.0)
    04: SPUSH(None)
\ PUSH(s -1)
    06: VPUSH(0)
    08: PUSH(-1.0)
    10: SPUSH(None)
\ PUSH(s 0)
    12: VPUSH(0)
    14: PUSH(0.0)
    16: SPUSH(None)
\ PUSH(s 2)
    18: VPUSH(0)
    20: PUSH(2.0)
    22: SPUSH(None)
\ DEF to-find = 0
    24: PUSH(0.0)
    26: VSTORE(1)
\ FOR i = 0
    28: PUSH(0.0)
    30: VSTORE(2)
\ TO LEN(s)
    32: VPUSH(2)
    34: VPUSH(0)
    36: SLEN(None)
    38: LT(None)
    40: JPZ(62)
\ DO
\ IF s[i] = to-find
    42: VPUSH(0)
    44: VPUSH(2)
    46: IPUSH(None)
    48: VPUSH(1)
    50: EQ(None)
    52: JPZ(58)
\ THEN PRINT i
    54: VPUSH(2)
    56: PRINT(None)
\ FI
\ NEXT
    58: VINCR(2)    \ Increases _VSTK[2], thus i
    60: JP(32)      \ Repeat the loop
```

Of course one could provide a specific loop to scan elements of a stack, and also introduce for-loops that decreases the loop variable downto a lower limit.

### 3.5. Subroutines

The final step toward a minimal but decent programming language will be the introduction of user defined subroutines (or procedures or function or methods or whatever you call them). Even if it would be possible to introduce a general construction to define any word with any priority: I'll rather allow to define just:

- *Commands*, user defined words with priority 0.
- *Procedures*, words with priority 10 (such as `PRINT`).
- *Functions*, words with priority 250.

It'll turn out that our stack discipline for variables implies a rough concept of local variable without changes at all!!!

I shall describe PROCedures: the case of ComManDs and FUNCtions will be similar. The syntax is

```
    PROC w
        ...
    EMD
```

First we'll need some runtime routine to fetch and store data inside this stack:

- `CALL(i)` which pushes `_IP` on `_VSTK`.
- `RET(i)` which pops from `_VSTK` an address which is stored in `_IP`.

`PROC` is a priority 0 word that parses the next word *w* and inserts a new definition *(w, 10, `CALL`, a)* where *a* is the address of a stack where the words between $w$ and `END` are compiled. The `END` command compiles `RET` (which pairs `CALL`) and restores the compilation to `_CSTK`.

More precisely

- At compile time `PROC`:
    - Saves on `_PSTK` the address of `_CSTK`.
    - Allocates a new empty stack and assigns it to `CSTK`.
    - Scan a word *w* and insert a definition (*w*, 10, `CALL`, `_CSTK`) on `_DICT`.
    - Saves on `_PSTK` the index of the last element of the dictionary.
- Runtime effects:
    - `PROC` has no direct runtime effects but the word *w* it defines when compiled will perform a CALL to the code compiled between `PROC` and `END`.

- At compile time `END`:
    - Compiles all words pending in the `_DSTK`.
    - Compiles (`RET`, `NIL`) on `_CSTK`.
    - Pops from `_PSTK` the index of the word definition preceding any definition given between `PROC` and `END` and deletes all those entries.
    - Pops from `_PSTK` the previous value of `_CSTK`.

Thus, not only `PROC` allocates a new code stack and makes it the current one, saving the previous one, but also compiles the call to this routine and marks the end of the dictionary, so that `END` will restore it, deleting any definition local to the `PROC` ... `END` block.

In this way local variables may be defined via the same `DEF`, `STACK` and even `PROC` words!

For example consider:

```
    PROC swap01
        DEF s = \ Parameter
    
        PROC swap   \ swap(s i j)
            DEF j = \ Parameter
            DEF i = \ Parameter
            DEF s = \ Parameter
            DEF temp = s[i]
            i OF s = s[j]
            j OF s = temp
        END
        swap(s 0 1)
    END
    
    STACK s
    PUSH(s 0) PUSH(s 1) PUSH(s 2) PUSH(s 3)
    
    PRINT s
    swap01(s)
    PRINT s
```

This will print first `[0.0, 1.0, 2.0, 3.0]` and then `[1.0, 0.0, 2.0, 3.0]`. Notice that we omit the argument in a procedure parameter so that it will pop it from the stack where the caller pushed it. Namely, when we write `swap01(s)` we push `s` on the stack and call the `swap01` routine whose first instruction `DEF` assigns at runtime the value to its local variable `s` defined at compile time (at a different location than the `s` defined at global scope).

Notice also that formal parameters are defined in the procedure in inverse order w.r.t. the actual ones, still because we are using a stack: one could try several tricks to avoid that, but I didn't.

Variables defined at outer scope are still available in nested scopes so that we could use the outer `s` variable inside both `swap01` and `swap`. Since we are using stacks to store both compile time definitions and runtime variables, nested procedures works automatically. 

However notice that variables in `_VSTK` still are allocated at compile time: they are never disposed while the definitions that refers to them can be deleted. Since e are allocating space for values at compile time, calling a function time and again will result in using the same location for its local variable. Thus recursion is not allowed (this is the storage organization of the old versions of Fortran, as Fortran IV).

But consider the snippet:

```
FUNC fact
    DEF x =
    IF x <= 1 THEN 1
    ELSE x * fact(x - 1)
    FI
END

FOR x = 1 TO 11 DO
    PRINT fact(x)
NEXT
```

It'll work!!! That is because the recursion in this case is a tail recursion: since we do not allocate a new instance of a variable at runtime but only at compile time, general recursion won't work.

So,if you want WTF recursion you'll have to modify the compiler so to generate space for variables at runtime, not at compile time.

### 3.6. Odds & Ends

I have added some words to handle files and even to include and compile another source file: the next step would be to provide words to encapsulate data inside a file so to export only part of it when included.

The word `INCLUDE` scans the word following it, interpret it as a file name and opens this file, saving the current one on `_PSTK`. The effect is the same with C inclusions, just the text of the included file is immediately compiled where the `INCLUSION` word appears.

To deal with file use the following words:

- `OPEN`(name mode) which has priority 200 and opens the file whose name is provided with the given mode (as in C and Python it can be "r", "w", "a"): both name and mode of the file should be strings, we already discussed them above when describing the `DEF` word. The function returns a handle to the file, or the `NIL` pointer if the opening failed.
- `CLOSE`(handle) which has priority 10 and closes an opened file, given its handle.
- `FGET`(handle) which parses a single character from the given file and returns it on the stack: it has priority 200.
- `FPUT`(handle c) which writes a single character into the given file: the character is passed as number, and transformed into the corresponding ASCII character.

A couple of useful functions are:

- `ROUND`(e) which rounds a number to the nearest integer.
- `RAND` which has priority 255 and no parameters, and pushes on the stack a random number between 0 and 1.

What next? One can improve, in several ways this language by, say:
- include more I/O stuff and exception handling;
- introduce structures, objects, coroutines.
- make compiled codes first class objects: for example code inside `\{` and `\}` could be compiled somewhere and the address returned on the stack to be used as value for a variable etc.;

Moreover, with little effort the core routines of the program, such as the scanner, the compiler and the interpreter of the compiled code, may be made words accessible by the language itself, as well as built-in stacks may. One could also try to write the compiler in WTF itself, bootstrapping it with the bare amount of foreign code needed.

More on that in future projects, this one had as only purpose to show some classic techniques in a non standard way and promote the ideas in Moore's book.

## 4. Usage and Builtin words

In this section the complete list of words built-in the dictionary at start up is provided for the [wtf.py](wtf.py) interpreter.

Launch the interpreter as

```bash
    $ python --dump-obj --dump-dict --dump-vars SOURCE-FILE
```

being the switches optional and disabled by default. Only a single source can be compiled: use `INCLUDE` to compile several sources in a single session.

In the following, when describing the runtime operations, the term "stack" will mean `_DSTK`, TOS will refer to its topmost element, 2OS to the element below TOS, and so forth. When referring to other stacks, they will always be explicitly mentioned.

The list of all words follows.

### Newline (the newline character)

- Priority = 0.
- Compile time: compiles all words in the `_DSTK` with priorities >0. 

### `"`

- Priority = 0.
- Compile time: scans characters until a double quote is found and creates a string with those characters (excluded the final double quote. If no double quote follows, exits with an error.
- Runtime: The address of the string is pushed on the stack.

### `(`

- Priority = 0.
- Compile time: pushes a fake word (0, ")", `NIL`) on the stack.

### `)`

- Priority = 0.
- Compile time: pops and compiles words from `_DSTK` to `_CSTK` until the fake word (0, ")", `NIL`) which is just removed. If no such fake word is found, an error is raised.

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
- Compile time: scans a word *w* and creates a new definition (*w*, 0, `CMD`, *v*) being *v* the address of a stack that will contain the code compiled until the matching `END`. The `CMD` runtime routine invokes a subroutine at compile time, while `CALL` does it at runtime.

### `DEF` w `=` ...

- Priority = 0.
- Compile time: scans a word *w* and creates a new zero numeric variable definition (*w*, 0, `VPUSH`, *v*) being *v* the index in `_VSTK`of the new variable's value. Furthermore the `=` word is scanned, raising an error if not following *w*.
- Runtime: assigns to *w* the value of the expression following `=`.

### `DO`

- Priority = 0.
- Compile time: matches a previous `WHILE` or `TO` and prepares a match for the corresponding `DO`; compiles all words in the `_DSTK` with priorities >0.
- Runtime: it the loop condition is not satisfied, jump after the matching `OD`.


### `ELIF`

- Priority = 0.
- Compile time: same as `ELSE` but prepares a match for `THEN`.
- Runtime: same as `ELSE`.

### `ELSE`

- Priority = 0.
- Compile time: matches a previous `THEN`, compiles all words in the `_DSTK` with priorities >0, pushes on `_PSTK` a reference to the argument of the jump to the end of the `IF-FI` structure, completes the jump compiled by the previous `THEN`, prepares a match for the corresponding `THEN`.
- Runtime: skip the following code if the condition on the stack is zero

### `END`

- Priority = 0.
- Compile time: matches a previous `CMD`, `FUNC` or `PROC`, compiles all words in the `_DSTK` with priorities >0, pops an index to `_DICT` from `_PSTK` and delete all items downto that index, pops `_CSTK` from `_PSTK`.
- Runtime: Returns from the current subroutine.

### `FCLOSE`

- Priority = 10.
- Runtime: pops a file descriptor and closes the file; exits on error.

### `FGET`

- Priority = 200.
- Runtime: pops a file descriptor, reads a character from the file and pushes its ASCII code on the stack; exits on error.

### `FI`

- Priority = 0.
- Compile time: matches a previous `THEN` or `ELSE`, compiles all words in the `_DSTK` with priorities >0, pops from `_PSTK` jump addresses where to store the current compiling address.

### `FOPEN`

- Priority = 200.
- Runtime: pops a mode string, pops a name string, opens the file with that name in that mode ("r", "w", "a") and returns a handle to it (an address); exits on error.

### `FOR`

- Priority = 0.
- Compile time: same as `DEF` but pushes the variable address on `_PSTK` and prepares a match for the corresponding `TO`.
- Runtime: assigns to the loop variable the initial value.

### `FPUT`

- Priority = 10.
- Runtime: pops an ASCII code, pops a file handle, writes the character with that code on the file; exits on error.

### `FUNC`

- Priority = 0.
- Compile time: scans a word *w* and creates a new definition (*w*, 250, `CALL`, *v*) being *v* the address of a stack that will contain the code compiled until the matching `END`.

### `IF`

- Priority = 0.
- Compile time: compiles all words in the `_DSTK` with priorities >0, prepares a match for `THEN`.

### `INCLUDE`

- Priority = 0.
- Compile time: pushes on `_PSTK` the reference to the current source file (handle, name, line number), scans a word and pushes it as a string on the stack, pushes "r" on the stack, performs `FOPEN` and assigns the resulting handle to the current source handle, compile the file, closes it and restores the previous values for the source file. Exits on error.

### `LEN`

- Priority = 200.
- Runtime: pops the index of a variable from the stack, consider it as a stack and pushes its length on the stack.

### `LET` w `=` ...

- Priority = 0.
- Compile time: scans a word *w* and check if a variable with that name exists (if not an error is raised), the `=` word is scanned, raising an error if not following *w*.
- Runtime: assigns to *w* the value of the expression following `=`.

### `NEG`

- Priority = 120.
- Runtime: pops a number and pushes its negation on the stack.

### `NEXT`

- Priority = 0.
- Compile time: matches a previous `DO`, pops from `_PSTK` the jump address where to store the address just after the loop, pops from `_PSTK` the index of the loop variable, pops from `_PSTK` the address where to jump to iterate the loop and compiles the variable increasing and the jump.
- Runtime: increases the loop variable and repeats the `FOR` loop from the conditon compiled by `TO`.

### `NIL`

- Priority = 255.
- Runtime: pushes the null pointer on the stack.

### `NOT`

- Priority = 80.
- Runtime: pops a number and pushes 1 if the number is 0, else pushes 0.

### `OD`

- Priority = 0.
- Compile time: matches a previous `DO`, pops from `_PSTK` the jump address where to store the address just after the loop, pops from `_PSTK` the address where to jump to iterate the loop and compiles the jump.
- Runtime: repeats the `WHILE` loop.

### `OF`

- Priority = 0.
- Compile time: scans a word *w* and check if a variable with that name exists (if not an error is raised), the `=` word is scanned, raising an error if not following *w*.
- Runtime: pops an index *i* and assigns to the *i*-th element of the stack *w* the value of the expression following `=`.

### `OR`

- Priority = 60.
- Runtime: pops two numbers and pushes 0 if both numbers are 0, else pushes 1.

### `POP`

- Priority = 200.
- Runtime: pops the address of a stack, pops an element from it and pushes it. Exits on error.


### `PRINT`

- Priority = 10.
- Runtime: pops a number and prints it (it works also for strings and stacks).

### `PROC`

- Priority = 0.
- Compile time: scans a word *w* and creates a new definition (*w*, 10, `CALL`, *v*) being *v* the address of a stack that will contain the code compiled until the matching `END`.

### `PUSH`

- Priority = 20.
- Runtime: pops an item, pops a stack, pushes the item on the stack.

### `RAND`

- Priority = 255.
- Runtime: pushes a pseudo-random number between 0 (included) and 1 on the stack.

### `ROUND`

- Priority = 200.
- Runtime: pops a number, pushes its nearest integer.

### `STACK`

- Priority = 0.
- Compile time: scans a word *w* and creates a new empty stack variable definition (*w*, 0, `VPUSH`, *v*) being *v* the index in `_VSTK`of the new variable's value.

### `THEN`

- Priority = 0.
- Compile time: matches a previous `IF`, compiles all words in the `_DSTK` with priorities >0, pushes on `_PSTK` the jump address to be written by `ELIF`, `ELSE` or `FI`, prepares a match for `ELIF`, `ELSE` or `FI`.
- Runtime: skip the following code if the condition on the stack is zero

### `TO`

- Priority = 0.
- Compile time: matches a previous `FOR`, compiles all words in the `_DSTK` with priorities >0, compiles the loop termination condition, pushes on `_PSTK` a jump address, the index of the loop variable and a match for `DO`.
- Runtime: if the loop variable is greater or equal to the expression following `TO` then skip the loop, else perform it.

### `TOS`

- Priority = 200.
- Runtime: pops a stack, pushes its topmost element without popping it.

### `WHILE`

- Priority = 0.
- Compile time: compiles all words in the `_DSTK` with priorities >0, pushes on `_PSTK` the initial address of the loop and a match for `DO`.

### `[`

- Priority = 0.
- Compile time: pushes a fake word (0, "]", `NIL`) on the stack.

### `\`

- Priority = 0.
- Compile time: scans and discards each character until a newline or the end of the file is found

### `]`

- Priority = 0.
- Compile time: pops and compiles words from `_DSTK` to `_CSTK` until the fake word (0, "]", `NIL`) which is just removed. If no such fake word is found, an error is raised.
- Runtime: pops from the stack an index *i* a stack variable *s* and pushes the *i*-th element of *s* on the stack.

