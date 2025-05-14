tables = {}


# IMPORT TABLE
def p_import_stmt(p):
    'import_stmt : IMPORT TABLE IDENTIFIER FROM STRING'
    filename = p[5]
    table_name = p[3]
    
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = [row for row in reader if not row[0].startswith('#')]
            
            # Processing text in ""
            processed_data = []
            for row in data:
                processed_row = []
                for field in row:
                    if field.startswith('"') and field.endswith('"'):
                        processed_row.append(field[1:-1])
                    else:
                        processed_row.append(field)
                processed_data.append(processed_row)
            
            tables[table_name] = {'headers': headers, 'data': processed_data}
            print(f"Tabela '{table_name}' importada com sucesso de '{filename}'")
    except Exception as e:
        print(f"Erro ao importar tabela: {e}")

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
            writer = csv.writer(f)
            writer.writerow(tables[table_name]['headers'])
            writer.writerows(tables[table_name]['data'])
        print(f"Tabela '{table_name}' exportada com sucesso para '{filename}'")
    except Exception as e:
        print(f"Erro ao exportar tabela: {e}")

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