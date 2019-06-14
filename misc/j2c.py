from common import (
    pypath
)
from os.path import (
    join
)
from six.moves.tkinter import (
    Y,
    LEFT,
    BOTH,
    END,
    Tk,
    Text,
    Scrollbar
)
from six.moves.tkinter_font import (
    NORMAL,
    ITALIC
)

with pypath("..ply"):
    from ply.yacc import (
        yacc
    )
    from ply.lex import (
        join as join_tokens,
        lex
    )
    from ply.helpers import (
        iter_tokens
    )


for kw in ["package", "class", "extends", "public", "return", "true", "false",
    "new", "for", "static", "final", "if", "else", "import", "try", "catch"
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
    "[0-9]+"
    t.tag = "int"
    return t

def t_FLOAT(t):
    "([.][0-9]+)|([0-9]+[.])|([0-9]+[.][0-9]+)"
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

def t_COMMENT_ML(t):
    "/[*](.|\\n|\\r)*[*]/"
    t.lexer.lineno += t.value.count('\n') +  t.value.count('\r')

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
    p[0] = p.slice[1:]

def p_package(p):
    "package : PACKAGE dot_expr SC"
    p[0] = p.slice[1:]

def p_import(p):
    "import : IMPORT dot_expr SC"
    p[0] = p.slice[1:]

def p_imports(p):
    """ imports :
                | imports import
    """
    p[0] = p.slice[1:]

def p_dot_expr(p):
    """ dot_expr : WORD
                 | dot_expr DOT dot_expr
                 | dot_expr DOT CLASS
    """
    p[0] = p.slice[1:]

def p_class_def(p):
    """ class_def : CLASS WORD EXTENDS WORD LB methods_def RB
    """
    p[0] = p.slice[1:]

def p_methods_def(p):
    """ methods_def :
                    | methods_def constructor_def
                    | methods_def method_def
                    | methods_def field_def
                    | methods_def fields_def
    """
    p[0] = p.slice[1:]

def p_constructor_def(p):
    """ constructor_def : def_spec WORD LBE args_def RBE LB commands RB
    """
    p[0] = p.slice[1:]

def p_method_def(p):
    """ method_def : def_spec WORD WORD LBE args_def RBE LB commands RB
    """
    p[0] = p.slice[1:]

def p_field_def(p):
    "field_def : def_spec var_decl SC"
    p[0] = p.slice[1:]

def p_fields_def(p):
    """ fields_def : def_spec WORD vars_def SC
    """
    p[0] = p.slice[1:]

def p_vars_def(p):
    """ vars_def : var_def
                 | vars_def COMMA var_def
    """
    p[0] = p.slice[1:]

def p_var_def(p):
    """ var_def : WORD
                | WORD ASSIGN expr
    """
    p[0] = p.slice[1:]

def p_storage(p):
    """ storage :
                | FINAL
                | STATIC
    """
    p[0] = p.slice[1:]

def p_access(p):
    """ access :
               | PUBLIC
    """
    p[0] = p.slice[1:]

def p_def_spec(p):
    """ def_spec : storage access storage
    """
    p[0] = p.slice[1:]

def p_args_def(p):
    """ args_def :
                 | arg_def
                 | args_def COMMA arg_def
    """
    p[0] = p.slice[1:]

def p_arg_def(p):
    "arg_def : WORD WORD"
    p[0] = p.slice[1:]

def p_commands(p):
    """ commands :
                 | commands command
    """
    p[0] = p.slice[1:]

def p_command(p):
    """ command : for
                | if
                | try
                | var_decl SC
                | call SC
                | return SC
                | assign SC
    """
    p[0] = p.slice[1:]

def p_var_decl(p):
    """ var_decl : arg_def
                 | arg_def ASSIGN expr
    """
    p[0] = p.slice[1:]

def p_call(p):
    "call : dot_expr LBE args_val RBE"
    p[0] = p.slice[1:]

def p_return(p):
    "return : RETURN expr"
    p[0] = p.slice[1:]

def p_assign(p):
    """ assign : lval ASSIGN expr
               | lval assign_op expr
    """
    p[0] = p.slice[1:]

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
    p[0] = p.slice[1:]

def p_lval(p):
    """ lval : WORD
             | array_item
             | lval DOT WORD
    """
    p[0] = p.slice[1:]

def p_new(p):
    "new : NEW WORD LBE args_val RBE"
    p[0] = p.slice[1:]

def p_new_array(p):
    "new_array : NEW WORD LBT expr RBT"
    p[0] = p.slice[1:]

def p_expr(p):
    """ expr : dot_expr
             | INTEGER
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
             | array_item
             | cast
             | CHAR
             | unary_noside
             | expr logical expr
             | FLOAT
             | expr DOT call
    """
    p[0] = p.slice[1:]

def p_unary_noside(p):
    """ unary_noside : MINUS expr
                     | NOT expr
                     | LNOT expr
    """
    p[0] = p.slice[1:]

def p_unary(p):
    """ unary : WORD un_op
              | un_op WORD
    """
    p[0] = p.slice[1:]

def p_un_op(p):
    """ un_op : INC
              | DEC
    """
    p[0] = p.slice[1:]

def p_array_item(p):
    """ array_item : WORD LBT expr RBT
    """
    p[0] = p.slice[1:]

def p_ternary(p):
    """ ternary : expr CONDOP expr COLON expr
    """
    p[0] = p.slice[1:]

def p_cast(p):
    "cast : LBE WORD RBE expr"
    p[0] = p.slice[1:]

def p_cmp(p):
    """ cmp : LT
            | GT
            | LE
            | GE
            | EQ
            | NE
    """
    p[0] = p.slice[1:]

def p_arithm(p):
    """ arithm : PLUS
               | MINUS
               | TIMES
               | DIVIDE
               | MOD
    """
    p[0] = p.slice[1:]

def p_bitwise(p):
    """ bitwise : OR
                | AND
                | XOR
                | LSHIFT
                | RSHIFT
    """
    p[0] = p.slice[1:]

def p_logical(p):
    """ logical : LOR
                | LAND
    """
    p[0] = p.slice[1:]

def p_bool_val(p):
    """ bool_val : TRUE
                 | FALSE
    """
    p[0] = p.slice[1:]

def p_args_val(p):
    """ args_val :
                 | arg_val
                 | args_val COMMA args_val
    """
    p[0] = p.slice[1:]

def p_arg_val(p):
    """ arg_val : expr
    """
    p[0] = p.slice[1:]

def p_for(p):
    """ for : for_header LB commands RB
            | for_header command
    """
    p[0] = p.slice[1:]

def p_for_header(p):
    "for_header : FOR LBE comma_commands SC expr SC comma_commands RBE"
    p[0] = p.slice[1:]

def p_comma_commands(p):
    """ comma_commands :
                       | assign
                       | unary
                       | comma_commands COMMA comma_commands
    """
    p[0] = p.slice[1:]

def p_if_header(p):
    "if_header : IF LBE expr RBE"
    p[0] = p.slice[1:]

def p_if(p):
    """ if : if_header LB commands RB
           | if_header command
           | if_header LB commands RB ELSE if
           | if_header command ELSE if
           | if_header LB commands RB ELSE else
           | if_header command ELSE else
    """
    p[0] = p.slice[1:]

def p_else(p):
    """ else : LB commands RB
             | command
    """
    p[0] = p.slice[1:]

def p_try(p):
    """ try : TRY LB commands RB CATCH LBE WORD WORD RBE LB commands RB
    """
    p[0] = p.slice[1:]

# DEBUG

for k, v in tuple(globals().items()):
    if k[:2] != "p_":
        continue

    # assert ("rest",) == v(("", "rest"))

    if False:
        # XXX: I do not know, why this does not work
        globals().pop(k)

        code = """\
def %s(p):
\"""%s\"""
p[0] = p.slice[1:]
""" % (k, v.__doc__)

        print(code)
        exec(code)

p_error = t_error

lexer = lex()
parser = yacc()

ROOT_DIR = "/home/real/me/circuit/circuitjs/src/src/com/lushprojects/circuitjs1/client"

if __name__ == "__main__":
    root = Tk()

    text = Text(root, font = ("Courier", 10, NORMAL))
    text.pack(fill = BOTH, expand = True, side = LEFT)

    font_ignored = ("Courier", 10, ITALIC)
    text.tag_config("ignored", font = font_ignored, foreground = "#AAAAAA")

    text.tag_config("keyword", foreground = "#FF0000")
    text.tag_config("int", foreground = "#00AAFF")
    text.tag_config("float", foreground = "#00AAFF")
    text.tag_config("char", foreground = "#00AAFF")
    text.tag_config("string", foreground = "#AA8800")

    sb = Scrollbar(root)
    sb.pack(fill = Y, expand = True)

    sb.config(command = text.yview)
    text.config(yscrollcommand = sb.set)

    for fn in [
        #"ADCElm.java",
        #"ACRailElm.java",
        #"RailElm.java",
        "VoltageElm.java",
    ]:
        FULL = join(ROOT_DIR, fn)
        with open(FULL, "r") as f:
            code = f.read()
        try:
            res = parser.parse(code, lexer = lexer, debug = False)
        except:
            lexer.lineno = 1
            parser.parse(code, lexer = lexer, debug = True)
            res = None

        for t in iter_tokens(res):
            if t.prefix:
                content = ""
                for c in t.prefix:
                    if c == " ":
                        content += u"\u00B7"
                    elif c == "\t":
                        content += u"\u00BB   "
                    else:
                        content += c

                text.insert(END, content, "ignored")

            tags = []
            try:
                tags.append(t.tag)
            except AttributeError:
                pass

            text.insert(END, t.value, *tags)

        text.insert(END, "\n\n")

    root.mainloop()
