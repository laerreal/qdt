from common import (
    Persistent,
    ee,
    pypath
)
from os.path import (
    join
)
from six.moves.tkinter import (
    Toplevel,
    SEL,
    CURRENT,
    HORIZONTAL,
    END,
    Tk,
    Text,
    Scrollbar
)
from six.moves.tkinter_ttk import (
    Treeview
)
from six.moves.tkinter_font import (
    NORMAL,
    ITALIC
)

with pypath("..ply"):
    from ply.yacc import (
        YaccSymbol,
        yacc
    )
    from ply.lex import (
        LexToken,
        join as join_tokens,
        lex
    )
    from ply.helpers import (
        iter_tokens
    )

def t_COMMENT_ML(t):
    "/[*](.|\\n|\\r)*?[*]/"
    t.lexer.lineno += t.value.count('\n') + t.value.count('\r')

for kw in ["package", "class", "extends", "public", "return", "true", "false",
    "new", "for", "static", "final", "if", "else", "import", "try", "catch",
    "switch", "case", "break", "default", "instanceof", "abstract", "private",
    "implements", "throw", "while"
]:
    exec("""\
def t_%s(t):
    "%s(?=\\W)"
    t.tag = "keyword"
    return t
    """ % (kw.upper(), kw))

def t_WORD(t):
    "[a-zA-Z][_a-zA-Z0-9]*"
    return t

def t_INTEGER(t):
    "[0-9]+(?=[^.e])"
    t.tag = "int"
    return t

def t_FLOAT(t):
    "(([0-9]+[.][0-9]+)|([.][0-9]+)|([0-9]+[.]?))(e-?[0-9]+)?"
    t.tag = "float"
    return t

def t_INC(t):
    "[+][+]"
    return t

def t_DEC(t):
    "--"
    return t

t_LT = r"<"
t_GT = r">"
t_LE = r"<="
t_GE = r">="

def t_EQ(t):
    r"=="
    return t

t_NE = r"!="

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

t_OR = r'\|'
t_AND = r'&'
t_XOR = r'\^'
t_LSHIFT = r'<<'
t_RSHIFT = r'>>'

t_LNOT = r'!'
t_NOT = r'~'

t_LOR = r'\|\|'
t_LAND = r'&&'

t_TIMESEQUAL = r'\*='
t_DIVEQUAL = r'/='
t_MODEQUAL = r'%='
t_PLUSEQUAL = r'\+='
t_MINUSEQUAL = r'-='
t_LSHIFTEQUAL = r'<<='
t_RSHIFTEQUAL = r'>>='
t_ANDEQUAL = r'&='
t_OREQUAL = r'\|='
t_XOREQUAL = r'\^='

def t_ASSIGN(t):
    "="
    return t

def t_LB(t):
    "{"
    return t

def t_RB(t):
    "}"
    return t

def t_LBE(t):
    "\\("
    return t

def t_RBE(t):
    "\\)"
    return t

def t_LBT(t):
    "\\["
    return t

def t_RBT(t):
    "\\]"
    return t

def t_SC(t):
    ";"
    return t

def t_DOT(t):
    "[.]"
    return t

def t_COMMENT_SL(t):
    "//.*"

def t_SPACE(t):
    "[ \\t]"

def t_NL(t):
    "[\\r\\n]"
    t.lexer.lineno += 1

def t_COMMA(t):
    ","
    return t

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.tag = "string"
    return t

def t_CHAR(t):
    r"'[a-zA-Z0-9]'"
    t.tag = "char"
    return t

def t_COLON(t):
    ":"
    return t

def t_CONDOP(t):
    "[?]"
    return t

tokens = tuple(k[2:] for k in globals() if k[:2] == "t_")

def t_error(t):
    raise RuntimeError(t)

def p_module(p):
    "module : package imports class_def"

def p_package(p):
    "package : PACKAGE dot_expr SC"

def p_import(p):
    "import : IMPORT dot_expr SC"

def p_imports(p):
    """ imports :
                | imports import
    """

def p_dot_expr(p):
    """ dot_expr : dot_expr DOT WORD
                 | WORD DOT WORD
                 | dot_expr DOT CLASS
                 | WORD DOT CLASS
    """

def p_class_def(p):
    """ class_def : class_spec CLASS WORD inheritance LB methods_def RB
    """

def p_parent(p):
    """ parent : EXTENDS WORD
    """

def p_interfaces(p):
    """ interfaces : IMPLEMENTS WORD
                   | interfaces COMMA WORD
    """

def p_inheritance(p):
    """ inheritance : parent
                    | parent interfaces
                    | interfaces parent
                    | interfaces
    """

def p_class_spec(p):
    """ class_spec : access
                   | ABSTRACT access
                   | access ABSTRACT
    """

