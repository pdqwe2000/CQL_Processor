import ply.lex as lex

tokens = (
    'SELECT', 'FROM', 'WHERE', 'CREATE', 'TABLE', 'IMPORT', 'EXPORT', 
    'DISCARD', 'RENAME', 'PRINT', 'JOIN', 'USING', 'PROCEDURE', 'DO', 
    'END', 'CALL', 'AND', 'LIMIT', 'AS', 'IDENTIFIER', 'STRING', 'NUMBER',
    'GREATER', 'LESS', 'GREATER_EQ', 'LESS_EQ', 'EQUALS', 'NOT_EQUALS',
    'COMMA', 'SEMICOLON', 'LPAREN', 'RPAREN','STAR'
)


# Reserved words
reserved = {
    'select': 'SELECT',
    'from': 'FROM',
    'where': 'WHERE',
    'create': 'CREATE',
    'table': 'TABLE',
    'import': 'IMPORT',
    'export': 'EXPORT',
    'discard': 'DISCARD',
    'rename': 'RENAME',
    'print': 'PRINT',
    'join': 'JOIN',
    'using': 'USING',
    'procedure': 'PROCEDURE',
    'do': 'DO',
    'end': 'END',
    'call': 'CALL',
    'and': 'AND',
    'limit': 'LIMIT',
    'as': 'AS'
}

# Operators
t_GREATER = r'>'
t_LESS = r'<'
t_GREATER_EQ = r'>='
t_LESS_EQ = r'<='
t_EQUALS = r'='
t_NOT_EQUALS = r'<>'
t_COMMA = r','
t_SEMICOLON = r';'
t_LPAREN = r'\('
t_RPAREN = r'\)'

# Ignores spaces and tabs
t_ignore = ' \t'

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'IDENTIFIER')
    return t

def t_STAR(t):
    r'\*'
    return t

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"|\'([^\\\n]|(\\.))*?\''
    t.value = t.value[1:-1]  # Remove ""
    return t

def t_NUMBER(t):
    r'\d+\.?\d*'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Lexer Constructor
lexer = lex.lex()