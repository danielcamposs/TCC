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

# def get_text_from_url(url: str) -> str:
#     # Mantendo o mock para o  ambiente local 
#     return "Texto bruto extraído do documento acadêmico da UFF com requisitos sobre centralização de materiais e regras como e-mail @id.uff.br obrigatório."
def get_text_from_url(url: str) -> str:
    """
    Mock atualizado contendo o escopo legítimo da UFF e um cenário absurdo 
    injetado intencionalmente para testar o validador semântico (V1).
    """
    return """
    --- DOCUMENTO DE ESCOPO DO PROJETO UFF ---
    1. Requisitos Legítimos:
    O sistema deve centralizar materiais acadêmicos em um repositório acessível. 
    O e-mail institucional @id.uff.br é obrigatório para todos os usuários (estudantes, professores e funcionários) realizarem a autenticação segura.

    2. Cenário de Teste de Estresse Semântico (Injetado Propositalmente):
    Adicionalmente, o sistema deve permitir que o ator 'Lápis de Cor' consiga 'dirigir o módulo de transporte' para que 'o servidor consiga voar até a nuvem de dados'.
    """

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
def semantic_consistency_tool(user_stories: str, structured_context: str) -> str:
    """
    Avalia se as User Stories geradas fazem sentido lógico, se são semanticamente 
    coerentes e se estão estritamente alinhadas ao contexto e domínio real do projeto.
    """
    messages = [
        SystemMessage(content="""Você é um Engenheiro de Software sênior especialista em Validação Semântica de Requisitos.
Sua função não é avaliar a fôrma ou a gramática das histórias, mas sim o NEXO COGNITIVO, COERÊNCIA SEMÂNTICA e o ALINHAMENTO DE DOMÍNIO.
Você deve caçar absurdos lógicos, ações fisicamente impossíveis (ex: objetos inanimados agindo como atores humanos) ou funcionalidades que inventam escopos fora do contexto fornecido."""),
        HumanMessage(content=f"""
            Compare as User Stories geradas com o Contexto Estruturado do Projeto para garantir que não há falhas lógicas e de nexo.

            CONTEXTO ESTRUTURADO ORIGINAL:
            ---
            {structured_context}
            ---

            USER STORIES GERADAS:
            ---
            {user_stories}
            ---

            Para cada User Story, faça uma análise crítica respondendo em formato de relatório curto:
            1. Coerência Semântica: A ação descrita faz sentido lógico no mundo real? (Atores legítimos e ações coerentes).
            2. Pertinência de Domínio: Essa história resolve um problema mapeado no contexto original ou está alucinando escopo?

            Atribua um status claro de [APROVADO SEMANTICAMENTE] ou [REPROVADO SEMANTICAMENTE] para cada história.
            Se houver reprovação devido a um absurdo semântico, justifique o erro encontrado.
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

# CONFIGURAÇÃO DO AGENTE ATUALIZADO (Incluída a validação semântica cruzada)
toolkit = [context_extraction_tool, user_story_generation_tool, semantic_consistency_tool, quality_assessment_tool, invest_assessment_tool]

prompt = ChatPromptTemplate.from_messages([
    ("system", """
Você é um Engenheiro de Software automatizado especialista em Engenharia de Requisitos Ágeis e Validação Avançada de Modelos.
Seu fluxo de trabalho é estrito, ordenado e obrigatório:
    1. Execute a 'context_extraction_tool' passando a URL enviada pelo usuário.
    2. Envie o contexto gerado para a 'user_story_generation_tool'.
    3. Envie as histórias geradas E o contexto estruturado da etapa 1 para a 'semantic_consistency_tool' para caçar absurdos lógicos e garantir o alinhamento de nexo do domínio.
    4. Envie as histórias geradas para a 'quality_assessment_tool' (Auditoria QUS).
    5. Envie as MESMAS histórias geradas para a 'invest_assessment_tool' (Auditoria INVEST).
    
    ESTRUTURA DE RESPOSTA FINAL (Siga rigorosamente esta estrutura enxuta no output final):
    
    ### 3.4. Resultados e Métricas do Estudo Piloto (Pipeline de Agente com Validação Semântica)

    A execução do pipeline automatizado processou o escopo do projeto da UFF, gerou um backlog de User Stories (US) e aplicou uma tripla camada de auditoria. Os resultados consolidados são apresentados abaixo:

    #### 1. Consolidação Quantitativa das Métricas
    - [MÉTRICAS QUS: ... ]
    - [MÉTRICAS INVEST: ... ]

    #### 2. Relatório de Validação de Domínio e Nexo Semântico
    (Apresente aqui o resumo do resultado obtido na 'semantic_consistency_tool' indicando se o nexo lógico das histórias foi integralmente aprovado ou se alguma bizarrice conceitual foi encontrada).

    #### 3. Relatório de Auditoria Simplificado (Métricas Estruturais)
    Monte uma tabela Markdown comparativa consolidando os dados das ferramentas QUS e INVEST com as colunas exatas:
    | ID da US | Funcionalidade Principal | Avaliação QUS (Total: 7) | Avaliação INVEST (Total: 6) | Critério com Falha detectado |

    #### 4. Diagnóstico Técnico dos Resultados
    Apresente uma justificativa analítica curta (em tópicos) explicando:
    - Por que a métrica QUS atingiu o resultado obtido.
    - Por que a métrica INVEST variou ou se comportou dessa forma.
    - Como a nova camada de consistência semântica impede que histórias sintaticamente perfeitas mas absurdas (ex: "lápis que dirige") passem pelo pipeline sem supervisão.
    
    Termine com uma breve conclusão sobre o papel estratégico e insubstituível do engenheiro humano no refino final do fatiamento do backlog.
    """),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, toolkit, prompt)
agent_executor = AgentExecutor(agent=agent, tools=toolkit, verbose=True)
if __name__ == "__main__":
    import time
    import tracemalloc
    from langchain_community.callbacks.manager import get_openai_callback

    url_teste = "https://docs.google.com/document/d/e/2PACX-1vTwj4Yh9UVPzqEpHJMprp875O7bW6XRQek_JNl-1ZxriLWvXvWInIxlxaYY4-yTRRTvxNIvUSPkuFbm/pub"
    
    # 1. Inicia o monitoramento de Hardware (Memória e Tempo)
    tracemalloc.start()
    tempo_inicial = time.time()
    
    # 2. Inicia o monitoramento da API da OpenAI (Tokens)
    with get_openai_callback() as cb:
        
        # Execução do Pipeline do Agente
        result = agent_executor.invoke({
            "input": f"Execute todo o pipeline de engenharia de requisitos com tripla auditoria (Semântica + QUS + INVEST) para o projeto em: {url_teste}"
        })
        
        # Finaliza a medição de tempo e hardware logo após a execução do agente
        tempo_final = time.time()
        memoria_atual, memoria_pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 3. Cálculo matemático manual do custo real do gpt-4o-mini
        # Preço por token: Entrada = $0.15 / 1.000.000 | Saída = $0.60 / 1.000.000
        custo_entrada = (cb.prompt_tokens / 1000000) * 0.15
        custo_saida = (cb.completion_tokens / 1000000) * 0.60
        custo_real_calculado = custo_entrada + custo_saida
        
        # --- PRINTS DOS RESULTADOS ---
        print("\n=== OUTPUT FINAL DO EXPERIMENTO ===\n")
        print(result["output"])
        
        print("\n=== MÉTRICAS DE DESEMPENHO DA MÁQUINA (LOCAL) ===")
        print(f"Tempo total de execução: {tempo_final - tempo_inicial:.2f} segundos")
        print(f"Consumo de Memória RAM de Pico: {memoria_pico / (1024 * 1024):.2f} MB")
        
        print("\n=== MÉTRICAS DE CONSUMO DA API (NUVEM - OPENAI) ===")
        print(f"Total de Tokens Usados: {cb.total_tokens}")
        print(f"Tokens de Entrada (Prompt): {cb.prompt_tokens}")
        print(f"Tokens de Saída (Completion): {cb.completion_tokens}")
        # Exibe o custo com formatador de 6 casas decimais para capturar frações de centavos
        print(f"Custo Total Estimado (Nativo LangChain): ${cb.total_cost:.5f} USD")
        print(f"Custo Total Real (Calculado gpt-4o-mini): ${custo_real_calculado:.6f} USD")