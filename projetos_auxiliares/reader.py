import sqlite3 as sql
import csv 
from datetime import datetime as dt
from database import GerenciadorBancoETL as gerente
import re

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
    
        # Garantia 1: Se dados_brutos for None ou vazio, já retorna a lista vazia imediatamente
        if not dados_brutos:
            return dados_limpos

        for index, linha_original in enumerate(dados_brutos):
            print(f"--- LINHA BRUTA {index}: {linha_original}")
            try:
                # 1. Padronização estrita de chaves (ignora chaves nulas ou vazias)
                linha = {
                    str(k).lower().strip(): v 
                    for k, v in linha_original.items() 
                    if k and str(k).strip()
                }
            
                # 2. Validação Adaptativa do Produto (Obrigatório)
                produto = linha.get('produto')
                if not produto or not str(produto).strip():
                    continue
                
                # Validação Adaptativa do Cliente
                cliente = linha.get('cliente') or linha.get('canal_venda') or 'Geral'
                
                # 3. Limpeza Agressiva de Quantidade (Extrai apenas números)
                qtd_bruta = str(linha.get('quantidade', '0')).strip()
                qtd_numerica = re.sub(r'\D', '', qtd_bruta) 
                quantidade = int(qtd_numerica) if qtd_numerica else 0

                # 4. Tratamento Avançado de Valores Monetários
                def limpar_float(valor_bruto: str | None) -> float:
                    if not valor_bruto:
                        return 0.0
                    v_str = str(valor_bruto).replace("R$", "").replace("$", "").replace("\xa0", "").strip()
                    if not v_str:
                        return 0.0
                    
                    if "," in v_str and "." in v_str:
                        if v_str.find('.') < v_str.find(','):
                            v_str = v_str.replace(".", "").replace(",", ".")
                        else:
                            v_str = v_str.replace(",", "")
                    elif "," in v_str:
                        v_str = v_str.replace(",", ".")
                    
                    try:
                        return float(v_str)
                    except ValueError:
                        return 0.0

                valor_unitario = limpar_float(linha.get('valor_unitario') or linha.get('valor_unitário'))
                valor_total = limpar_float(linha.get('valor_total'))
                
                # 5. Regra Adaptativa de Integridade Financeira
                if valor_unitario > 0 and valor_total == 0:
                    valor_total = quantidade * valor_unitario
                elif valor_total > 0 and valor_unitario == 0 and quantidade > 0:
                    valor_unitario = round(valor_total / quantidade, 2)
                elif valor_unitario > 0 and valor_total > 0:
                    valor_total = quantidade * valor_unitario

                # 6. Motor de parsing de data tolerante a falhas
                data_limpa = str(linha.get('data') or linha.get('data_venda')).strip()
                data_limpa = data_limpa.replace("/", "-")
                
                data_formatada = None
                for formato in ("%Y-%m-%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%y"):
                    try:
                        data_formatada = dt.strptime(data_limpa, formato)
                        break
                    except ValueError:
                        continue
                
                if not data_formatada:
                    raise ValueError(f"Formato de data inválido: {data_limpa}")

                # 7. Construção do registro higienizado
                dados_limpos.append({
                    'data_venda': data_formatada.strftime("%Y-%m-%d"),
                    'cliente': str(cliente).strip().title(),
                    'produto': str(produto).strip(),
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario,
                    'valor_total': valor_total
                })
                
            except Exception as e:
                print(f"Linha {index} descartada por inconsistência crítica: {e}")
                continue

        # Garantia 2: O return fica no escopo principal da função, garantindo a entrega da lista
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
            

