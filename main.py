import ply.lex as lex
import ply.yacc as yacc
import csv
import sys
import os
import re
import traceback

from collections import defaultdict

# ==============================================
# Lexic Analizer
# ==============================================

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

def t_COMMENT_SINGLELINE(t):
    r'\-\-.*'
    pass  # Ignora completamente

def t_COMMENT_MULTILINE(t):
    r'\{\-[\s\S]*?\-\}'
    pass  # Ignora completamente

# Lexer Constructor
lexer = lex.lex()

# ==============================================
# SINTATIC Analizer
# ==============================================

# Data Structures For Memory
tables = {}
procedures = {}

def p_program(p):
    '''program : statement SEMICOLON
               | program statement SEMICOLON'''
    pass

def p_statement(p):
    '''statement : import_stmt
                | export_stmt
                | discard_stmt
                | rename_stmt
                | print_stmt
                | select_stmt
                | create_select_stmt
                | create_join_stmt
                | procedure_decl
                | procedure_call'''
    pass

# IMPORT TABLE
def p_import_stmt(p):
    'import_stmt : IMPORT TABLE IDENTIFIER FROM STRING'
    filename = p[5]
    table_name = p[3]
    
    try:
        with open(filename, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            num_columns = len(headers)

            valid_data = []
            line_number = 1  # header is line 1

            for row in reader:
                line_number += 1

                # Ignorar linhas comentadas
                if not row or row[0].strip().startswith('#'):
                    continue

                # Validação: número de colunas correto
                if len(row) != num_columns:
                    print(f"Aviso: Linha {line_number} ignorada - número de colunas inválido (esperado {num_columns}, obtido {len(row)})")
                    continue

                # Remover aspas de campos se necessário
                processed_row = [field.strip('"').strip("'") for field in row]
                valid_data.append(processed_row)

            # Armazenar na memória
            tables[table_name] = {
                'headers': headers,
                'data': valid_data
            }

            print(f"Tabela '{table_name}' importada com sucesso de '{filename}' ({len(valid_data)} linhas válidas)")
    
    except Exception as e:
        print(f"Erro ao importar tabela de '{filename}': {e}")

# EXPORT TABLE
def p_export_stmt(p):
    'export_stmt : EXPORT TABLE IDENTIFIER AS STRING'
    table_name = p[3]
    filename = p[5]
    
    if table_name not in tables:
        print(f"Erro: Tabela '{table_name}' não encontrada")
        return
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)

            table = tables[table_name]
            writer.writerow(table['headers'])
            for row in table['data']:
                writer.writerow(row)

        print(f"Tabela '{table_name}' exportada com sucesso para '{filename}'")
    
    except Exception as e:
        print(f"Erro ao exportar tabela para '{filename}': {e}")

# DISCARD TABLE
def p_discard_stmt(p):
    'discard_stmt : DISCARD TABLE IDENTIFIER'
    table_name = p[3]
    if table_name in tables:
        del tables[table_name]
        print(f"Tabela '{table_name}' descartada")
    else:
        print(f"Erro: Tabela '{table_name}' não encontrada")

# RENAME TABLE
def p_rename_stmt(p):
    'rename_stmt : RENAME TABLE IDENTIFIER IDENTIFIER'
    old_name = p[3]
    new_name = p[4]
    
    if old_name in tables:
        tables[new_name] = tables.pop(old_name)
        print(f"Tabela '{old_name}' renomeada para '{new_name}'")
    else:
        print(f"Erro: Tabela '{old_name}' não encontrada")

# PRINT TABLE
def p_print_stmt(p):
    'print_stmt : PRINT TABLE IDENTIFIER'
    table_name = p[3]
    
    if table_name not in tables:
        print(f"Erro: Tabela '{table_name}' não encontrada")
        return
    
    table = tables[table_name]
    print("\n" + " | ".join(table['headers']))
    print("-" * (sum(len(h) for h in table['headers']) + 3 * (len(table['headers']) - 1)))
    
    for row in table['data']:
        print(" | ".join(str(x) for x in row))
    print()

# SELECT
def p_select_stmt(p):
    '''select_stmt : SELECT select_fields FROM IDENTIFIER where_clause limit_clause'''
    fields = p[2]
    table_name = p[4]
    conditions = p[5]
    limit = p[6]
    
    if table_name not in tables:
        print(f"Erro: Tabela '{table_name}' não encontrada")
        return
    
    table = tables[table_name]
    headers = table['headers']
    data = table['data']
    
    # Index of the selected fields
    if fields == ['*']:
        selected_indices = list(range(len(headers)))
    else:
        selected_indices = []
        for field in fields:
            if field in headers:
                selected_indices.append(headers.index(field))
            else:
                print(f"Erro: Campo '{field}' não encontrado")
                return
    
    # Filter lines based on conditions
    filtered_data = []
    if conditions:
        for row in data:
            if evaluate_conditions(row, headers, conditions):
                filtered_data.append(row)
    else:
        filtered_data = data
    
    # Add Limit
    if limit is not None and limit < len(filtered_data):
        filtered_data = filtered_data[:limit]
    
    # Show Results
    selected_headers = [headers[i] for i in selected_indices]
    print("\n" + " | ".join(selected_headers))
    print("-" * (sum(len(h) for h in selected_headers) + 3 * (len(selected_headers) - 1)))
    
    for row in filtered_data:
        selected_row = [str(row[i]) for i in selected_indices]
        print(" | ".join(selected_row))
    print()

