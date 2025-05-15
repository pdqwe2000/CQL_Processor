def generate_c_code(ast_node):
    """Gera código C equivalente para o comando"""
    # Implementação básica para SELECT
    if isinstance(ast_node, SelectStatement):
        print("// Código C equivalente:")
        print(f"void query() {{")
        print(f"    // SELECT {', '.join(ast_node.fields)}")
        print(f"    // FROM {ast_node.table_name}")
        if ast_node.where_conditions:
            print("    // WHERE ...")
        print("}")