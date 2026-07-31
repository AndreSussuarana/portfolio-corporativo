import sqlite3 as sql
import csv 
from datetime import datetime as dt
from database import GerenciadorBancoETL as gerente

class ProcessadorETL:
    """Classe responsável por extrair, transformar e carregar os dados das planilhas."""

    def __init__(self, gerenciador_db: gerente):
        # Injeção de dependência: passamos o gestor do banco para o processador
        self.db = gerenciador_db

    def extrair_dados_csv(self, caminho_arquivo: str) -> list[dict[str, str]]: 
        """Extrai os dados brutos de um arquivo CSV."""
        registros: list[dict[str, str]] = []
        try:
            with open(caminho_arquivo, mode='r', encoding='utf-8') as arquivo:
                leitor = csv.DictReader(arquivo)
                for linha in leitor:
                    registros.append(linha)
            return registros
        except Exception as e:
            raise Exception(f"Erro ao ler arquivo: {str(e)}")
        
    def transformar_dados(self, dados_brutos: list[dict[str, str]]) -> list[dict[str, str | int | float]]:
        """Limpa, valida e formata os dados de acordo com as regras de negócio."""
        dados_limpos: list[dict[str, str | int | float]] = []

        for index, linha in enumerate(dados_brutos):
            try:
                # Regra de Negócio 1: Validação de campos obrigatórios
                if not linha.get('cliente') or not linha.get('produto'):
                    continue
                
                # Regra de Negócio 2: Conversão e tratamento de tipos
                qtd_bruta = linha.get('quantidade', '0').strip()
                quantidade = int(qtd_bruta) if qtd_bruta else 0

                # Captura o que vier na planilha (tratando chaves ausentes)
                v_unitario_bruto = linha.get('valor_unitario')
                v_total_bruto = linha.get('valor_total')

                valor_unitario = 0.0
                valor_total = 0.0

                # Converte os valores se eles existirem na planilha
             # Converte os valores tratando de forma inteligente pontos e vírgulas
                if v_unitario_bruto and str(v_unitario_bruto).strip():
                    v_u_str = str(v_unitario_bruto).replace("R$", "").strip()
                    # Se tiver vírgula e ponto (ex: 1.500,50), remove o ponto e troca a vírgula por ponto
                    if "," in v_u_str and "." in v_u_str:
                        v_u_str = v_u_str.replace(".", "").replace(",", ".")
                    # Se só tiver vírgula (ex: 150,50), vira ponto
                    elif "," in v_u_str:
                        v_u_str = v_u_str.replace(",", ".")
                    valor_unitario = float(v_u_str)

                if v_total_bruto and str(v_total_bruto).strip():
                    v_t_str = str(v_total_bruto).replace("R$", "").strip()
                    if "," in v_t_str and "." in v_t_str:
                        v_t_str = v_t_str.replace(".", "").replace(",", ".")
                    elif "," in v_t_str:
                        v_t_str = v_t_str.replace(",", ".")
                    valor_total = float(v_t_str)
                                # --- REGRA ADAPTATIVA DE INTEGRIDADE ---
                # Caso 1: Tem quantidade e unitário, mas não tem o total
                if valor_unitario > 0 and valor_total == 0:
                    valor_total = quantidade * valor_unitario
                
                # Caso 2: Tem quantidade e total, mas falta o unitário (O caso do seu teste!)
                elif valor_total > 0 and valor_unitario == 0 and quantidade > 0:
                    valor_unitario = round(valor_total / quantidade, 2)
                
                # Caso 3: Recalcula por garantia se ambos existirem para evitar fraudes/erros manuais
                elif valor_unitario > 0 and valor_total > 0:
                    valor_total = quantidade * valor_unitario

                # Regra de Negócio 4: Padronização de datas (padrão ISO)
                data_limpa = str(linha['data_venda']).strip()
                data_formatada = dt.strptime(data_limpa, "%Y-%m-%d")

                dados_limpos.append({
                    'data_venda': data_formatada.strftime("%Y-%m-%d"),
                    'cliente': linha['cliente'].strip().title(),
                    'produto': linha['produto'].strip(),
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario,
                    'valor_total': valor_total
                })
            except (ValueError, TypeError) as e:
                print(f"Linha {index} descartada por inconsistência de dados: {e}")
                continue

        return dados_limpos
    
    def carregar_no_banco(self, nome_arquivo: str, dados_transformados: list[dict[str, str | int | float]]) -> bool:
        """Insere os dados limpos e o histórico de importação no SQLite."""
        if not dados_transformados:
            return False
        
        with self.db.conectar() as conn:
            cursor = conn.cursor()
            try:
                # 1. Registra a importação na tabela de metadados
                data_atual = dt.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO importacoes (nome_ficheiro, data_importacao, linhas_processadas, status)
                    VALUES (?, ?, ?, ?)
                """, (nome_arquivo, data_atual, len(dados_transformados), "CONCLUÍDO"))

                importacao_id = cursor.lastrowid

                vendas_tuplas = [(
                        d['data_venda'], 
                        d['cliente'], 
                        d['produto'], 
                        d['quantidade'], 
                        d['valor_unitario'], 
                        d['valor_total'], 
                        importacao_id
                    ) 
                    for d in dados_transformados
                    ]
                cursor.executemany("""
                    INSERT INTO vendas_consolidadas 
                    (data_venda, cliente, produto, quantidade, valor_unitario, valor_total, importacao_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, vendas_tuplas)

                conn.commit()
                return True
            except sql.Error as e:
                conn.rollback()
                raise Exception(f"Erro ao persistir no banco de dados: {str(e)}")
            