def p_select_fields(p):
    '''select_fields : STAR
                    | field_list'''
    if isinstance(p[1], str) and p[1] == '*':
        p[0] = ['*']
    else:
        p[0] = p[1]

def p_field_list(p):
    '''field_list : IDENTIFIER
                 | field_list COMMA IDENTIFIER'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_where_clause(p):
    '''where_clause : WHERE condition_list
                   | empty'''
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = p[2]

def p_condition_list(p):
    '''condition_list : condition
                     | condition_list AND condition'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_condition(p):
    '''condition : IDENTIFIER GREATER NUMBER
                 | IDENTIFIER LESS NUMBER
                 | IDENTIFIER GREATER_EQ NUMBER
                 | IDENTIFIER LESS_EQ NUMBER
                 | IDENTIFIER EQUALS value
                 | IDENTIFIER NOT_EQUALS value'''
    p[0] = {'field': p[1], 'op': p[2], 'value': p[3]}

def p_value(p):
    '''value : STRING
            | NUMBER'''
    p[0] = p[1]

def p_limit_clause(p):
    '''limit_clause : LIMIT NUMBER
                   | empty'''
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = p[2]

# CREATE TABLE FROM SELECT
def p_create_select_stmt(p):
    'create_select_stmt : CREATE TABLE IDENTIFIER select_stmt'
    # Implementação simplificada - na prática precisaria capturar o resultado do SELECT
    print("CREATE TABLE FROM SELECT ainda não implementado")

# CREATE TABLE FROM JOIN
def p_create_join_stmt(p):
    'create_join_stmt : CREATE TABLE IDENTIFIER FROM IDENTIFIER JOIN IDENTIFIER USING LPAREN IDENTIFIER RPAREN'
    # Implementação simplificada
    print("CREATE TABLE FROM JOIN ainda não implementado")

# PROCEDURE
def p_procedure_decl(p):
    'procedure_decl : PROCEDURE IDENTIFIER DO program END'
    procedures[p[2]] = p[4]
    print(f"Procedimento '{p[2]}' definido")

# CALL PROCEDURE
def p_procedure_call(p):
    'procedure_call : CALL IDENTIFIER'
    if p[2] in procedures:
        # Implementação simplificada - na prática precisaria executar as instruções
        print(f"Executando procedimento '{p[2]}'")
    else:
        print(f"Erro: Procedimento '{p[2]}' não encontrado")

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p:
        print(f"Erro de sintaxe em '{p.value}'")
    else:
        print("Erro de sintaxe no fim do comando")

# Construction of parser
parser = yacc.yacc()

# ==============================================
# Auxiliary Functions
# ==============================================

def evaluate_conditions(row, headers, conditions):
    for cond in conditions:
        field = cond['field']
        op = cond['op']
        value = cond['value']
        
        if field not in headers:
            return False
        
        idx = headers.index(field)
        cell_value = row[idx]
        
        # Try convert to number
        try:
            cell_num = float(cell_value)
            if isinstance(value, str):
                try:
                    value_num = float(value)
                except ValueError:
                    pass
                else:
                    value = value_num
        except ValueError:
            pass
        
        # Comparasion
        if op == '=':
            if str(cell_value) != str(value):
                return False
        elif op == '<>':
            if str(cell_value) == str(value):
                return False
        elif op == '>':
            if float(cell_value) <= float(value):
                return False
        elif op == '<':
            if float(cell_value) >= float(value):
                return False
        elif op == '>=':
            if float(cell_value) < float(value):
                return False
        elif op == '<=':
            if float(cell_value) > float(value):
                return False
    
    return True

# ==============================================
# UI
# ==============================================

def main():
    print("Interpretador CQL (Comma Query Language)")
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        
        if not filename.endswith('.fca'):
            print("Erro: O ficheiro deve ter extensão .fca")
            return
        
        if not os.path.exists(filename):
            print(f"Erro: Ficheiro '{filename}' não encontrado")
            return
        
        try:
            with open(filename, 'r') as f:
                content = f.read()
                commands = [cmd.strip() for cmd in content.split(';') if cmd.strip()]
                for cmd in commands:
                    parser.parse(cmd + ';')
        except Exception as e:
            print("Erro ao ler o ficheiro:")
            traceback.print_exc()
    else:
        print("Modo interativo. Digite 'sair' para encerrar.")
        while True:
            try:
                text = input('CQL> ')
                if text.lower() == 'sair':
                    break
                commands = [cmd.strip() for cmd in text.split(';') if cmd.strip()]
                for cmd in commands:
                    parser.parse(cmd + ';')
            except EOFError:
                break
            except Exception as e:
                print(f"Erro: {e}")


if __name__ == '__main__':
    main()
