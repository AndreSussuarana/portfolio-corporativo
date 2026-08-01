from datetime import datetime as dt
from database import GerenciadorBancoETL
from flask import Flask, render_template, request, redirect, send_from_directory, jsonify
import os
import pandas as pd
from projetos_auxiliares.reader import ProcessadorETL
import sqlite3
from urllib.parse import quote

app = Flask(__name__)

class GerenciadorSistema:
    """Classe responsável por encapsular as regras de negócio de Whatsapp e registros básicos"""

    def __init__(self, numero_telefone: str):
        self.numero = numero_telefone
        self.nome_banco = "banco_portfolio.db"
        self._criar_tabela()

    def _conectar(self):
        """Método auxiliar para abrir a conexão com o database"""
        return sqlite3.connect(self.nome_banco)
    
    def _criar_tabela(self):
        """Método privado que cria a tabela no banco de dados se ela não existir"""
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS acessos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    data_hora TEXT NOT NULL
                )
            """)
            conn.commit()

    def _formatar_mensagem(self, nome: str) -> str:
        """Método privado para construir e formatar a mensagem para a URL do WhatsApp"""
        mensagem_base = f"Ola! Meu nome é {nome} e vim por meio do seu site-portfólio saber mais informações"
        return quote(mensagem_base)
    
    def _salvar_no_banco(self, nome: str):
        """Método privado responsável por persistir o acesso no arquivo SQLite (.db)"""
        data_atual = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO acessos (nome, data_hora) VALUES (?, ?)",
                (nome, data_atual)
            )
            conn.commit()

    def gerar_link_contato(self, nome: str) -> str:
        """Método público que retorna o link final pronto para o redirecionamento."""
        nome_limpo = nome.strip() if nome else ""

        if not nome_limpo or len(nome_limpo) < 2:
            raise ValueError("Nome inválido para contato.")
        
        self._salvar_no_banco(nome_limpo)
        mensagem_ajustada = self._formatar_mensagem(nome_limpo)
        return f"https://wa.me/{self.numero}?text={mensagem_ajustada}"
    
    def registrar_download_cv(self):
        """Método público para registrar o download do currículo no banco"""
        self._salvar_no_banco("📥Download de Currículo (CV)")

gerenciador = GerenciadorSistema(numero_telefone="5569981636742")
instancia_banco = GerenciadorBancoETL()
processador = ProcessadorETL(instancia_banco)

# -- Rotas do Flask --

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/enviar", methods=["POST"])
def enviar():
    nome_cliente = request.form.get("nome_usuario")
    nome_seguro = nome_cliente or "Cliente"
    
    try:
        link_final = gerenciador.gerar_link_contato(nome_seguro)
        return redirect(link_final)
    except ValueError:
        return redirect("/")

@app.route("/download_cv")
def download_cv():
    gerenciador.registrar_download_cv()

    diretorio_estatico = os.path.join(app.root_path, 'static')
    nome_arquivo = 'Curriculo_Andre_Sussuarana.pdf'
    caminho_completo = os.path.join(diretorio_estatico, nome_arquivo)

    if not os.path.exists(caminho_completo):
        with open(caminho_completo, "w", encoding='utf-8') as f:
            f.write("Olá! Este é um arquivo de testes do portfólio do André Sussuarana.\n\n"
                    "Instruções para o André:\n"
                    "Substitua este arquivo 'cv.pdf' na sua pasta '/static' pelo seu currículo real em PDF.")
        return send_from_directory(
            directory=diretorio_estatico,
            path=nome_arquivo,
            as_attachment=True,
            download_name="Instrucoes_Curriculo_Andre.txt")
    
    return send_from_directory(
        directory=diretorio_estatico,
        path=nome_arquivo,
        as_attachment=True,
        download_name="Curriculo_Andre_Sussuarana.pdf"
    )

@app.route("/api/upload_etl", methods=["POST"])
def upload_etl():
    """Rota da API que recebe o arquivo CSV, processa os dados e salva localmente."""
    caminho_temporario: str = ""

    try:
        if "planilha" not in request.files:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo foi enviado"}), 400
            
        arquivo = request.files["planilha"]
        nome_ficheiro = arquivo.filename 

        if not nome_ficheiro or nome_ficheiro == "":
            return jsonify({"status": "erro", "mensagem": "O arquivo selecionado está inválido."}), 400
        
        if not nome_ficheiro.lower().endswith(".csv"):
            return jsonify({"status": "erro", "mensagem": "Formato de arquivo inválido. Apenas .csv é permitido"}), 400
        
        pasta_temp = "temp"
        if not os.path.exists(pasta_temp):
            os.makedirs(pasta_temp)
        
        caminho_temporario = os.path.join(pasta_temp, nome_ficheiro)
        arquivo.save(caminho_temporario)

        dados_brutos = processador.extrair_dados_csv(caminho_temporario)
        dados_limpos = processador.transformar_dados(dados_brutos)
        sucesso_carga = processador.carregar_no_banco(nome_ficheiro, dados_limpos)

        # Limpeza preventiva do arquivo temporário após o processamento
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)

        if sucesso_carga:
            df_limpo = pd.DataFrame(dados_limpos)
            df_limpo.columns = [str(c).upper().strip() for c in df_limpo.columns]
            df_limpo.to_csv("banco_local.csv", index=False)

            return jsonify({
                "status": "sucesso",
                "arquivo": nome_ficheiro,
                "linhas": len(dados_limpos),
                "url_redirect": "https://sussutech-dashboard.streamlit.app/"
            }), 200
        else:
            return jsonify({
                "status": "aviso",
                "mensagem": "O arquivo foi lido, mas nenhuma linha válida foi encontrada para ser analisada",
            }), 200

    except Exception as e:
        if caminho_temporario and os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)
        
        return jsonify({
            "status": "erro",
            "mensagem": f"Falha interna no processamento: {str(e)}",
        }), 500

if __name__ == "__main__":
    app.run(debug=True)