def p_methods_def(p):
    """ methods_def :
                    | methods_def constructor_def
                    | methods_def method_def
                    | methods_def field_def
                    | methods_def fields_def
    """

def p_constructor_def(p):
    """ constructor_def : def_spec WORD LBE args_def RBE LB commands RB
    """

def p_method_def(p):
    """ method_def : def_spec type_spec WORD LBE args_def RBE LB commands RB
    """

def p_type_spec(p):
    """ type_spec : WORD
                  | WORD LBT RBT
    """

def p_field_def(p):
    "field_def : def_spec var_decl SC"

def p_fields_def(p):
    """ fields_def : def_spec type_spec vars_def SC
    """

def p_vars_def(p):
    """ vars_def : var_def
                 | var_def ASSIGN expr
                 | vars_def COMMA var_def
    """

def p_var_def(p):
    """ var_def : WORD
                | WORD LBT RBT
    """

def p_storage(p):
    """ storage :
                | FINAL
                | STATIC
    """

def p_access(p):
    """ access :
               | PUBLIC
               | PRIVATE
    """

def p_def_spec(p):
    """ def_spec : storage access storage
    """

def p_args_def(p):
    """ args_def :
                 | arg_def
                 | args_def COMMA arg_def
    """

def p_arg_def(p):
    """ arg_def : type_spec var_def
    """

def p_commands(p):
    """ commands :
                 | commands command
    """

def p_command(p):
    """ command : for
                | if
                | try
                | var_decl SC
                | call SC
                | return SC
                | assign SC
                | break SC
                | switch
                | SC
                | throw SC
                | while
    """

def p_throw(p):
    "throw : THROW expr"


def p_break(p):
    "break : BREAK"

def p_var_decl(p):
    """ var_decl : arg_def
                 | arg_def ASSIGN expr
                 | var_decl COMMA var_def
    """

def p_call(p):
    """ call : dot_expr LBE args_val RBE
             | WORD LBE args_val RBE
    """

def p_return(p):
    """ return : RETURN
               | RETURN expr
               | RETURN LBE WORD RBE
    """

def p_assign(p):
    """ assign : lval ASSIGN expr
               | lval assign_op expr
    """

def p_assign_op(p):
    """ assign_op : TIMESEQUAL
                  | DIVEQUAL
                  | MODEQUAL
                  | PLUSEQUAL
                  | MINUSEQUAL
                  | LSHIFTEQUAL
                  | RSHIFTEQUAL
                  | ANDEQUAL
                  | OREQUAL
                  | XOREQUAL
    """

def p_lval(p):
    """ lval : dot_expr
             | array_item
             | lval DOT WORD
             | WORD
    """

def p_new(p):
    "new : NEW WORD LBE args_val RBE"

def p_new_array(p):
    "new_array : NEW WORD LBT expr RBT"

def p_expr(p):
    """ expr : INTEGER
             | bool_val
             | STRING
             | ternary
             | new
             | new_array
             | call
             | expr cmp expr
             | expr arithm expr
             | unary
             | LBE expr RBE
             | expr bitwise expr
             | cast
             | CHAR
             | unary_noside
             | expr logical expr
             | FLOAT
             | expr DOT call
             | assign
             | lval
    """

def p_unary_noside(p):
    """ unary_noside : MINUS expr
                     | NOT expr
                     | LNOT expr
    """

def p_unary(p):
    """ unary : WORD un_op
              | un_op WORD
    """

def p_un_op(p):
    """ un_op : INC
              | DEC
    """

def p_array_item(p):
    """ array_item : WORD LBT expr RBT
    """

def p_ternary(p):
    """ ternary : expr CONDOP expr COLON expr
    """

def p_cast(p):
    "cast : LBE WORD RBE expr"

def p_cmp(p):
    """ cmp : LT
            | GT
            | LE
            | GE
            | EQ
            | NE
            | INSTANCEOF
    """

def p_arithm(p):
    """ arithm : PLUS
               | MINUS
               | TIMES
               | DIVIDE
               | MOD
    """

def p_bitwise(p):
    """ bitwise : OR
                | AND
                | XOR
                | LSHIFT
                | RSHIFT
    """

def p_logical(p):
    """ logical : LOR
                | LAND
    """

def p_bool_val(p):
    """ bool_val : TRUE
                 | FALSE
    """

def p_args_val(p):
    """ args_val :
                 | arg_val
                 | args_val COMMA args_val
    """

def p_arg_val(p):
    """ arg_val : expr
    """

def p_for(p):
    """ for : for_header LB commands RB
            | for_header command
    """

def p_for_header(p):
    "for_header : FOR LBE comma_commands SC expr SC comma_commands RBE"

def p_comma_commands(p):
    """ comma_commands :
                       | assign
                       | unary
                       | comma_commands COMMA comma_commands
    """

