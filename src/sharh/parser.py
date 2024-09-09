import re
from sharh.expr import Literal, Conjunction, Disjunction


class ParseError(Exception):
    pass

class ExpressionTree:
    def __init__(self, custom_literal_classes=None):
        self.tree = []
        self.stack = []
        self.expressions = {}
        self.custom_literal_classes = custom_literal_classes or {}

        self.original_expr_was_dnf = True

    def push(self, expr_args):
        LiteralClass = Literal
        if self.custom_literal_classes.get(expr_args[0]):
            LiteralClass = self.custom_literal_classes[expr_args[0]]

        self.stack.append(LiteralClass(*expr_args))

    def commit(self, operator):
        right = self.stack.pop()
        left = self.stack.pop()

        if re.match(t_AND, operator):
            if (
                (isinstance(left, Literal) or isinstance(left, Conjunction))
                and isinstance(right, Disjunction)
            ) or (
                (isinstance(right, Literal) or isinstance(right, Conjunction))
                and isinstance(left, Disjunction)
            ):
                self.original_expr_was_dnf = False

            self.stack.append(left * right)
        elif re.match(t_OR, operator):
            self.stack.append(left + right)


tree = ExpressionTree()


tokens = (
    "IDENTIFIER_STR",
    "VALUE_STR",
    "VALUE_LIST_STR",
    "IDENTIFIER_LIST",
    "IDENTIFIER_IP",
    "VALUE_IP",
    "VALUE_LIST_IP_CIDR",
    "IDENTIFIER_NUM",
    "VALUE_NUM",
    "VALUE_LIST_NUM",
    "IDENTIFIER_BOOL",
    "VALUE_BOOL",
    "EQ",
    "NEQ",
    "GE",
    "LE",
    "IN",
    "NOT_IN",
    "HAS",
    "NOT_HAS",
    "CONTAINS",
    "NOT_CONTAINS",
    "AND",
    "OR",
    "LPAREN",
    "RPAREN",
)

IP_OR_CIDR_PATTERN = (
    r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}(\/([1-9]|[1-2]\d|3[0-2]))?"
)

t_IDENTIFIER_STR = (
    r"ip.geoip.country|ip.geoip.continent|"
    r"http.method|http.version|http.headers.user_agent|http.headers.x_forwarded_for|http.headers.referer|"
    r"http.headers\['[a-zA-Z0-9\-\_]+'\]|"
    r"device"
)
t_VALUE_STR = r"'[a-zA-Z0-9\/\-\.:\s]+'"
t_VALUE_LIST_STR = rf"\[\s*({t_VALUE_STR}\s*,\s*)*{t_VALUE_STR}\s*\]"
t_IDENTIFIER_LIST = r"http.headers"
t_IDENTIFIER_IP = "ip.addr"
t_VALUE_IP = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"
t_VALUE_LIST_IP_CIDR = rf"\[\s*({IP_OR_CIDR_PATTERN}\s*,\s*)*{IP_OR_CIDR_PATTERN}\s*\]"
t_IDENTIFIER_NUM = r"ip.geoip.asn|ip.reputation"
t_VALUE_NUM = "[0-9]{1,11}"
t_VALUE_LIST_NUM = rf"\[\s*({t_VALUE_NUM}\s*,\s*)*{t_VALUE_NUM}\s*\]"
t_IDENTIFIER_BOOL = r"http.secure"
t_VALUE_BOOL = r"(true)|(false)"
t_EQ = r"=="
t_NEQ = r"!="
t_GE = r">="
t_LE = r"<="
t_IN = r"in"
t_NOT_IN = r"!in"
t_HAS = r"has"
t_NOT_HAS = r"!has"
t_CONTAINS = r"contains"
t_NOT_CONTAINS = r"!contains"
t_AND = r"(and)|(AND)"
t_OR = r"(or)|(OR)"
t_LPAREN = r"\("
t_RPAREN = r"\)"

# Ignored characters
t_ignore = " \t\n"

precedence = (
    ("left", "OR"),
    ("left", "AND"),
)


def t_error(t):
    t.lexer.skip(1)


import ply.lex as lex

lexer = lex.lex()


def p_error(t):
    raise ParseError()


def p_expression_unit(t):
    """expression : IDENTIFIER_STR EQ VALUE_STR
    | IDENTIFIER_STR NEQ VALUE_STR
    | IDENTIFIER_STR CONTAINS VALUE_STR
    | IDENTIFIER_STR NOT_CONTAINS VALUE_STR
    | IDENTIFIER_STR IN VALUE_LIST_STR
    | IDENTIFIER_STR NOT_IN VALUE_LIST_STR
    | IDENTIFIER_LIST HAS VALUE_STR
    | IDENTIFIER_LIST NOT_HAS VALUE_STR
    | IDENTIFIER_IP EQ VALUE_IP
    | IDENTIFIER_IP NEQ VALUE_IP
    | IDENTIFIER_IP IN VALUE_LIST_IP_CIDR
    | IDENTIFIER_IP NOT_IN VALUE_LIST_IP_CIDR
    | IDENTIFIER_NUM EQ VALUE_NUM
    | IDENTIFIER_NUM NEQ VALUE_NUM
    | IDENTIFIER_NUM GE VALUE_NUM
    | IDENTIFIER_NUM LE VALUE_NUM
    | IDENTIFIER_NUM IN VALUE_LIST_NUM
    | IDENTIFIER_NUM NOT_IN VALUE_LIST_NUM
    | IDENTIFIER_BOOL EQ VALUE_BOOL"""

    identifier = t[1]
    operation = t[2]
    value = t[3]

    if re.match(t_VALUE_STR, value):
        value = value[1:-1]
    elif re.match(t_VALUE_BOOL, value):
        value = True if value == "true" else False

    try:
        tree.push([identifier, operation, value])
    except ValueError as e:
        raise ParseError(*e.args)
    t[0] = [[t[1], t[2], t[3]]]


def p_expression_binop(t):
    """expression : expression AND expression
    | expression OR expression"""

    tree.commit(t[2])


def p_expression_group(t):
    "expression : LPAREN expression RPAREN"
    t[0] = t[2]


import ply.yacc as yacc

parser = yacc.yacc()


def parse(s, custom_literal_classes = None):
    if not s.strip():
        return Disjunction([])

    global tree
    tree = ExpressionTree(custom_literal_classes)
    parser.parse(s)

    if custom_literal_classes is not None:
        global CUSTOM_LITERAL_CLASSES
        CUSTOM_LITERAL_CLASSES = custom_literal_classes

    try:
        parsed = tree.stack.pop()
    except IndexError:
        raise ParseError()

    if isinstance(parsed, Literal):
        parsed = Conjunction([parsed])
    if isinstance(parsed, Conjunction):
        parsed = Disjunction([parsed])

    parsed.original_expr_was_dnf = tree.original_expr_was_dnf

    return parsed
