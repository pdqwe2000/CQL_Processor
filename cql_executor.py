from cql_ast import *
from cql_database import *

def execute_ast(ast_node, tables):
    """Executa um nó da AST e retorna o resultado"""
    return ast_node.execute(tables)