def p_if_header(p):
    "if_header : IF LBE expr RBE"

def p_if(p):
    """ if : if_header LB commands RB
           | if_header command
           | if_header LB commands RB ELSE else
           | if_header command ELSE else
    """

def p_else(p):
    """ else : LB commands RB
             | command
    """

def p_try(p):
    """ try : TRY LB commands RB CATCH LBE WORD WORD RBE LB commands RB
    """

def p_switch(p):
    """ switch : SWITCH LBE expr RBE LB cases RB
    """

def p_cases(p):
    """ cases : case
              | default
              | cases cases
    """

def p_case(p):
    """ case : CASE case_const COLON commands
             | CASE case_const COLON LB commands RB
    """

def p_case_const(p):
    """ case_const : INTEGER
                   | FLOAT
                   | WORD
    """

def p_default(p):
    """ default : DEFAULT COLON commands
                | DEFAULT COLON LB commands RB
    """


def p_while(p):
    """ while : while_header LB commands RB
              | while_header command
    """

def p_while_header(p):
    "while_header : WHILE LBE expr RBE"

# Grammar post-processing

glob_snapshot = dict(globals())

def unify_rule(p_func):
    line = getattr(p_func, "co_firstlineno", p_func.__code__.co_firstlineno)
    code = "\n" * (line - 1) + """\
def _{p_func}(p):
    \"""{rule}\"""
    {p_func}(p)
    p[0] = p.slice[1:]
""".format(
        p_func = p_func.__name__,
        rule = p_func.__doc__
    )
    return exec(code, glob_snapshot)

for k, v in tuple(glob_snapshot.items()):
    if k[:2] != "p_" or k == "p_error":
        continue

    # assert ("rest",) == v(("", "rest"))

    unify_rule(v)

    globals()[k] = glob_snapshot["_" + k]

p_error = t_error

lexer = lex()
parser = yacc()

ROOT_DIR = ee("J2C_INPUT_ROOT")

def decorate_ignored(c):
    if c == " ":
        return u"\u00B7"
    elif c == "\t":
        return u"\u00BB   "
    elif c == "\n":
        return "\u2193\n"
    elif c == "\r":
        return "\u2190\n"
    else:
        return c


