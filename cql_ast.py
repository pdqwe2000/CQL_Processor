class Node:
    """Classe base para todos os nós da AST"""
    pass

class SelectStatement(Node):
    def __init__(self, fields, table_name, where_conditions=None, limit=None):
        """
        Representa um comando SELECT
        :param fields: Lista de campos a selecionar (ou '*' para todos)
        :param table_name: Nome da tabela
        :param where_conditions: Lista de condições WHERE
        :param limit: Número máximo de resultados
        """
        self.fields = fields
        self.table_name = table_name
        self.where_conditions = where_conditions or []
        self.limit = limit

    def execute(self, tables):
        """Executa a consulta na tabela especificada"""
        if self.table_name not in tables:
            raise ValueError(f"Tabela '{self.table_name}' não encontrada")
        
        table = tables[self.table_name]
        headers = table['headers']
        data = table['data']
        
        # Filtragem
        filtered_data = []
        for row in data:
            if self._matches_conditions(row, headers):
                filtered_data.append(row)
        
        # Limite
        if self.limit is not None:
            filtered_data = filtered_data[:self.limit]
        
        # Projeção
        if self.fields == ['*']:
            return {'headers': headers, 'data': filtered_data}
        else:
            indices = [headers.index(f) for f in self.fields]
            return {
                'headers': self.fields,
                'data': [[row[i] for i in indices] for row in filtered_data]
            }

    def _matches_conditions(self, row, headers):
        """Avalia se a linha satisfaz todas as condições WHERE"""
        for cond in self.where_conditions:
            if not self._eval_condition(row, headers, cond):
                return False
        return True

    def _eval_condition(self, row, headers, condition):
        """Avalia uma única condição"""
        # Implementação da avaliação de condições
        pass

class ImportStatement(Node):
    def __init__(self, table_name, filename):
        self.table_name = table_name
        self.filename = filename

    def execute(self, tables):
        """Executa o comando IMPORT"""
        # Implementação da importação
        pass

class ExportStatement(Node):
    def __init__(self, table_name, filename):
        self.table_name = table_name
        self.filename = filename

    def execute(self, tables):
        """Executa o comando EXPORT"""
        # Implementação da exportação
        pass

# Outras classes de comandos...
class CreateTableSelect(Node):
    pass

class JoinStatement(Node):
    pass

class ProcedureDefinition(Node):
    pass