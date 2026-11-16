# UStory.IA 🧠🤖

**Uma Ferramenta Baseada em IA e RAG para Engenharia de Requisitos e Geração de Backlogs**

---

## 🌐 Visão Geral
A **UStory.IA** é uma solução inteligente desenvolvida para otimizar o processo de Engenharia de Requisitos por meio da geração automatizada, estruturada e auditada de Histórias de Usuário (*User Stories*). 
O sistema integra técnicas avançadas de Geração Aumentada por Recuperação (**RAG**), bases vetoriais em memória (**FAISS**) e ferramentas encadeadas em Python para transformar especificações de escopo em artefatos ágeis de alta qualidade, avaliados automaticamente com base nos frameworks **QUS** e **INVEST**.

---

## 🔗 Links e Avaliação
- **📝 Formulário de Avaliação (TAM):** [Acessar Formulário TAM](https://docs.google.com/forms/d/e/1FAIpQLScXBCVIn4Big93odLjCgknyBbtWauECcO7YUaDN5qUJjeLbfw/viewform?usp=header)
- **📋 Formulários de Avaliação de Qualidade das Histórias de Usuário:**
  * **AV01:** [Acessar Formulário AV01](https://docs.google.com/forms/d/e/1FAIpQLSf7FoJTXSSaTAOscF2CkjC3gKCVk3zcMCefOChmH-5dUvnNqA/viewform?usp=header)
  * **AV02:** [Acessar Formulário AV02](https://docs.google.com/forms/d/e/1FAIpQLScchIEDPf2GSF4kOMiPjVfRwy3Oo9r1nFcP1rvbzlGfDJaQYw/viewform?usp=header)
  * **AV03:** [Acessar Formulário AV03](https://docs.google.com/forms/d/e/1FAIpQLScpZX8XHrI2ALrBkGtp7rwfheezWrXC_kqEyjfHz8F--hHWiQ/viewform?usp=header)
- **🌐 Aplicação Web (Streamlit):** [https://use-story-generation.streamlit.app/](https://use-story-generation.streamlit.app/)

---

## 🚀 Motivação
A derivação manual de histórias de usuário a partir de documentos extensos é uma atividade complexa, suscetível a ambiguidades e inconsistências. 
A **UStory.IA** foi concebida para automatizar e auditar esse fluxo, encapsulando estratégias rigorosas de engenharia de prompt e verificação de cobertura, permitindo que analistas, estudantes e equipes de desenvolvimento obtenham backlogs estruturados sem a necessidade de domínio avançado em engenharia de prompt.

---

## ✨ Principais Funcionalidades
A plataforma oferece suporte integrado para:
- 📥 **Ingestão e Vetorização de Escopo:** Leitura de URLs, limpeza de conteúdo HTML e fragmentação inteligente (`RecursiveCharacterTextSplitter` + *embeddings* `text-embedding-3-small`).
- 🔍 **Análise Normativa:** Diagnóstico inicial e mapeamento automático de regras de negócio, módulos e lacunas no documento de requisitos.
- ⚙️ **Geração Iterativa por RAG:** Criação de histórias em etapas encadeadas para evitar limites de tokens, garantindo o formato canônico (*Como [Ator], quero [Ação], para que [Benefício]*) e critérios de aceitação ancorados no texto original.
- 🎯 **Garantia de Cobertura (100%):** Auditoria automática de rastreabilidade para certificar que nenhum requisito ou módulo ficou de fora do backlog.
- 🛡️ **Auditoria Semântica e Estrutural:** Validação rigorosa contra alucinações e checagem automática de conformidade pelos critérios **QUS** (*Quality of User Stories*) e **INVEST**.
- 📊 **Interface Interativa em Streamlit:** Painel visual completo para acompanhamento da execução do pipeline e exportação dos relatórios auditados.

---

## 👥 Público-Alvo
A **UStory.IA** foi projetada para apoiar:
- Engenheiros e Analistas de Requisitos
- Product Owners (POs) e Gerentes de Produto
- Analistas de Sistemas e Equipes Ágeis
- Pesquisadores, Docentes e Estudantes de Engenharia de Software

---

## 🏗️ Arquitetura e Orquestração Multi-Ferramentas
A aplicação é desenvolvida integralmente em **Python**, utilizando **Streamlit** na camada de interface e um pipeline modular composto por ferramentas especializadas e encadeadas:

1. **`rag_indexing_tool`**: Ingestão, limpeza de texto (`get_text_from_url`), *chunking* (500 caracteres com *overlap* de 120) e armazenamento vetorial em memória via **FAISS**.
2. **`normative_analysis_tool`**: Pesquisa de similaridade no FAISS e diagnóstico inicial estruturado em módulos, regras de negócio, lacunas e perguntas de refinamento.
3. **`user_story_rag_generation_tool`**: Geração iterativa em duas etapas encadeadas via LLM (`gpt-4o-mini`, `temp = 0.0`) para evitar truncamento de tokens.
4. **`gap_coverage_verification_tool`**: Auditoria de rastreabilidade que compara o escopo mapeado com o backlog gerado, assegurando 100% de cobertura.
5. **`semantic_consistency_tool`**: Auditoria semântica individual para prevenir alucinações e garantir aderência estrita ao documento de origem.
6. **`requirements_coverage_tool`**: Construção da matriz de rastreabilidade de requisitos em formato estruturado (`JSON`).
7. **`quality_assessment_tool`**: Avaliação estrutural e sintática baseada nos 7 critérios binários do framework **QUS** (notas de `0/7` a `7/7`).
8. **`invest_assessment_tool`**: Avaliação de viabilidade ágil baseada nas 6 dimensões do acrônimo **INVEST** (notas de `0/6` a `6/6`).
9. **Utilitários Determinísticos (`recalcular_metricas_markdown`)**: Pós-processamento em Python via expressões regulares (*Regex*) para garantir exatidão matemática nos relatórios finais.

---

## ⚙️ Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone [https://github.com/n2Gabrielle/UStory.IA.git](https://github.com/n2Gabrielle/UStory.IA.git)
cd UStory.IA
```

### 2. Criar e Ativar o Ambiente Virtual
```bash
python -m venv .venv
```

- **Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

- **Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto contendo a sua chave da API da OpenAI:
```env
OPENAI_API_KEY=sua_chave_aqui
```

### 5. Executar a Aplicação (Streamlit)
```bash
streamlit run app.py
```

---

## 📦 Disponibilidade de Artefatos (*Artifact Availability*)
Todos os artefatos utilizados e produzidos durante o experimento, incluindo o código-fonte da ferramenta **UStory.IA**, os instrumentos dos questionários de avaliação (TAM, AV01, AV02 e AV03) e os recursos de suporte, encontram-se publicamente disponíveis neste repositório e nos links oficiais. A ferramenta web interativa também está acessível em: [https://use-story-generation.streamlit.app/](https://use-story-generation.streamlit.app/).

---

## 👥 Autores e Orientação

- **Daniel Izu Campos** — *Discente / Autor*  
  Instituto de Computação — Universidade Federal Fluminense (UFF)
- **Gabrielle de Oliveira Silva Rosa** — *Discente / Autora*  
  Instituto de Computação — Universidade Federal Fluminense (UFF)  
- **Rebeca Campos Motta** — *Orientadora*  
  Instituto de Computação — Universidade Federal Fluminense (UFF)

---

## 🏛️ Instituição
- **Instituição:** Instituto de Computação (IC) — Universidade Federal Fluminense (UFF), Niterói, RJ, Brasil (https://www.ic.uff.br/)
