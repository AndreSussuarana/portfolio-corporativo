import pandas as pd
from pandas import DataFrame

def processar_e_tipar_colunas(df: DataFrame) -> DataFrame:
    """
    Analisa as colunas de um DataFrame dinâmico e converte 
    automaticamente textos que contêm números para o tipo numérico correto.
    """
    df_copia = df.copy()
    
    for col in df_copia.columns:
        # Tenta converter a coluna para número (int ou float)
        col_convertida = pd.to_numeric(df_copia[col], errors='coerce')
        
        # Se a coluna inteira não virou NaN, atualiza o DataFrame com o tipo correto
        if not col_convertida.isna().all():
            df_copia[col] = col_convertida
            
    return df_copia

def calcular_kpis_dinamicos(df: DataFrame) -> tuple[int, float, float]:
    """
    Calcula as métricas do painel com base na primeira coluna numérica encontrada.
    Retorna uma tupla contendo: (total_linhas, soma_total, media_total)
    """
    total_linhas = len(df)
    
    # Filtra apenas as colunas que possuem tipo numérico (float ou int)
    colunas_numericas = df.select_dtypes(include=['number']).columns
    
    if len(colunas_numericas) > 0 and total_linhas > 0:
        col_alvo = colunas_numericas[0]
        # .fillna(0) garante que linhas em branco na planilha não quebrem a soma
        soma_total = float(df[col_alvo].fillna(0).sum())
        media_total = float(df[col_alvo].fillna(0).mean())
    else:
        soma_total = 0.0
        media_total = 0.0
        
    return total_linhas, soma_total, media_total