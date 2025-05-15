from cql_parser import parser
from cql_lexer import lex
from cql_database import tables
from cql_codegen import generate_c_code  # Para a funcionalidade opcional de C

def execute_commands(text):
    while True:
        try:
            # Process multiple codes separated by ;
            commands = [command.strip() for command in text.split(';') if command.strip()]
            for command in commands:
                if command:
                    parser.parse(command + ';')
        except EOFError:
            break
        except Exception as e:
            print(f"Erro: {e}")

# def execute_commands(command):
#     ast = parser.parse(command + ';')  # Adiciona ; para comandos do terminal
#     result = ast.execute(tables)
    
#     # Exibe resultados no terminal
#     if result:
#         print_result(result)
    
#     # Opcional: Gera código C
#     if should_generate_c(command):
#         generate_c_code(ast)

def print_result(result):
    """Formata a saída de resultados no terminal"""
    if isinstance(result, dict):  # Resultados de SELECT
        headers = result['headers']
        data = result['data']
        
        print("\n" + " | ".join(headers))
        print("-" * (sum(len(h) for h in headers) + 3*(len(headers)-1)))
        
        for row in data:
            print(" | ".join(str(x) for x in row))
        print()
    else:  # Mensagens de outros comandos
        print(result)

def should_generate_c(command):
    """Lógica para determinar quando gerar código C"""
    # Implemente conforme necessário
    return False