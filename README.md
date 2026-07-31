# Plataforma Integrada de Contato & Pipeline ETL Resiliente

Este projeto demonstra a construção de um ecossistema funcional que une desenvolvimento backend (**Flask**), engenharia de dados (**ETL/SQLite**) e análise visual de dados (**Streamlit**). O sistema foi projetado seguindo boas práticas de arquitetura de software, tratamento de exceções e regras adaptativas de integridade de dados.

O objetivo principal é simular um cenário real de governança de dados: capturar interações de usuários (contatos e downloads), processar cargas financeiras externas massivas corrigindo falhas humanas comuns de digitação, e expor esses dados de forma limpa e gerencial.

---

## Arquitetura do Sistema

O ecossistema é dividido em três camadas principais:

1. **Frontend Institucional (Flask + HTML/CSS):** Interface onde o usuário insere seu nome para ser redirecionado ao WhatsApp com mensagem tratada de forma segura (`urllib.parse.quote`) e realiza o download de documentos (como o Currículo).
2. **Pipeline de Dados ETL (Python + SQLite):** Camada sênior e resiliente responsável por ler arquivos CSV temporários, validar campos obrigatórios, aplicar regras matemáticas de autocompletude de preços e persistir os registros em banco relacional.
3. **Dashboard de Business Intelligence (Streamlit):** Interface administrativa que lê o banco local refinado e renderiza uma Matriz de Cruzamento Comercial (Mapa de Calor) com formatação decimal limpa (`.2f`).

---

## Regras de Negócio & Resiliência Implementadas

*   **Higienização de Moedas:** O pipeline analisa strings financeiras de forma inteligente, distinguindo o uso de pontos e vírgulas para centavos ou milhares (padrão brasileiro vs. americano), impedindo distorções nos valores convertidos para `float`.
*   **Integridade Adaptativa (Cálculo Automático):** Caso a planilha original contenha campos em branco ou zerados por erro humano, o sistema recalcula os valores de forma analítica:
    *   Se possui *Quantidade* e *Valor Unitário*, mas falta o *Valor Total*: O pipeline calcula e preenche o total.
    *   Se possui *Quantidade* e *Valor Total*, mas falta o *Valor Unitário*: O sistema deduz o valor unitário real (`Total / Quantidade`).
*   **Segurança contra Injeção de Dados:** Uso rigoroso de consultas parametrizadas (`?`) no SQLite, mitigando riscos de SQL Injection.
*   **Tratamento Preventivo:** Isolamento de erros com blocos `try/except` específicos (`ValueError`, `TypeError`), garantindo que linhas corrompidas sejam descartadas com logs informativos sem derrubar a execução de toda a carga.

---

## Como Executar o Projeto Localmente

### 1. Clonar o repositório
```bash
git clone [https://github.com/AndreSussuarana/NOME_DO_SEU_REPOSITORIO.git](https://github.com/AndreSussuarana/NOME_DO_SEU_REPOSITORIO.git)
cd NOME_DO_SEU_REPOSITORIO