if __name__ == "__main__":
    root = Tk()

    root.rowconfigure(0, weight = 1)
    root.rowconfigure(1, weight = 0)
    root.columnconfigure(0, weight = 0)
    root.columnconfigure(1, weight = 1)
    root.columnconfigure(2, weight = 0)

    main_font = ("Courier", 10, NORMAL)

    # line numbers
    ln = Text(root,
        font = main_font,
        wrap = "none",
        background = "#BBBBBB",
        width = 4
    )
    ln.grid(row = 0, column = 0, sticky = "NESW")

    text = Text(root, font = main_font, wrap = "none")
    text.grid(row = 0, column = 1, sticky = "NESW")

    font_ignored = ("Courier", 10, NORMAL) # , ITALIC)
    text.tag_config("ignored", font = font_ignored, foreground = "#AAAAAA")

    text.tag_config("keyword", foreground = "#FF0000")
    text.tag_config("int", foreground = "#00AAFF")
    text.tag_config("float", foreground = "#00AAFF")
    text.tag_config("char", foreground = "#00AAFF")
    text.tag_config("string", foreground = "#AA8800")

    sbv = Scrollbar(root)
    sbv.grid(row = 0, column = 2, sticky = "NESW")

    sbh = Scrollbar(root, orient = HORIZONTAL)
    sbh.grid(row = 1, column = 0, sticky = "NESW", columnspan = 2)

    # https://stackoverflow.com/questions/32038701/python-tkinter-making-two-text-widgets-scrolling-synchronize
    def yview(*a):
        text.yview(*a)
        ln.yview(*a)

    sbv.config(command = yview)

    def text_yset(*a):
        sbv.set(*a)
        ln.yview("moveto", a[0])

    text.config(yscrollcommand = text_yset)

    def ln_yset(*a):
        sbv.set(*a)
        text.yview("moveto", a[0])

    ln.config(yscrollcommand = ln_yset)

    def xview(*a):
        text.xview(*a)
        ln.xview(*a)

    sbh.config(command = xview)
    text.config(xscrollcommand = sbh.set)

    tree_window = Toplevel(root)

    tree_window.rowconfigure(0, weight = 1)
    tree_window.rowconfigure(1, weight = 0)
    tree_window.columnconfigure(0, weight = 1)
    tree_window.columnconfigure(1, weight = 0)

    stree = Treeview(tree_window)
    # stree.column("#0", stretch = True, width = 800)
    stree.grid(row = 0, column = 0, sticky = "NESW")

    sbv2 = Scrollbar(tree_window)
    sbv2.grid(row = 0, column = 1, sticky = "NESW")

    sbh2 = Scrollbar(tree_window, orient = HORIZONTAL)
    sbh2.grid(row = 1, column = 0, sticky = "NESW")

    sbv2.config(command = stree.yview)
    stree.config(yscrollcommand = sbv2.set)

    sbh2.config(command = stree.xview)
    stree.config(xscrollcommand = sbh2.set)

    file_lineno = 0
    prev_lineno = 0

    iid2line = {}

    for fn in [
        "ADCElm.java",
        "ACRailElm.java",
        "RailElm.java",
        "VoltageElm.java",
        "CircuitElm.java",
    ]:
        FULL = join(ROOT_DIR, fn)
        with open(FULL, "r") as f:
            code = f.read()

        try:
            lexer.lineno = 1
            res = parser.parse(code, lexer = lexer, debug = False)
        except:
            lexer.lineno = 1
            parser.parse(code, lexer = lexer, debug = True)
            continue

        for t in iter_tokens(res):
            if prev_lineno > t.lineno:
                file_lineno += prev_lineno
                prev_lineno = 0

            while prev_lineno < t.lineno:
                prev_lineno += 1
                ln.insert(END, "%d\n" % prev_lineno)

            if t.prefix:
                content = ""
                for c in t.prefix:
                    content += decorate_ignored(c)

                text.insert(END, content, "ignored")

            tags = []
            try:
                tags.append(t.tag)
            except AttributeError:
                pass

            text.insert(END, t.value, *tags)

        for c in lexer.ignored:
            text.insert(END, decorate_ignored(c), "ignored")
            if c in "\r\n":
                prev_lineno += 1
                ln.insert(END, "%d\n" % prev_lineno)

        text.insert(END, "\n\n")
        ln.insert(END, "\n")

        # Build syntax tree
        sroot_iid = stree.insert("", END, text = fn, open = True)

        stack = [(sroot_iid, res)]

        while stack:
            cur_iid, symbols = stack.pop()

            if isinstance(symbols, list):
                for s in symbols:
                    stack.append((cur_iid, s))
                continue

            if isinstance(symbols, LexToken):
                s_iid = stree.insert(cur_iid, 0,
                    text = str(symbols.value),
                    open = True
                )

                lineno = symbols.lineno + file_lineno
                iid2line[s_iid] = lineno

                _iid = stree.parent(s_iid)
                while _iid:
                    if _iid not in iid2line:
                        iid2line[_iid] = lineno
                    _iid = stree.parent(_iid)

            if isinstance(symbols, (YaccSymbol)):
                s_iid = stree.insert(cur_iid, 0,
                    text = str(symbols),
                    open = True
                )
                stack.append((s_iid, symbols.value))

        # because of text.insert(END, "\n\n") below
        file_lineno += 1

    def on_stree_select(_):
        try:
            sel = stree.selection()[0]
        except:
            return
        try:
            lineno = iid2line[sel]
        except KeyError:
            return

        # print(lineno)
        start, end = "%d.0" % lineno, "%d.end" % lineno
        text.see("%d.0" % lineno)
        text.tag_remove(SEL, "1.0", END)
        text.tag_add(SEL, start, end)
        text.focus_force()

    stree.bind("<<TreeviewSelect>>", on_stree_select, "+")

    line2iid = {}
    for iid, line in iid2line.items():
        line2iid.setdefault(line, iid)

    def on_b1(e):
        line, _ = text.index("@%d,%d" % (e.x, e.y)).split(".")
        try:
            line_n = int(line)
        except ValueError:
            return
        try:
            iid = line2iid[line_n]
        except KeyError:
            return
        stree.see(iid)
        stree.selection_set(iid)

    text.bind("<Button-1>", on_b1, "+")

    with Persistent(".J2C-GUI-settings.py",
        tree_geometry = (650, 900),
        tree_offset = (650, 0),
        geometry = (650, 900)
    ) as cfg:

        def set_geom():
            root.geometry("%dx%d" % cfg.geometry)
            x = root.winfo_x() + cfg.tree_offset[0]
            y = root.winfo_y() + cfg.tree_offset[1]
            tree_window.geometry("%dx%d+%d+%d" % (cfg.tree_geometry + (x, y)))

        root.after(10, set_geom)

        def on_destroy_root(_):
            # ignore screen offset
            cfg.geometry = root.winfo_width(), root.winfo_height()

        root.bind("<Destroy>", on_destroy_root, "+")

        def on_destroy_tree(_):
            # ignore screen offset
            cfg.tree_geometry = (
                tree_window.winfo_width(), tree_window.winfo_height()
            )
            cfg.tree_offset = (
                tree_window.winfo_x() - root.winfo_x(),
                tree_window.winfo_y() - root.winfo_y(),
            )

        tree_window.bind("<Destroy>", on_destroy_tree, "+")

        root.mainloop()
