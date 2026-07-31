class InterfaceETL {
    /**
     * Inicializa a classe mapeando os elementos do DOM e configurando os eventos.
     * @param {string} idFormulario - ID do formulário de upload
     * @param {string} idAreaFeedback - ID da div para mostrar mensagens
     */
    constructor(idFormulario, idAreaFeedback){
        this.formulario = document.getElementById(idFormulario);
        this.areaFeedback = document.getElementById(idAreaFeedback);

        if (this.formulario){
            this.registrarEventos();
        }
    }
    /**
     * Registra os eventos de clique e submissão na tela.
     */
    registrarEventos(){
        this.formulario.addEventListener('submit', (evento) => this.processarEnvio(evento));
    }
    /**
     * Gerencia o envio do arquivo via Fetch API (AJAX).
     */
    async processarEnvio(evento) {
        evento.preventDefault();

        const inputArquivo = this.formulario.querySelector('input[type="file"]');
        if (!inputArquivo.files.length) {
            this.exibirMensagem("Por favor, selecione um arquivo primeiro!", "alerta");
            return;
        }
        const arquivo = inputArquivo.files[0];
        const dadosFormulario = new FormData();
        dadosFormulario.append('planilha', arquivo);

        this.exibirMensagem("Processando arquivo e consolidando dados...", "carregando");

        try {
            // Requisição assíncrona para a API Flask
            const resposta = await fetch('/api/upload_etl', {
                method: 'POST',
                body: dadosFormulario
            });

            const resultado = await resposta.json();

            if (resposta.ok) {
                this.exibirMensagem(
                    `Sucesso! ${resultado.linhas} linhas do arquivo "${resultado.arquivo}" foram consolidadas com êxito!`, 
                    "sucesso"
                );
                this.formulario.reset();
            } else {
                throw new Error(resultado.mensagem || "Erro inesperado ao processar arquivo.");
            }
        } catch {
            this.exibirMensagem(`Falha no processo de ETL: ${erro.message}`, "erro");
        }
        
    }
    /**
     * Atualiza a interface do usuário com mensagens estilizadas.
     */
    exibirMensagem(texto, tipo) {
        this.areaFeedback.className = `feedback-box ${tipo}`;
        this.areaFeedback.innerHTML = `
            <span class="feedback-icon"></span>
            <span class="feedback-text">${texto}</span>
        `;
    }
}
// Inicializando a nossa classe JavaScript assim que a página carregar
window.addEventListener('DOMContentLoaded', () => {
    const appETL = new InterfaceETL('form-upload-etl', 'feedback-etl');
});
