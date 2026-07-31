import sqlite3 as sql


class GerenciadorBancoETL:
    """Classe responsável por criar e gerir a base de dados do projeto de consolidação (ETL)."""
    def __init__(self, nome_banco: str ="central_consolidada.db"):
        self.nome_banco = nome_banco
        self.inicializar_banco()

    def conectar(self):
        """Método auxiliar para abrir a conexão com a base de dados SQLite."""
        return sql.connect(self.nome_banco)

    def inicializar_banco(self):
        """Cria as tabelas necessárias para o fluxo de ETL se elas não existirem."""
        with self.conectar() as conn:
            cursor = conn.cursor()

            # Ativar suporte a Chaves Estrangeiras (Foreign Keys) no SQLite
            cursor.execute("PRAGMA foreign_keys = ON;")

            # TABELA 1: Histórico de Importações (Metadados do ETL)
            # Guarda informações de auditoria sobre quais ficheiros foram carregados e quando.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS importacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_ficheiro TEXT NOT NULL,
                    data_importacao TEXT NOT NULL,
                    linhas_processadas INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
            """)

            # TABELA 2: Dados Consolidados de Vendas
            # Guarda os registros limpos e consolidados extraídos das planilhas.
            # Possui uma chave estrangeira ligada à tabela de importações.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendas_consolidadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_venda TEXT NOT NULL,
                    cliente TEXT NOT NULL,
                    produto TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    valor_unitario REAL NOT NULL,
                    valor_total REAL NOT NULL,
                    importacao_id INTEGER,
                    FOREIGN KEY (importacao_id) REFERENCES importacoes(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
            print("[Sucesso] Base de dados e tabelas inicializadas corretamente.")


if __name__ == "__main__":
    # Executa a inicialização ao rodar o script diretamente
    gerenciador = GerenciadorBancoETL()
