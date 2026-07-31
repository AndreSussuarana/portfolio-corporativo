import streamlit as st
import pandas as pd
import pathlib
from funcoes import processar_e_tipar_colunas, calcular_kpis_dinamicos

# --- CONFIGURAÇÃO DE ESTÉTICA E TEMA ---
st.set_page_config(
    page_title="SaaS Express Premium", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)


# Estilização minimalista via Markdown para dar um acabamento premium
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
        
        /* Deixa os cards de métricas com um visual de mini-dashboard moderno */
        div[data-testid="stMetric"] {
            background-color: rgba(28, 131, 225, 0.05);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(28, 131, 225, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Plataforma de Dados Express")
st.subheader("Suba planilhas, filtre indicadores e edite dados em tempo real")

ARQUIVO_BANCO = pathlib.Path("banco_local.csv")
ARQUIVO_FEEDBACKS = pathlib.Path("feedbacks.csv")

# Inicialização de variáveis de escopo global para o Pylance
filtro_ativo: bool = False
coluna_filtro: str = ""
opcao_selecionada: str = "Todos"

# --- 3. UPLOAD DE ARQUIVOS BASE (ONBOARDING) ---
if not ARQUIVO_BANCO.exists():
    st.info("👋 Bem-vindo! Comece definindo os campos na barra lateral ou arraste uma planilha existente abaixo.")
    arquivo_upload = st.file_uploader("📂 Importar planilha existente (.csv)", type=["csv"])
    
    if arquivo_upload is not None:
        try:
            df_carregado = pd.read_csv(arquivo_upload)
            df_carregado.columns = [str(c).upper().strip() for c in df_carregado.columns]
            df_carregado.to_csv(ARQUIVO_BANCO, index=False)
            st.toast("🚀 Planilha importada com sucesso!", icon="📊")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

# --- BARRA LATERAL: CONFIGURAÇÃO E FILTROS ---
st.sidebar.header("⚙️ Configuração Estrutural")

if ARQUIVO_BANCO.exists():
    df_bruto_local = pd.read_csv(ARQUIVO_BANCO)
    # Roda a sua função para garantir que números não sejam lidos como texto
    df_existente = processar_e_tipar_colunas(df_bruto_local)
    df_existente.columns = [str(c).upper().strip() for c in df_existente.columns]
    colunas = list(df_existente.columns)
    st.sidebar.success("🔒 **Estrutura de Dados Ativa**")
    
    # --- 1. FILTROS DINÂMICOS NA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filtros do Dashboard")
    
    df_tipado_lateral = processar_e_tipar_colunas(df_existente)
    colunas_texto = [c for c in df_existente.columns if df_existente[c].dtype == 'object']
    
    if colunas_texto:
        coluna_filtro = colunas_texto[0]
        opcoes = ["Todos"] + sorted(df_tipado_lateral[coluna_filtro].dropna().unique().tolist())
        opcao_selecionada = str(st.sidebar.selectbox(f"Filtrar por {coluna_filtro.title()}:", opcoes))
        filtro_ativo = (opcao_selecionada != "Todos")

    if st.sidebar.button("🗑️ Resetar Tudo (Apagar Banco)"):
        if ARQUIVO_BANCO.exists():
            ARQUIVO_BANCO.unlink()
        for chave in list(st.session_state.keys()):
            del st.session_state[chave]
        st.toast("Banco e memória limpos com sucesso!", icon="🗑️")
        st.rerun()
else:
    st.sidebar.warning(
        "⚠️ **Atenção:** Defina bem os seus campos agora! Uma vez que você salvar o primeiro "
        "registro, a estrutura da tabela será travada para garantir a integridade dos seus dados."
    )
    campos_usuario = st.sidebar.text_area(
        "Ou crie do zero definindo as colunas (separadas por vírgula):", 
        value="Nome, Produto, Valor, Quantidade"
    )
    colunas = [c.strip().upper() for c in campos_usuario.split(",") if c.strip()]
    
    if not colunas:
        st.sidebar.error("⚠️ Digite pelo menos um nome de coluna para iniciar o sistema!")
    else:
        st.sidebar.info("💡 Tudo pronto! Digite o primeiro registro na aba ao lado para criar sua planilha.")

# --- CORPO PRINCIPAL ORGANIZADO EM ABAS ---
tab_dados, tab_dash, tab_feedback = st.tabs([
    "📝 Lançamentos & Planilha", 
    "📊 Dashboard Inteligente", 
    "💬 Feedbacks & Avaliações"
])

# --- ABA 1: FORMULÁRIO E PLANILHA EDITÁVEL ---
with tab_dados:
    col_form, col_espaco = st.columns([1, 1])
    
    with col_form:
        st.subheader("Novo Registro")
        respostas_usuario: dict[str, str] = {}
        
        if colunas:
            for coluna in colunas:
                respostas_usuario[coluna] = st.text_input(
                    label=coluna.title(), 
                    placeholder="Digite o dado...", 
                    key=f"input_{coluna}"
                ).strip()
                
            if st.button("💾 Salvar Registro"):
                # --- AVISO DE CAMPOS VAZIOS (VALIDAÇÃO INTELIGENTE) ---
                campos_em_branco = [col.title() for col, val in respostas_usuario.items() if not val]
                
                if campos_em_branco:
                    st.error(f"⚠️ Atenção! Os seguintes campos precisam ser preenchidos: {', '.join(campos_em_branco)}")
                else:
                    with st.status("Computando dados e atualizando modelos...", expanded=True) as status:
                        dados_linha: dict[str, list[str]] = {}
                        for nome_coluna in colunas:
                            dados_linha[nome_coluna] = [str(respostas_usuario[nome_coluna])]
                        
                        nova_linha = pd.DataFrame(dados_linha)
                        
                        if ARQUIVO_BANCO.exists():
                            df_dados_brutos = pd.read_csv(ARQUIVO_BANCO)
                            df_final = pd.concat([df_dados_brutos, nova_linha], ignore_index=True)
                        else:
                            df_final = nova_linha
                            
                        df_final.to_csv(ARQUIVO_BANCO, index=False)
                        status.update(label="⚡ Registro salvo localmente com sucesso!", state="complete", expanded=False)
                    st.rerun()
        else:
            st.warning("Defina as colunas na barra lateral para liberar o formulário.")

    if ARQUIVO_BANCO.exists():
        st.markdown("---")
        st.subheader("📋 Planilha Interativa (Excel In-App)")
        
        df_dados_brutos = pd.read_csv(ARQUIVO_BANCO)
        df_editado = st.data_editor(df_dados_brutos, use_container_width=True, num_rows="dynamic", key="planilha_interativa")
        
        if not df_editado.equals(df_dados_brutos):
            df_editado.to_csv(ARQUIVO_BANCO, index=False)
            st.toast("🔄 Alterações na planilha salvas automaticamente!", icon="💾")
            st.rerun()

        csv_para_download = df_editado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar para Excel (.csv)",
            data=csv_para_download,
            file_name="dados_consolidados.csv",
            mime="text/csv",
        )

# --- ABA 2: DASHBOARD INTERATIVO ---
with tab_dash:
    st.subheader("📈 Análise de Indicadores")
    
    if ARQUIVO_BANCO.exists():
        df_dados_brutos = pd.read_csv(ARQUIVO_BANCO)
        df_dados_completos = processar_e_tipar_colunas(df_dados_brutos)
        
        if filtro_ativo and coluna_filtro:
            df_visualizacao = df_dados_completos[df_dados_completos[coluna_filtro] == opcao_selecionada]
            st.caption(f"🎯 Mostrando dados filtrados por: **{opcao_selecionada}**")
        else:
            df_visualizacao = df_dados_completos
            
        total_linhas, soma_total, media_total = calcular_kpis_dinamicos(df_visualizacao)
        
        c1, c2, c3 = st.columns(3)
        c1.metric(label="📊 Total de Linhas", value=total_linhas)
        
        colunas_numericas = df_visualizacao.select_dtypes(include=['number']).columns
        if len(colunas_numericas) > 0:
            col_alvo_kpi = colunas_numericas[0]
            c2.metric(label=f"💰 Soma de {col_alvo_kpi.title()}", value=f"{soma_total:,.2f}")
            c3.metric(label=f"📐 Média de {col_alvo_kpi.title()}", value=f"{media_total:,.2f}")
            st.markdown("---")
            
            col_grafico_config, col_grafico_vis = st.columns([1, 3], gap="medium")
            
            with col_grafico_config:
                st.markdown("🛠️ **Ajustar Visualização**")
                tipo_grafico = st.radio("Tipo de Gráfico:", ["Barras", "Linhas", "Área"], index=0)
                col_y = st.selectbox("Métrica (Eixo Y):", colunas_numericas)
                
                colunas_texto_v = [c for c in df_visualizacao.columns if c not in colunas_numericas]
                col_x = st.selectbox("Categoria (Eixo X):", colunas_texto_v if colunas_texto_v else df_visualizacao.columns)
            
            with col_grafico_vis:
                df_grafico = df_visualizacao.groupby(col_x)[col_y].sum()
                st.markdown(f"**Gráfico dinâmico de {tipo_grafico}:** `{col_y.title()}` por `{col_x.title()}`")
                
                if tipo_grafico == "Barras":
                    st.bar_chart(df_grafico, use_container_width=True)
                elif tipo_grafico == "Linhas":
                    st.line_chart(df_grafico, use_container_width=True)
                elif tipo_grafico == "Área":
                    st.area_chart(df_grafico, use_container_width=True)

                st.markdown("----")

                item_campeao: int | str = ""
                texto_formatado: str = ""
                if not df_visualizacao.empty and len(df_grafico) > 0:
                    item_campeao = df_grafico.idxmax()
                    valor_campeao = df_grafico.max()
                    if "QUANTIDADE" in col_y.upper():
                        texto_formatado = f"**{int(valor_campeao)} unidades**"
                    else:
                        texto_formatado = f"**R$ {valor_campeao:,.2f}**"
        
                st.success(f"💡 **Insight de Negócio:** O maior acumulado de `{col_y.title()}` pertence a **{item_campeao}**, totalizando {texto_formatado}!")
                # Criamos duas coluninhas menores para os botões de ação ficarem alinhados
                col_btn_1, col_btn_2 = st.columns([2, 1])
                
                with col_btn_1:
                    # 2. Tabela Oculta/Expansível para auditoria
                    with st.expander("🔍 Rastreabilidade: Ver Linhas Deste Recorte"):
                        st.dataframe(df_visualizacao, use_container_width=True)
                        
                with col_btn_2:
                    # 3. Botão para exportar o filtro atual
                    csv_filtrado = df_visualizacao.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Filtro Atual",
                        data=csv_filtrado,
                        file_name="recorte_dashboard.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                st.markdown("---")
                st.markdown("### 🧮 Matriz de Cruzamento Comercial (Mapa de Calor)")
                st.caption("Entenda o cruzamento de duas categorias de texto baseadas na métrica selecionada.")

                # Pegamos todas as colunas de texto disponíveis para os seletores da matriz
                opcoes_matriz = [c for c in df_visualizacao.columns if c not in colunas_numericas]

                if len(opcoes_matriz) >= 2:
                    c_matriz_1, c_matriz_2 = st.columns(2)
                    with c_matriz_1:
                        eixo_linhas = st.selectbox("Linhas da Matriz:", opcoes_matriz, index=0, key="matriz_linhas")
                    with c_matriz_2:
                        # Garante que o segundo seletor comece com uma opção diferente se houver
                        index_padrao = 1 if len(opcoes_matriz) > 1 else 0
                        eixo_colunas = st.selectbox("Colunas da Matriz:", opcoes_matriz, index=index_padrao, key="matriz_colunas")

                    if eixo_linhas != eixo_colunas:
                        # 1. Cria a Tabela Dinâmica somando a métrica escolhida no painel lateral (col_y)
                        df_pivot = df_visualizacao.pivot_table(
                            index=eixo_linhas,
                            columns=eixo_colunas,
                            values=col_y,
                            aggfunc='sum',
                            fill_value=0
                        )

                        # 2. Aplica a estilização de gradiente do Pandas (Cor 'Blues' ou 'Greens')
                        df_estilizado = df_pivot.style.background_gradient(cmap='Blues', axis=None)

                        # 3. Exibe no Streamlit mantendo a interatividade
                        st.dataframe(df_estilizado.format("{:.2f}"), use_container_width=True)
                    else:
                        st.warning("⚠️ Selecione categorias diferentes para as linhas e colunas para cruzar os dados.")
                else:
                    st.info("💡 A matriz de cruzamento precisa de pelo menos 2 colunas de texto no seu arquivo (ex: Cliente e Produto).")
        else:
            c2.metric(label="💰 Métrica Financeira", value="N/A")
            c3.metric(label="📐 Média Geral", value="N/A")
            st.info("💡 Insira ou importe colunas numéricas para habilitar os gráficos e cálculos.")
    else:
        st.info("✨ O Dashboard será gerado automaticamente aqui assim que o primeiro registro for salvo na primeira aba.")

# --- ABA 3: CENTRAL DE FEEDBACK ---
with tab_feedback:
    st.subheader("💬 Sua opinião é fundamental!")
    st.write("Ajude-nos a lapidar a plataforma relatando problemas ou sugerindo novas ideias.")
    
    col_feed, col_historico = st.columns([1, 1], gap="large")
    
    with col_feed:
        with st.form("formulario_feedback", clear_on_submit=True):
            nome_usuario = st.text_input("Seu Nome (Opcional):", placeholder="Ex: João Silva")
            nota = st.slider("Qual nota você dá para a experiência com o app?", min_value=1, max_value=5, value=5)
            mensagem = st.text_area("Escreva seu comentário ou sugestão:", placeholder="Ex: Adorei a planilha editável, mas seria legal se...", max_chars=500)
            enviar_feedback = st.form_submit_button("Enviar Avaliação 🚀")
            
            if enviar_feedback:
                if not mensagem.strip():
                    st.error("Por favor, preencha a mensagem antes de enviar.")
                else:
                    novo_feedback = pd.DataFrame([{
                        "DATA": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "NOME": nome_usuario.strip() if nome_usuario.strip() else "Anônimo",
                        "NOTA": f"{'★' * nota}{'☆' * (5 - nota)}",  # Converte a nota em estrelas visuais bem legais
                        "MENSAGEM": mensagem.strip()
                    }])
                    
                    if ARQUIVO_FEEDBACKS.exists():
                        df_fb_existente = pd.read_csv(ARQUIVO_FEEDBACKS)
                        df_fb_final = pd.concat([df_fb_existente, novo_feedback], ignore_index=True)
                    else:
                        df_fb_final = novo_feedback
                        
                    df_fb_final.to_csv(ARQUIVO_FEEDBACKS, index=False)
                    st.toast("Obrigado pelo seu feedback! 🌟", icon="💖")
                    st.rerun()

    with col_historico:
        st.subheader("📝 Feedbacks Recebidos")
        if ARQUIVO_FEEDBACKS.exists():
            df_fb = pd.read_csv(ARQUIVO_FEEDBACKS)
            # Mostra os feedbacks mais recentes primeiro
            for _, linha in df_fb.iloc[::-1].iterrows():
                st.markdown(f"**{linha['NOME']}** • {linha['NOTA']} • *{linha['DATA']}*")
                st.info(linha['MENSAGEM'])
        else:
            st.caption("Ainda não recebemos nenhum feedback. Seja o primeiro a avaliar!")


st.markdown("---")
st.caption("⚡ **SaaS Express Premium** • Desenvolvido por André | Engenharia de Software & Dados")