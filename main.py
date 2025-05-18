import ply.lex as lex
import ply.yacc as yacc
import csv
import sys
import os
import re
import traceback

from collections import defaultdict

# ==============================================
# Lexic
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

def t_COMMENT_SINGLELINE(t):
    r'\-\-.*'
    pass  

def t_COMMENT_MULTILINE(t):
    r'\{\-[\s\S]*?\-\}'
    pass  

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Constructor
lexer = lex.lex()

# ==============================================
# SINTATIC
# ==============================================

# Data Structures For Memory
tables = {}
procedures = {}

def p_program(p):
    '''program : statement
               | program statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_statements(p):
    '''statements : statement SEMICOLON
                 | statements statement SEMICOLON'''
    if len(p) == 3:  # statement SEMICOLON
        p[0] = [p[1]] if p[1] is not None else []
    else:  # statements statement SEMICOLON
        p[0] = p[1] + ([p[2]] if p[2] is not None else [])

def p_statement(p):
    '''statement : import_stmt SEMICOLON
                | export_stmt SEMICOLON
                | discard_stmt SEMICOLON
                | rename_stmt SEMICOLON
                | print_stmt SEMICOLON
                | select_stmt SEMICOLON
                | create_select_stmt SEMICOLON
                | create_join_stmt SEMICOLON
                | procedure_decl SEMICOLON
                | procedure_call SEMICOLON'''
    p[0] = p[1]


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
    
    p[0] = {'type': 'import_stmt', 'table': table_name, 'file': filename}

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
        
    p[0] = {'type': 'export_stmt', 'table': table_name, 'file': filename}

# DISCARD TABLE
def p_discard_stmt(p):
    'discard_stmt : DISCARD TABLE IDENTIFIER'
    table_name = p[3]
    if table_name in tables:
        del tables[table_name]
        print(f"Tabela '{table_name}' descartada")
    else:
        print(f"Erro: Tabela '{table_name}' não encontrada")
        
    p[0] = {'type': 'discard_stmt', 'table': table_name}

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
        
    p[0] = {'type': 'rename_stmt', 'old_table': old_name, 'new_table': new_name}

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
    
    p[0] = {'type': 'print_stmt', 'table': table_name}

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

    # Verifica se os campos existem
    if fields == ['*']:
        selected_indices = list(range(len(headers)))
        selected_headers = headers
    else:
        selected_indices = []
        selected_headers = []
        for field in fields:
            if field not in headers:
                print(f"Erro: Campo '{field}' não encontrado na tabela '{table_name}'")
                return
            idx = headers.index(field)
            selected_indices.append(idx)
            selected_headers.append(field)

    # Aplica cláusula WHERE
    filtered_data = []
    for row in data:
        if not conditions or evaluate_conditions(row, headers, conditions):
            filtered_data.append([row[i] for i in selected_indices])

    # Aplica cláusula LIMIT
    if limit is not None:
        filtered_data = filtered_data[:limit]

    # Imprime o resultado
    print("\n" + " | ".join(selected_headers))
    print("-" * (sum(len(h) for h in selected_headers) + 3 * (len(selected_headers) - 1)))
    for row in filtered_data:
        print(" | ".join(str(cell) for cell in row))
    print()
    # Retorna resultado
    p[0] = {
        'type': 'select_stmt',
        'fields': fields,
        'table': table_name,
        'conditions': conditions,
        'limit': limit,
        'result': {
            'headers': selected_headers,
            'data': filtered_data
        }
    }


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
    table_name = p[3]
    select_result = p[4]['result']  # Resultado da consulta SELECT
    
    if not isinstance(select_result, dict) or 'headers' not in select_result or 'data' not in select_result:
        print("Erro: Resultado da consulta SELECT inválido")
        return
    
    if table_name in tables:
        print(f"Aviso: Substituindo tabela existente '{table_name}'")
    
    tables[table_name] = {
        'headers': select_result['headers'],
        'data': select_result['data']
    }
    print(f"Tabela '{table_name}' criada com sucesso com {len(select_result['data'])} registros")
    
    p[0] = {'type': 'create_select_stmt', 'table': table_name, 'select': p[4]}

def p_create_join_stmt(p):
    'create_join_stmt : CREATE TABLE IDENTIFIER FROM IDENTIFIER JOIN IDENTIFIER USING LPAREN IDENTIFIER RPAREN'
    new_table = p[3]       # Nome da nova tabela
    left_table = p[5]      # Primeira tabela a unir
    right_table = p[7]     # Segunda tabela a unir
    join_column = p[10]     # Coluna para o JOIN
    
    # Verificar se as tabelas existem
    if left_table not in tables:
        print(f"Erro: Tabela '{left_table}' não encontrada")
        return
        
    if right_table not in tables:
        print(f"Erro: Tabela '{right_table}' não encontrada")
        return
    
    left_data = tables[left_table]
    right_data = tables[right_table]
    
    # Verificar se a coluna de junção existe em ambas as tabelas
    if join_column not in left_data['headers']:
        print(f"Erro: Coluna '{join_column}' não encontrada em '{left_table}'")
        return
        
    if join_column not in right_data['headers']:
        print(f"Erro: Coluna '{join_column}' não encontrada em '{right_table}'")
        return
    
    # Obter índices das colunas de junção
    left_idx = left_data['headers'].index(join_column)
    right_idx = right_data['headers'].index(join_column)
    
    # Criar dicionário para lookup da tabela direita
    right_lookup = {}
    for row in right_data['data']:
        key = row[right_idx]
        if key not in right_lookup:
            right_lookup[key] = []
        right_lookup[key].append(row)
    
    # Realizar o JOIN
    joined_data = []
    for left_row in left_data['data']:
        join_key = left_row[left_idx]
        if join_key in right_lookup:
            for right_row in right_lookup[join_key]:
                # Combinar as linhas (excluindo a coluna de junção duplicada)
                combined_row = left_row + right_row[:right_idx] + right_row[right_idx+1:]
                joined_data.append(combined_row)
    
    # Combinar os cabeçalhos (excluindo a coluna de junção duplicada)
    combined_headers = left_data['headers'] + [
        h for h in right_data['headers'] if h != join_column
    ]
    
    # Armazenar a nova tabela
    tables[new_table] = {
        'headers': combined_headers,
        'data': joined_data
    }
    
    print(f"Tabela '{new_table}' criada com sucesso a partir do JOIN entre '{left_table}' e '{right_table}'")
    print(f"Total de registros: {len(joined_data)}")
    print(f"Colunas: {', '.join(combined_headers)}")
    
    p[0] = {
        'type': 'create_join_stmt', 
        'new_table': new_table, 
        'left_table': left_table, 
        'right_table': right_table, 
        'join_column': join_column
    }

# PROCEDURE
def p_procedure_decl(p):
    '''procedure_decl : PROCEDURE IDENTIFIER DO statements END'''
    procedure_name = p[2]
    statements_text = []
    mydict={procedure_name:p[4]}
    print(mydict)
    # Extract the text of each statement from the statements list
    for stmt in p[4]:
        # Find the statement text in the source code if possible
        # Otherwise just save the statement type for execution
        if isinstance(stmt, dict) and 'type' in stmt:
            statements_text.append(stmt)
    
    # Store procedure as a list of commands to execute
    procedures[procedure_name] = statements_text
    
    print(f"Procedimento '{procedure_name}' definido com {len(statements_text)} instruções")
    
    p[0] = {'type': 'procedure_decl', 'name': procedure_name}

# CALL PROCEDURE
def p_procedure_call(p):
    'procedure_call : CALL IDENTIFIER'
    procedure_name = p[2]
    
    if procedure_name in procedures:
        print(f"\nExecutando procedimento '{procedure_name}':")
        procedure_statements = procedures[procedure_name]
        
        for i, stmt in enumerate(procedure_statements):
            try:
                if isinstance(stmt, dict) and 'type' in stmt:
                    # For clarity in debug output
                    stmt_type = stmt['type']
                    print(f">> Executando instrução {i+1}: {stmt_type}")
                    
                    # Execute different statement types
                    if stmt_type == 'create_select_stmt':
                        # For CREATE TABLE ... SELECT
                        table_name = stmt['table']
                        select_result = stmt['select']['result']
                        tables[table_name] = {
                            'headers': select_result['headers'],
                            'data': select_result['data']
                        }
                        print(f"Tabela '{table_name}' criada com sucesso com {len(select_result['data'])} registros")
                    
                    elif stmt_type == 'create_join_stmt':
                        # For CREATE TABLE ... FROM ... JOIN
                        execute_join(stmt['new_table'], stmt['left_table'], stmt['right_table'], stmt['join_column'])
                    
                    # Add handlers for other statement types as needed
                    elif stmt_type == 'select_stmt':
                        # Executar SELECT (já imprime o resultado)
                        pass
                    
                    elif stmt_type == 'print_stmt':
                        # Imprimir tabela
                        table_name = stmt['table']
                        if table_name in tables:
                            table = tables[table_name]
                            print("\n" + " | ".join(table['headers']))
                            print("-" * (sum(len(h) for h in table['headers']) + 3 * (len(table['headers']) - 1)))
                            for row in table['data']:
                                print(" | ".join(str(x) for x in row))
                            print()
                        else:
                            print(f"Erro: Tabela '{table_name}' não encontrada")
                            
                    # Add other statement types as needed
                    
                else:
                    print(f">> Aviso: Instrução {i+1} não pode ser executada (formato inválido)")
            except Exception as e:
                print(f"Erro na execução da instrução {i+1}: {str(e)}")
                traceback.print_exc()
        
        print(f"Procedimento '{procedure_name}' concluído\n")
    else:
        print(f"Erro: Procedimento '{procedure_name}' não encontrado")
    
    p[0] = {'type': 'procedure_call', 'name': procedure_name}

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p:
        print(f"Erro de sintaxe na linha {p.lineno}, token '{p.value}' (tipo: {p.type})")
        # Recuperação de erro: descarta tokens até encontrar um ponto-e-vírgula
        parser.errok()
        parser.token()  # Descarta o token problemático
    else:
        print("Erro de sintaxe: comando incompleto ou inválido")

# ==============================================
# Auxiliary Functions
# ==============================================

def execute_join(new_table, left_table, right_table, join_column):
    """Helper function to execute a JOIN operation"""
    # Verificar se as tabelas existem
    if left_table not in tables:
        print(f"Erro: Tabela '{left_table}' não encontrada")
        return
        
    if right_table not in tables:
        print(f"Erro: Tabela '{right_table}' não encontrada")
        return
    
    left_data = tables[left_table]
    right_data = tables[right_table]
    
    # Verificar se a coluna de junção existe em ambas as tabelas
    if join_column not in left_data['headers']:
        print(f"Erro: Coluna '{join_column}' não encontrada em '{left_table}'")
        return
        
    if join_column not in right_data['headers']:
        print(f"Erro: Coluna '{join_column}' não encontrada em '{right_table}'")
        return
    
    # Obter índices das colunas de junção
    left_idx = left_data['headers'].index(join_column)
    right_idx = right_data['headers'].index(join_column)
    
    # Criar dicionário para lookup da tabela direita
    right_lookup = {}
    for row in right_data['data']:
        key = row[right_idx]
        if key not in right_lookup:
            right_lookup[key] = []
        right_lookup[key].append(row)
    
    # Realizar o JOIN
    joined_data = []
    for left_row in left_data['data']:
        join_key = left_row[left_idx]
        if join_key in right_lookup:
            for right_row in right_lookup[join_key]:
                # Combinar as linhas (excluindo a coluna de junção duplicada)
                combined_row = left_row + right_row[:right_idx] + right_row[right_idx+1:]
                joined_data.append(combined_row)
    
    # Combinar os cabeçalhos (excluindo a coluna de junção duplicada)
    combined_headers = left_data['headers'] + [
        h for h in right_data['headers'] if h != join_column
    ]
    
    # Armazenar a nova tabela
    tables[new_table] = {
        'headers': combined_headers,
        'data': joined_data
    }
    
    print(f"Tabela '{new_table}' criada com sucesso a partir do JOIN entre '{left_table}' e '{right_table}'")
    print(f"Total de registros: {len(joined_data)}")
    print(f"Colunas: {', '.join(combined_headers)}")

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

# Construction of parser
parser = yacc.yacc()

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
                parser.source_code = content  # Store the source code for procedure extraction
                commands = [cmd.strip() for cmd in content.split(';') if cmd.strip()]
                for cmd in commands:
                    parser.parse(cmd + ';')
        except Exception as e:
            print("Erro ao ler o ficheiro:")
            traceback.print_exc()
    else:
        print("Modo interativo. Escreva 'sair' para encerrar o programa.")
        parser.source_code = ""  # Initialize source code buffer for interactive mode
        while True:
            try:
                text = input('CQL> ')
                if text.lower() == 'sair':
                    break
                parser.source_code += text + "\n"  # Append to source buffer
                commands = [cmd.strip() for cmd in text.split(';') if cmd.strip()]
                for cmd in commands:
                    parser.parse(cmd + ';')
            except EOFError:
                break
            except Exception as e:
                print(f"Erro: {e}")
                traceback.print_exc()


if __name__ == '__main__':
    main()