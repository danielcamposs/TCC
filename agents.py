import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool

# CONFIGURAÇÃO GLOBAL (Utilizando gpt-4o-mini para melhor inteligência e custo-benefício)
os.environ["OPENAI_API_KEY"] = "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"
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def get_response_from_openai(messages):
    return llm.invoke(messages)

def get_text_from_url(url: str) -> str:
    # Mantendo o mock para o seu ambiente local (substitua pela chamada real do seu scraper se necessário)
    return "Texto bruto extraído do documento acadêmico da UFF com requisitos sobre centralização de materiais e regras como e-mail @id.uff.br obrigatório."

@tool
def context_extraction_tool(url: str) -> str:
    """
    Acessa a URL, extrai o texto bruto e gera um artefato de Contexto Estruturado
    (Atores, Regras de Negócio Invioláveis e Escopo Macro).
    """
    raw_context = get_text_from_url(url)
    messages = [
        SystemMessage(content="Você é um Engenheiro de Requisitos Sênior especializado em modelagem de domínio."),
        HumanMessage(content=f"""Analise o texto abaixo e extraia o contexto estruturado:
    ---
    {raw_context}
    ---
    Retorne no formato:
    # CONTEXTO ESTRUTURADO DO PROJETO
    ## 1. ATORES DO SISTEMA
    - [Atores]
    ## 2. REGRAS DE NEGÓCIO E RESTRIÇÕES INVIOLÁVEIS
    - [Regras]
    ## 3. ESCOPO MACRO (FUNCIONALIDADES)
    - [Módulos]
    """)
    ]
    return get_response_from_openai(messages).content

@tool
def user_story_generation_tool(structured_context: str) -> str:
    """
    Recebe o Contexto Estruturado e gera o Backlog de User Stories formal com critérios de aceitação.
    """
    messages = [
        SystemMessage(content="Você é um Analista de Sistemas Ágil. Você escreve User Stories baseadas em Contexto Estruturado."),
        HumanMessage(content=f"""Com base no Contexto Estruturado abaixo, gere as User Stories necessárias usando o padrão 'Como [Ator], quero [Ação], para que [Benefício]'. Adicione 2 critérios de aceitação simples por história.
        
        {structured_context}
        """)
    ]
    return get_response_from_openai(messages).content

@tool
def quality_assessment_tool(user_stories: str) -> str:
    """
    Avalia a qualidade das User Stories geradas usando os 7 critérios do framework QUS.
    """
    messages = [
        SystemMessage(content="Você é um auditor de qualidade de requisitos especialista no framework QUS."),
        HumanMessage(content=f"""
            Analise cada uma das seguintes User Stories sob os 7 critérios do framework QUS (avaliação binária: 1 ou 0).
            Apresente a identificação da US, uma tabela curta dos critérios e a pontuação final (X de 7).

            Critérios QUS: 1. Bem-formada | 2. Atômica | 3. Conceitualmente Sólida | 4. Inambígua | 5. Mínima | 6. Sentença Completa | 7. Estimável.

            User Stories para avaliar:
            {user_stories}
            
            IMPORTANTE: No final do texto desta ferramenta, termine com a tag:
            [MÉTRICAS QUS: TOTAL_PONTOS / TOTAL_POSSIVEIS]
        """)
    ]
    return get_response_from_openai(messages).content  

@tool
def invest_assessment_tool(user_stories: str) -> str:
    """
    Avalia o backlog de User Stories utilizando o framework INVEST focado em agilidade.
    """
    messages = [
        SystemMessage(content="Você é um Agile Coach especialista no acrônimo INVEST para histórias de usuário."),
        HumanMessage(content=f"""
            Analise as seguintes User Stories sob os 6 critérios do framework INVEST.
            Atribua 1 para Atendido e 0 para Não Atendido para cada critério por história.

            Critérios INVEST:
            - I (Independent): A história pode ser desenvolvida sem depender fortemente de outra?
            - N (Negotiable): Deixa espaço para discussão ou está super-especificada detalhando telas/código?
            - V (Valuable): Traz valor claro para o cliente/usuário final?
            - E (Estimable): O time de desenvolvimento consegue estimar o esforço?
            - S (Small): É pequena o suficiente para caber em uma Sprint?
            - T (Testable): Possui critérios de aceitação que permitem escrever um teste de software?

            Para CADA User Story, apresente:
            - Identificação da US
            - Lista dos 6 critérios (1 ou 0) com uma breve justificativa prática.
            - Pontuação final da história (X de 6).

            User Stories para avaliar:
            {user_stories}

            IMPORTANTE: No final do texto desta ferramenta, termine com a tag:
            [MÉTRICAS INVEST: TOTAL_PONTOS / TOTAL_POSSIVEIS]
        """)
    ]
    return get_response_from_openai(messages).content

# CONFIGURAÇÃO DO AGENTE ATUALIZADO (Adicionada a nova ferramenta ao toolkit)
toolkit = [context_extraction_tool, user_story_generation_tool, quality_assessment_tool, invest_assessment_tool]

prompt = ChatPromptTemplate.from_messages([
    ("system", """
Você é um Engenheiro de Software automatizado especialista em Engenharia de Requisitos Ágeis.
Seu fluxo de trabalho é estrito e obrigatório:
    1. Execute a 'context_extraction_tool' passando a URL enviada pelo usuário.
    2. Envie o contexto gerado para a 'user_story_generation_tool'.
    3. Pegue as histórias geradas e envie para a 'quality_assessment_tool' (Auditoria QUS).
    4. Pegue as MESMAS histórias geradas e envie para a 'invest_assessment_tool' (Auditoria INVEST).
    
    ESTRUTURA DE RESPOSTA FINAL (Siga rigorosamente esta estrutura enxuta no output):
    
    ### 3.4. Resultados e Métricas do Estudo Piloto (Pipeline de Agente)

    A execução do pipeline automatizado processou o escopo do projeto da UFF e gerou um backlog de User Stories (US) completas. A auditoria dupla automatizada obteve os seguintes resultados consolidados:

    #### 1. Consolidação Quantitativa das Métricas
    - [MÉTRICAS QUS: ... ]
    - [MÉTRICAS INVEST: ... ]

    #### 2. Relatório de Auditoria Simplificado
    Monte uma tabela Markdown comparativa com as colunas:
    | ID da US | Funcionalidade Principal | Avaliação QUS (Total: 7) | Avaliação INVEST (Total: 6) | Critério com Falha detectado |

    #### 3. Diagnóstico Técnico dos Resultados
    Apresente uma justificativa analítica curta (em tópicos) explicando:
    - Por que a métrica QUS atingiu o resultado obtido (focando na disciplina sintática e no isolamento de contexto).
    - Por que a métrica INVEST variou (focando nos critérios de tamanho 'Small' e na granularidade das tarefas).
    
    Termine com uma breve conclusão sobre o papel do engenheiro humano no fatiamento de histórias.
    """),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, toolkit, prompt)
agent_executor = AgentExecutor(agent=agent, tools=toolkit, verbose=True)

if __name__ == "__main__":
    url_teste = "https://docs.google.com/document/d/e/2PACX-1vTwj4Yh9UVPzqEpHJMprp875O7bW6XRQek_JNl-1ZxriLWvXvWInIxlxaYY4-yTRRTvxNIvUSPkuFbm/pub"
    result = agent_executor.invoke({"input": f"Execute todo o pipeline de engenharia de requisitos com auditoria dupla (QUS + INVEST) para o projeto em: {url_teste}"})
    print("\n=== OUTPUT FINAL DO EXPERIMENTO ===\n")
    print(result["output"])