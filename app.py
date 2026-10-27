import sys
import os

# Remove o diretório atual do topo da busca de caminhos do Python
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
if diretorio_atual in sys.path:
    sys.path.remove(diretorio_atual)
sys.path.append(diretorio_atual)

import time
import tracemalloc
import re
import io
import json
import uuid
from datetime import datetime
import requests
import pandas as pd
import gspread
from openpyxl.styles import Alignment, Font, PatternFill
from bs4 import BeautifulSoup
import streamlit as st
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.callbacks import BaseCallbackHandler
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# O Streamlit reexecuta o script inteiro a cada clique: a base vetorial e os resultados ficam
# em st.session_state para sobreviver aos reruns (ex.: clique no botão de refinamento).
VECTOR_STORE = st.session_state.get("vector_store")

# Resultados produzidos pelas ferramentas na execução atual.
# As ferramentas de verificação/avaliação e a interface leem daqui, em vez de depender
# do agente repassar (e muitas vezes resumir ou truncar) textos longos.
RESULTADOS = st.session_state.setdefault("resultados", {})

def estado_inicial() -> dict:
    return {
        "analise_normativa": "",
        "historias": [],
        "lacunas": [],
        "semantica": "",
        "cobertura": "",
        "qus": "",
        "invest": "",
        "refinamentos": [],
        # None = avaliar o backlog completo; lista = modo refinamento, reavaliar só essas histórias
        "ids_reavaliar": None,
    }

def novo_estado_execucao():
    RESULTADOS.clear()
    RESULTADOS.update(estado_inicial())

# Mantém os resultados de reruns anteriores; só completa as chaves ausentes
for chave, valor in estado_inicial().items():
    RESULTADOS.setdefault(chave, valor)

def backlog_completo() -> str:
    return "\n\n".join(RESULTADOS["historias"])

def normalizar_id_us(texto: str) -> str:
    return re.sub(r'US-?\s*(\d+)', lambda m: f"US-{int(m.group(1)):03d}", texto, flags=re.IGNORECASE)

def ids_no_backlog() -> list:
    ids = {normalizar_id_us(m) for m in re.findall(r'US-?\s*\d+', backlog_completo(), re.IGNORECASE)}
    return sorted(ids, key=lambda s: int(s.split("-")[1]))

PADRAO_MODULO = re.compile(r'^\s*#+\s*Módulo\s*:?\s*(.+)$', re.IGNORECASE)
PADRAO_TITULO_US = re.compile(r'^\W*(US-?\s*\d+)\s*[-–—:]\s*(.+)$', re.IGNORECASE)

def segmentar_backlog(texto: str) -> list:
    """Divide o texto do backlog em segmentos [ID, texto], na ordem original.
    Títulos de módulo e textos soltos ficam em segmentos com ID None."""
    segmentos = []
    for linha in texto.splitlines():
        m_us = PADRAO_TITULO_US.match(linha)
        if m_us:
            segmentos.append([normalizar_id_us(m_us.group(1)), [linha]])
        elif PADRAO_MODULO.match(linha) or not segmentos:
            segmentos.append([None, [linha]])
        else:
            segmentos[-1][1].append(linha)
    segmentos = [[id_us, "\n".join(linhas).strip()] for id_us, linhas in segmentos]
    return [s for s in segmentos if s[1]]

def historias_por_id(texto: str) -> dict:
    """{US-001: texto da história}; em IDs repetidos vale a primeira ocorrência."""
    historias = {}
    for id_us, bloco in segmentar_backlog(texto):
        if id_us:
            historias.setdefault(id_us, bloco)
    return historias

def _sem_espacos(texto: str) -> str:
    return " ".join(texto.split())

def formatar_historias(texto: str) -> str:
    """Garante uma parte da história por linha: título, Como, quero, para que, Critérios de Aceitação e cada CA.
    O LLM às vezes devolve o título e a história (ou vários CAs) na mesma linha."""
    linhas = []
    for linha in texto.splitlines():
        # Título e "Como ..." na mesma linha
        linha = re.sub(r'^(\W*US-?\s*\d+\s*[-–—:].*?\S)\s+(\**Como\s)', r'\1\n\2', linha, flags=re.IGNORECASE)
        # "... para que X. Critérios de Aceitação: - CA1: ... - CA2: ..."
        linha = re.sub(r'(?<=\S)\s+(\**Critérios de Aceitação\**\s*:)', r'\n\n\1', linha, flags=re.IGNORECASE)
        linha = re.sub(r'(Aceitação\s*:\**)\s+(-?\s*\**CA\s*\d+)', r'\1\n\2', linha, flags=re.IGNORECASE)
        linha = re.sub(r'(?<=[.)])\s+(-?\s*\**CA\s*\d+\s*\**\s*:)', r'\n\1', linha, flags=re.IGNORECASE)
        partes = []
        for parte in linha.split("\n"):
            # "Como ..., quero ..., para que ..." em uma linha só (só na linha do "Como", nunca nos CAs)
            if re.match(r'^\W*Como\s', parte, re.IGNORECASE):
                parte = re.sub(r',\s*(\**quero\s)', r',\n\1', parte, flags=re.IGNORECASE)
                parte = re.sub(r',\s*(\**para que\s)', r',\n\1', parte, flags=re.IGNORECASE)
            partes.append(parte)
        linhas.append("\n".join(partes))
    return "\n".join(linhas)

def markdown_com_quebras(texto: str) -> str:
    """No Markdown, uma quebra simples vira espaço: força a quebra para cada parte ficar na própria linha."""
    return re.sub(r'(?<=\S)\n(?=\S)', '  \n', texto)

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Sandbox de Engenharia de Requisitos Ágeis - UFF",
    page_icon="🎓",
    layout="wide"
)

# ---------------------------------------------------------
# CONFIGURAÇÃO SEGURA DA API KEY
# ---------------------------------------------------------
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    try:
        if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

if not api_key:
    st.error("Chave da OpenAI não configurada. Adicione nos Secrets do Streamlit Cloud ou no arquivo .env local.")
    st.stop()

os.environ["OPENAI_API_KEY"] = api_key

# ---------------------------------------------------------
# EDITOR DE TEMPERATURA (barra lateral)
# ---------------------------------------------------------
TEMPERATURA_PADRAO = 0.0

if "temperatura" not in st.session_state:
    st.session_state["temperatura"] = TEMPERATURA_PADRAO

def restaurar_temperatura():
    st.session_state["temperatura"] = TEMPERATURA_PADRAO

with st.sidebar:
    st.header("⚙️ Configurações do Modelo")
    temperatura = st.slider(
        "🌡️ Temperatura da IA",
        min_value=0.0,
        max_value=2.0,
        step=0.1,
        key="temperatura",
        help="Valores baixos geram respostas mais determinísticas; valores altos, mais criativas e variadas.",
    )
    st.button("↺ Restaurar padrão", on_click=restaurar_temperatura, use_container_width=True)

    if temperatura > 1.0:
        st.warning("Temperaturas acima de 1.0 podem quebrar o formato das seções e da matriz JSON.")
    else:
        st.caption(f"Temperatura atual: **{temperatura:.1f}**")

# Ajustado max_tokens para permitir respostas longas do modelo
llm = ChatOpenAI(model="gpt-4o-mini", temperature=temperatura, openai_api_key=api_key, max_tokens=8012)

def get_response_from_openai(messages):
    return llm.invoke(messages)

def get_text_from_url(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        text = soup.get_text(separator=' ')
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not cleaned_text or len(cleaned_text) < 30:
            return f"Aviso: Não foi possível extrair um texto significativo da URL ({url}). Certifique-se de que o documento está publicado na Web."
            
        return cleaned_text
        
    except Exception as e:
        return f"Erro ao extrair conteúdo da URL ({url}): {str(e)}"


def extrair_notas(tabela: str, maximo: int) -> dict:
    """Lê linhas '| US-001 | 6/7 | Atômica |' e devolve {US-001: (6, 'Atômica')}."""
    notas = {}
    padrao = re.compile(r'^\s*\|?\s*\**(US-?\s*\d+)\**\s*\|\s*(\d+)\s*/\s*%d\s*\|\s*([^|]*)' % maximo, re.IGNORECASE)
    for linha in tabela.splitlines():
        m = padrao.match(linha)
        if m:
            notas[normalizar_id_us(m.group(1))] = (int(m.group(2)), m.group(3).strip() or "Nenhuma")
    return notas

def montar_secao_metricas() -> str:
    """Monta a consolidação e a tabela QUS/INVEST em Python a partir das saídas das ferramentas."""
    qus = extrair_notas(RESULTADOS["qus"], 7)
    invest = extrair_notas(RESULTADOS["invest"], 6)
    ids = sorted(set(qus) | set(invest), key=lambda s: int(s.split("-")[1]))

    if not ids:
        return (
            "⚠️ Não foi possível extrair as notas no formato de tabela. Saídas brutas das ferramentas:\n\n"
            f"**QUS**\n\n{RESULTADOS['qus']}\n\n**INVEST**\n\n{RESULTADOS['invest']}"
        )

    total_qus = sum(nota for nota, _ in qus.values())
    total_invest = sum(nota for nota, _ in invest.values())

    linhas = [
        "#### 1. Consolidação Quantitativa das Métricas Sintáticas e Estruturais",
        f"- MÉTRICAS QUS: {total_qus} / {len(qus) * 7}",
        f"- MÉTRICAS INVEST: {total_invest} / {len(invest) * 6}",
    ]

    no_backlog = ids_no_backlog()
    nao_avaliadas = [i for i in no_backlog if i not in qus or i not in invest]
    if nao_avaliadas:
        linhas.append(
            f"\n⚠️ {len(nao_avaliadas)} de {len(no_backlog)} histórias do backlog não receberam nota QUS e/ou INVEST: "
            + ", ".join(nao_avaliadas)
        )

    linhas += [
        "",
        "#### 2. Relatório de Auditoria Estrutural (QUS e INVEST)",
        "",
        "| User Story | Nota QUS | Falhas QUS | Nota INVEST | Falhas INVEST |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for us in ids:
        nota_q, falha_q = qus.get(us, (None, "-"))
        nota_i, falha_i = invest.get(us, (None, "-"))
        linhas.append(
            f"| {us} | {f'{nota_q}/7' if nota_q is not None else '-'} | {falha_q} "
            f"| {f'{nota_i}/6' if nota_i is not None else '-'} | {falha_i} |"
        )
    return "\n".join(linhas)

def _formatar_total(notas: dict, maximo: int) -> str:
    if not notas:
        return "Não avaliado"
    total, limite = sum(nota for nota, _ in notas.values()), len(notas) * maximo
    return f"{total} / {limite} ({100 * total / limite:.1f}%)"

def totais_qus_invest() -> tuple:
    """Totais atuais do backlog, ex.: ('40 / 49 (81.6%)', '35 / 42 (83.3%)')."""
    return (
        _formatar_total(extrair_notas(RESULTADOS["qus"], 7), 7),
        _formatar_total(extrair_notas(RESULTADOS["invest"], 6), 6),
    )

def calcular_custo(cb) -> float:
    # Preços do gpt-4o-mini por 1M de tokens: US$ 0,15 (entrada) e US$ 0,60 (saída)
    return (cb.prompt_tokens / 1000000) * 0.15 + (cb.completion_tokens / 1000000) * 0.60

def descrever_alteracoes(registro: dict) -> str:
    return (
        f"Alteradas: {', '.join(registro['alterados']) or 'nenhuma'} · "
        f"Criadas: {', '.join(registro['criados']) or 'nenhuma'} · "
        f"Removidas: {', '.join(registro['removidos']) or 'nenhuma'}"
    )

COLUNAS_REFINAMENTO = [
    "ID Execução", "Data/hora", "Instrução", "Histórias antes", "Histórias depois",
    "Alteradas", "Criadas", "Removidas", "QUS antes", "QUS depois", "INVEST antes", "INVEST depois",
    "Temperatura", "Tokens de entrada", "Tokens de saída", "Custo estimado (USD)", "Tempo (s)",
    "Backlog revisado (texto completo)",
]

def linha_refinamento(registro: dict, id_execucao: str) -> list:
    """Uma linha da aba Refinamentos (Google Sheets e .xlsx), na ordem de COLUNAS_REFINAMENTO."""
    custo, tempo = registro.get("custo_usd"), registro.get("tempo_s")
    return [
        id_execucao,
        registro["data_hora"],
        registro["instrucao"],
        registro.get("historias_antes"),
        registro.get("historias_depois"),
        ", ".join(registro["alterados"]),
        ", ".join(registro["criados"]),
        ", ".join(registro["removidos"]),
        registro.get("qus_antes"),
        registro.get("qus_depois"),
        registro.get("invest_antes"),
        registro.get("invest_depois"),
        registro.get("temperatura"),
        registro.get("tokens_entrada"),
        registro.get("tokens_saida"),
        round(custo, 5) if custo is not None else None,
        round(tempo, 2) if tempo is not None else None,
        registro["depois"],
    ]

def tabela_refinamentos(id_execucao: str) -> pd.DataFrame:
    return pd.DataFrame(
        [linha_refinamento(r, id_execucao) for r in RESULTADOS["refinamentos"]],
        columns=COLUNAS_REFINAMENTO,
    )

# --- EXPORTAÇÃO PARA EXCEL ---
def _limpar_markdown(texto: str) -> str:
    return re.sub(r'[*_`#]+', '', texto).strip().rstrip(',').strip()

def estruturar_backlog() -> list:
    """Converte o texto do backlog em linhas (módulo, ID, título, como, quero, para que, critérios)."""
    linhas_saida = []
    modulo_atual = ""
    atual = None

    for linha in backlog_completo().splitlines():
        m_mod = PADRAO_MODULO.match(linha)
        m_us = PADRAO_TITULO_US.match(linha)
        if m_mod:
            modulo_atual = _limpar_markdown(m_mod.group(1))
        elif m_us:
            atual = {
                "Módulo": modulo_atual,
                "ID": normalizar_id_us(m_us.group(1)),
                "Título": _limpar_markdown(m_us.group(2)),
                "Como (Persona)": "",
                "Quero (Ação)": "",
                "Para que (Benefício)": "",
                "Critérios de Aceitação": [],
            }
            linhas_saida.append(atual)
        elif atual is not None:
            texto = _limpar_markdown(linha.lstrip("-* ").strip())
            if re.match(r'^Como\b', texto, re.IGNORECASE):
                atual["Como (Persona)"] = re.sub(r'^Como\s+', '', texto, flags=re.IGNORECASE)
            elif re.match(r'^quero\b', texto, re.IGNORECASE):
                atual["Quero (Ação)"] = re.sub(r'^quero\s+', '', texto, flags=re.IGNORECASE)
            elif re.match(r'^para que\b', texto, re.IGNORECASE):
                atual["Para que (Benefício)"] = re.sub(r'^para que\s+', '', texto, flags=re.IGNORECASE).rstrip('.')
            elif re.match(r'^CA\s*\d+', texto, re.IGNORECASE):
                atual["Critérios de Aceitação"].append(texto)

    for item in linhas_saida:
        item["Critérios de Aceitação"] = "\n".join(item["Critérios de Aceitação"])
    return linhas_saida

def _formatar_aba(planilha, larguras: dict):
    cabecalho = PatternFill("solid", fgColor="1E293B")
    for celula in planilha[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = cabecalho
        celula.alignment = Alignment(vertical="center", wrap_text=True)
    for linha in planilha.iter_rows(min_row=2):
        for celula in linha:
            celula.alignment = Alignment(vertical="top", wrap_text=True)
    for coluna, largura in larguras.items():
        planilha.column_dimensions[coluna].width = largura
    planilha.freeze_panes = "A2"

def montar_tabelas_resultado(info_execucao: dict):
    """Monta as tabelas (backlog, métricas e consolidação) usadas no .xlsx e no Google Sheets."""
    backlog = estruturar_backlog()
    if not backlog:
        # Formato inesperado: exporta o texto bruto para não perder conteúdo
        backlog = [{"Backlog (texto completo)": backlog_completo()}]
    df_backlog = pd.DataFrame(backlog)

    qus = extrair_notas(RESULTADOS["qus"], 7)
    invest = extrair_notas(RESULTADOS["invest"], 6)
    ids = ids_no_backlog()
    df_metricas = pd.DataFrame([
        {
            "ID": us,
            "Nota QUS (0-7)": qus[us][0] if us in qus else None,
            "Falhas QUS": qus[us][1] if us in qus else "Não avaliada",
            "Nota INVEST (0-6)": invest[us][0] if us in invest else None,
            "Falhas INVEST": invest[us][1] if us in invest else "Não avaliada",
        }
        for us in ids
    ])

    total_qus, max_qus = sum(n for n, _ in qus.values()), len(qus) * 7
    total_invest, max_invest = sum(n for n, _ in invest.values()), len(invest) * 6
    nao_avaliadas = [us for us in ids if us not in qus or us not in invest]
    df_consolidacao = pd.DataFrame(
        [
            ("Data/hora da execução", info_execucao["data_hora"]),
            ("Documento de escopo (URL)", info_execucao["url"]),
            ("Modelo", "gpt-4o-mini"),
            ("Temperatura", info_execucao["temperatura"]),
            ("Histórias no backlog", len(ids)),
            ("MÉTRICAS QUS", f"{total_qus} / {max_qus}"),
            ("QUS (%)", round(100 * total_qus / max_qus, 1) if max_qus else None),
            ("MÉTRICAS INVEST", f"{total_invest} / {max_invest}"),
            ("INVEST (%)", round(100 * total_invest / max_invest, 1) if max_invest else None),
            ("Histórias sem nota QUS e/ou INVEST", ", ".join(nao_avaliadas) or "Nenhuma"),
            ("Tempo total (s)", round(info_execucao["tempo_s"], 2)),
            ("Tokens de entrada", info_execucao["tokens_entrada"]),
            ("Tokens de saída", info_execucao["tokens_saida"]),
            ("Custo estimado (USD)", round(info_execucao["custo_usd"], 5)),
        ],
        columns=["Métrica", "Valor"],
    )
    return df_backlog, df_metricas, df_consolidacao

def gerar_xlsx(info_execucao: dict) -> bytes:
    """Gera a planilha com o backlog RAG ancorado, as métricas QUS/INVEST e a consolidação."""
    df_backlog, df_metricas, df_consolidacao = montar_tabelas_resultado(info_execucao)
    # O texto completo do backlog fica de fora: o Excel limita a célula a 32.767 caracteres
    # e a versão atual já está na aba Backlog RAG
    df_refinamentos = tabela_refinamentos(info_execucao.get("id_execucao", "")).drop(
        columns=["Backlog revisado (texto completo)"]
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_backlog.to_excel(writer, sheet_name="Backlog RAG", index=False)
        df_metricas.to_excel(writer, sheet_name="Métricas QUS-INVEST", index=False)
        df_consolidacao.to_excel(writer, sheet_name="Consolidação", index=False)
        df_refinamentos.to_excel(writer, sheet_name="Refinamentos", index=False)

        _formatar_aba(writer.sheets["Backlog RAG"], {"A": 28, "B": 10, "C": 38, "D": 28, "E": 50, "F": 50, "G": 90})
        _formatar_aba(writer.sheets["Métricas QUS-INVEST"], {"A": 10, "B": 15, "C": 35, "D": 17, "E": 35})
        _formatar_aba(writer.sheets["Consolidação"], {"A": 38, "B": 70})
        _formatar_aba(writer.sheets["Refinamentos"], {
            "A": 20, "B": 16, "C": 60, "D": 10, "E": 10, "F": 22, "G": 22, "H": 22,
            "I": 20, "J": 20, "K": 20, "L": 20, "M": 12, "N": 12, "O": 12, "P": 14, "Q": 10,
        })
    return buffer.getvalue()

# --- HISTÓRICO NO GOOGLE SHEETS ---
# Credencial: conta de serviço do Google, em st.secrets["gcp_service_account"] (Streamlit Cloud)
# ou no arquivo indicado por GCP_SERVICE_ACCOUNT_FILE no .env (execução local).
GOOGLE_SHEET_ID_PADRAO = "19od0s2vx4kGmD0r_2LKxWk7_BHiPRWkqGkezN2OTJmU"
LIMITE_CELULA_SHEETS = 49000  # o Google Sheets aceita até 50.000 caracteres por célula

def conectar_google_sheets():
    credencial = None
    try:
        if "gcp_service_account" in st.secrets:
            credencial = dict(st.secrets["gcp_service_account"])
    except Exception:
        pass

    if credencial:
        cliente = gspread.service_account_from_dict(credencial)
    else:
        caminho = (os.getenv("GCP_SERVICE_ACCOUNT_FILE") or "").strip().strip('"').strip("'")
        if not caminho:
            raise RuntimeError(
                "credencial do Google não configurada: a variável GCP_SERVICE_ACCOUNT_FILE não foi encontrada "
                "no .env (confira se o .env está salvo, na pasta do app.py, e reinicie o Streamlit) "
                "nem há gcp_service_account nos Secrets."
            )
        # Caminho relativo é resolvido a partir da pasta do app.py, não da pasta onde o terminal está
        if not os.path.isabs(caminho):
            caminho = os.path.join(diretorio_atual, caminho)
        if not os.path.exists(caminho):
            arquivos_parecidos = [f for f in os.listdir(diretorio_atual) if f.lower().startswith("credenciais")]
            raise RuntimeError(
                f"arquivo de credencial não encontrado em: {caminho}. "
                f"Arquivos 'credenciais*' na pasta do app: {arquivos_parecidos or 'nenhum'}."
            )
        cliente = gspread.service_account(filename=caminho)

    return cliente.open_by_key(os.getenv("GOOGLE_SHEET_ID") or GOOGLE_SHEET_ID_PADRAO)

def _celula(valor):
    if hasattr(valor, "item"):  # tipos numpy -> tipos Python
        valor = valor.item()
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    if isinstance(valor, str) and len(valor) > LIMITE_CELULA_SHEETS:
        return valor[:LIMITE_CELULA_SHEETS] + " …[truncado]"
    return valor

def _obter_aba(planilha, nome: str, cabecalho: list):
    try:
        aba = planilha.worksheet(nome)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome, rows=1000, cols=len(cabecalho))
    if not aba.row_values(1):
        aba.update(range_name="A1", values=[cabecalho])
        aba.freeze(rows=1)
        aba.format("1:1", {"textFormat": {"bold": True}})
    return aba

def _status_cobertura() -> str:
    if not RESULTADOS["lacunas"]:
        return "Não verificada"
    if "COBERTURA_TOTAL_CONFIRMADA" in RESULTADOS["lacunas"][-1]:
        return "Confirmada"
    return f"Lacunas encontradas (última verificação de {len(RESULTADOS['lacunas'])})"

def salvar_no_google_sheets(info_execucao: dict) -> str:
    """Acrescenta a execução atual nas abas Execuções, Histórias e Relatórios. Devolve o ID da execução."""
    df_backlog, df_metricas, df_consolidacao = montar_tabelas_resultado(info_execucao)
    id_execucao = info_execucao.get("id_execucao") or novo_id_execucao()
    data_hora = info_execucao["data_hora"]
    planilha = conectar_google_sheets()

    # Execuções: uma linha por execução, com a consolidação em colunas
    consolidacao = dict(zip(df_consolidacao["Métrica"], df_consolidacao["Valor"]))
    cab_exec = ["ID Execução", *consolidacao.keys(), "Status da cobertura"]
    linha_exec = [id_execucao, *consolidacao.values(), _status_cobertura()]
    _obter_aba(planilha, "Execuções", cab_exec).append_rows(
        [[_celula(v) for v in linha_exec]], value_input_option="RAW"
    )

    # Histórias: uma linha por história, com as notas QUS/INVEST
    df_historias = (
        df_backlog.merge(df_metricas, on="ID", how="left") if "ID" in df_backlog.columns else df_metricas
    )
    cab_hist = ["ID Execução", "Data/hora", *df_historias.columns]
    linhas_hist = [
        [id_execucao, data_hora, *[_celula(v) for v in linha]]
        for linha in df_historias.itertuples(index=False)
    ]
    if linhas_hist:
        _obter_aba(planilha, "Histórias", cab_hist).append_rows(linhas_hist, value_input_option="RAW")

    # Relatórios: textos completos produzidos pelas ferramentas
    cab_rel = ["ID Execução", "Data/hora", "Análise Normativa", "Verificação de Lacunas",
               "Validação Semântica", "Matriz de Cobertura", "Backlog (texto completo)"]
    linha_rel = [
        id_execucao, data_hora,
        RESULTADOS["analise_normativa"],
        "\n\n---\n\n".join(RESULTADOS["lacunas"]),
        RESULTADOS["semantica"],
        RESULTADOS["cobertura"],
        backlog_completo(),
    ]
    _obter_aba(planilha, "Relatórios", cab_rel).append_rows(
        [[_celula(v) for v in linha_rel]], value_input_option="RAW"
    )
    return id_execucao

def novo_id_execucao() -> str:
    return f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"

def salvar_refinamento_no_google_sheets(id_execucao: str, registro: dict):
    """Acrescenta um refinamento na aba Refinamentos, ligado à execução que gerou o backlog."""
    planilha = conectar_google_sheets()
    _obter_aba(planilha, "Refinamentos", COLUNAS_REFINAMENTO).append_rows(
        [[_celula(v) for v in linha_refinamento(registro, id_execucao)]], value_input_option="RAW"
    )

# --- FERRAMENTAS DO AGENTE ---
@tool
def rag_indexing_tool(url: str) -> str:
    """
    Acessa a URL, realiza o chunking do documento e cria a base vetorial FAISS em memória.
    """
    global VECTOR_STORE
    raw_text = get_text_from_url(url)
    
    if raw_text.startswith("Erro") or raw_text.startswith("Aviso"):
        return raw_text

    # Fragmentação adaptativa otimizada
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=120,
        separators=["\n\n", "\n", ".", ";", " "]
    )
    docs = text_splitter.create_documents([raw_text])
    
    # Geração do Vector Store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    VECTOR_STORE = FAISS.from_documents(docs, embeddings)
    
    return f"Indexação RAG concluída com sucesso. Total de {len(docs)} fragmentos processados."

@tool
def normative_analysis_tool(query_escopo: str) -> str:
    """
    Realiza busca vetorial no documento para identificar lacunas normativas, 
    regras ausentes ou contradições antes de gerar os requisitos.
    """
    global VECTOR_STORE
    if not VECTOR_STORE:
        return "Erro: Base vetorial não inicializada. Execute rag_indexing_tool primeiro."

    docs_relevantes = VECTOR_STORE.similarity_search(query_escopo, k=20)
    contexto_recuperado = "\n---\n".join([d.page_content for d in docs_relevantes])

    messages = [
        SystemMessage(content="""
Você é um Engenheiro de Requisitos especialista em Análise Normativa e Auditoria Primária.
Examine o texto recuperado do documento de escopo e identifique:
1. MAPEAMENTO DE MÓDULOS E REQUISITOS (Liste todos os módulos, APIs, telas, chatbots ou fases citadas).
2. REGRAS OMISSAS OU INCOMPLETAS (Ex: regras de validação ausentes, fluxos alternativos não descritos).
3. DÚVIDAS / LACUNAS que precisam de confirmação do analista.
4. CONTRADIÇÕES internas.

Formato da resposta:
# ANÁLISE NORMATIVA E DIAGNÓSTICO DE LACUNAS
## 1. MÓDULOS E ESCOPO MAPEADOS
- [Módulo/Componente X]: [Resumo das funcionalidades esperadas]
## 2. REGRAS IDENTIFICADAS E VALIDADAS
- [Regras confirmadas no texto]
## 3. LACUNAS E OMISSÕES DETECTADAS
- [Ponto Omisso]: [Explicação da ausência e impacto na regra de negócio]
## 4. PERGUNTAS DE REFINAMENTO SUGERIDAS
- [Pergunta objetiva para o Analista/PO sanar a lacuna]
"""),
        HumanMessage(content=f"Contexto Recuperado via RAG:\n{contexto_recuperado}")
    ]
    resposta = get_response_from_openai(messages).content
    RESULTADOS["analise_normativa"] = resposta
    return resposta

# Busca usada na geração; o refinamento repete a mesma busca para manter a numeração dos trechos
# citados em "(Origem: Trecho X)"
CONSULTA_GERACAO = "Módulos, funcionalidades, APIs, Chatbot, Heliasta, Sistema Jurídico Web, regras de negócio e estimativas do projeto"
K_GERACAO = 25

# Formato das histórias, compartilhado pela geração e pelo refinamento
FORMATO_HISTORIA = """FORMATO OBRIGATÓRIO PARA CADA HISTÓRIA:

US-[NÚMERO] - [NOME ESPECÍFICO DA FUNCIONALIDADE]
Como <Persona/Ator>,
quero <Ação Única e Concreta com contexto do negócio>,
para que <Benefício Direto e Métrica/Impacto do negócio>.

Critérios de Aceitação:
- CA1: [Detalhamento concreto da regra, campo, validação ou comportamento] (Origem: Trecho X)
- CA2: [Detalhamento concreto da regra, campo, validação ou comportamento] (Origem: Trecho Y)
"""

@tool
def user_story_rag_generation_tool(payload_contexto: str) -> str:
    """
    Gera um Backlog de Histórias de Usuário exaustivo e atômico,
    garantindo cobertura completa de todos os módulos e regras do documento.
    As histórias geradas são armazenadas automaticamente no backlog compartilhado.
    Em uma segunda chamada, envie em 'payload_contexto' apenas a lista de pendências.
    """
    global VECTOR_STORE
    if not VECTOR_STORE:
        return "Erro: Base vetorial não inicializada."

    docs_relevantes = VECTOR_STORE.similarity_search(CONSULTA_GERACAO, k=K_GERACAO)
    contexto_completo = "\n---\n".join([f"[Trecho {i+1}]: {d.page_content}" for i, d in enumerate(docs_relevantes)])

    # Na rodada de complemento (após a verificação de lacunas), evita repetir histórias e IDs
    instrucao_continuidade = ""
    if RESULTADOS["historias"]:
        existentes = ids_no_backlog()
        proximo = int(existentes[-1].split("-")[1]) + 1 if existentes else 1
        titulos = "\n".join(re.findall(r'US-?\s*\d+\s*-\s*[^\n*]+', backlog_completo(), re.IGNORECASE))
        instrucao_continuidade = (
            f"\n\nHISTÓRIAS JÁ EXISTENTES NO BACKLOG (NÃO repita):\n{titulos}\n\n"
            f"Gere SOMENTE as histórias faltantes, numerando a partir de US-{proximo:03d}."
        )

    prompt_mapeamento = [
        SystemMessage(content="Com base no contexto fornecido, liste TODOS os módulos, APIs, telas e componentes funcionais individualmente que necessitam de User Stories. Seja exaustivo e liste todos sem exceção."),
        HumanMessage(content=contexto_completo)
    ]
    mapa_funcionalidades = get_response_from_openai(prompt_mapeamento).content

    prompt_geracao = [
        SystemMessage(content="""
Você é um Engenheiro de Requisitos Sênior especializado em detalhamento fino de software industrial.
Sua missão é gerar um Backlog de Histórias de Usuário EXAUSTIVO e COMPLETO cobrindo TODOS os módulos identificados no escopo.

EXIGÊNCIAS DE COBERTURA:
- Você DEVE gerar User Stories para TODOS os módulos e componentes mapeados no documento sem omissões.
- Crie quantas histórias (US-001, US-002, ..., US-N) forem necessárias para cobrir 100% do escopo.

EVITE GENERALISMOS:
- CADA História de Usuário DEVE possuir  Critérios de Aceitação (CA) detalhados que cubram o escopo contendo, por exemplo:
  1. Campos obrigatórios/opcionais envolvidos.
  2. Regras de validação, bloqueios ou pré-condições.
  3. Formatos esperados ou comportamentos do sistema em caso de sucesso/erro.

""" + FORMATO_HISTORIA),
        HumanMessage(content=f"MAPEAMENTO DE MÓDULOS OBRIGATÓRIOS:\n{mapa_funcionalidades}\n\nCONTEXTO DO DOCUMENTO DE ESCOPO:\n{contexto_completo}\n\nORIENTAÇÃO ADICIONAL: {payload_contexto}{instrucao_continuidade}")
    ]
    resposta = formatar_historias(get_response_from_openai(prompt_geracao).content)
    RESULTADOS["historias"].append(resposta)

    # O agente recebe só um resumo: o conteúdo completo fica no backlog compartilhado,
    # evitando que ele precise copiar (ou resuma/trunque) as histórias nas próximas chamadas.
    ids_gerados = sorted({normalizar_id_us(m) for m in re.findall(r'US-?\s*\d+', resposta, re.IGNORECASE)})
    return (
        f"Histórias geradas e armazenadas no backlog: {len(ids_gerados)} nesta chamada "
        f"({', '.join(ids_gerados)}). Total no backlog: {len(ids_no_backlog())}. "
        "As próximas ferramentas leem o backlog completo automaticamente."
    )

@tool
def gap_coverage_verification_tool(observacao: str = "") -> str:
    """
    Compara a Análise Normativa (escopo total do documento) com as User Stories JÁ GERADAS.
    Identifica seções, APIs, regras de infraestrutura ou módulos do documento que NÃO possuem histórias associadas.
    Retorna a lista exata do delta (requisitos faltantes) ou 'COBERTURA_TOTAL_CONFIRMADA'.
    A análise normativa e o backlog completo são lidos automaticamente; NÃO copie o conteúdo no argumento.
    """
    payload = (
        f"ANÁLISE NORMATIVA (ESCOPO TOTAL):\n{RESULTADOS['analise_normativa']}\n\n"
        f"BACKLOG DE USER STORIES GERADO ATÉ AGORA:\n{backlog_completo()}"
    )
    messages = [
        SystemMessage(content="""
Você é um Auditor Especialista em Rastreabilidade de Requisitos.
Sua missão é comparar o escopo total extraído do documento com o backlog de User Stories gerado até agora.

Analise atentamente se ficaram de fora:
1. APIs descritas no Roadmap (ex: Criar Caso Não Processual, Agendamentos).
2. Funcionalidades de Infraestrutura/Governança (ex: limitação de tokens LLM, modelos padrão de petição).
3. Recursos de Interface/Sistemas Legados (ex: Login Automático/SSO, visualização de filas no Heliasta).

REGRAS DE RESPOSTA:
- Se houver requisitos/módulos do documento SEM histórias de usuário criadas, liste expressamente cada um deles com detalhes do que deve ser gerado.
- Se 100% dos requisitos do documento estiverem cobertos por histórias, responda ÚNICA e EXCLUSIVAMENTE a frase: "COBERTURA_TOTAL_CONFIRMADA".
"""),
        HumanMessage(content=f"DADOS PARA AUDITORIA DE LACUNAS:\n\n{payload}")
    ]
    resposta = get_response_from_openai(messages).content
    RESULTADOS["lacunas"].append(resposta)
    return resposta

def trechos_para_refinamento(instrucao_usuario: str) -> str:
    """Mesmos trechos da geração (mesma numeração) + os trechos mais ligados à instrução do usuário."""
    if not VECTOR_STORE:
        return ""
    conteudos = [d.page_content for d in VECTOR_STORE.similarity_search(CONSULTA_GERACAO, k=K_GERACAO)]
    for d in VECTOR_STORE.similarity_search(instrucao_usuario, k=10):
        if d.page_content not in conteudos:
            conteudos.append(d.page_content)
    return "\n---\n".join([f"[Trecho {i+1}]: {c}" for i, c in enumerate(conteudos)])

@tool
def user_story_refinement_tool(instrucao_usuario: str) -> str:
    """
    Aplica ao backlog atual as correções ou melhorias pedidas pelo usuário
    (ex.: dividir uma história, detalhar critérios de aceitação, trocar personas).
    Envie em 'instrucao_usuario' a instrução do usuário exatamente como foi escrita.
    O backlog atual é lido automaticamente e a versão revisada substitui o backlog compartilhado.
    """
    if not RESULTADOS["historias"]:
        return "Erro: Não há backlog gerado para refinar. Execute o pipeline principal primeiro."

    backlog_antes = backlog_completo()
    segmentos = segmentar_backlog(backlog_antes)
    historias_antes = historias_por_id(backlog_antes)
    existentes = ids_no_backlog()
    proximo = int(existentes[-1].split("-")[1]) + 1 if existentes else 1

    messages = [
        SystemMessage(content=f"""
Você é um Engenheiro de Requisitos Sênior responsável por REFINAR um Backlog de Histórias de Usuário já existente,
seguindo a instrução do usuário.

REGRAS:
- Aplique SOMENTE o que a instrução pede. NÃO reescreva, melhore ou renumere histórias que a instrução não atinge.
- Mantenha os IDs das histórias alteradas.
- Ao criar histórias novas (inclusive ao dividir uma história), mantenha o ID original na primeira parte
  e numere as novas a partir de US-{proximo:03d}, em sequência.
- Mantenha os critérios de aceitação ancorados no documento: preserve as referências "(Origem: Trecho X)" existentes
  e, em critérios novos ou alterados, cite o trecho do documento que os fundamenta.

""" + FORMATO_HISTORIA + """
FORMATO DA RESPOSTA:
- Devolva, completas e no formato obrigatório, SOMENTE as histórias alteradas ou criadas,
  na ordem em que devem aparecer no backlog.
- NÃO repita histórias que não mudaram: elas são mantidas automaticamente, sem alteração,
  e o backlog completo revisado é montado a partir da sua resposta.
- Se a instrução exigir remover histórias, termine com a linha: REMOVIDAS: US-XXX, US-YYY
- Não escreva nenhum texto antes ou depois das histórias.
"""),
        HumanMessage(content=(
            f"INSTRUÇÃO DO USUÁRIO:\n{instrucao_usuario}\n\n"
            f"BACKLOG ATUAL:\n{backlog_antes}\n\n"
            f"ANÁLISE NORMATIVA DO DOCUMENTO:\n{RESULTADOS['analise_normativa'] or 'Não disponível.'}\n\n"
            f"CONTEXTO DO DOCUMENTO DE ESCOPO:\n{trechos_para_refinamento(instrucao_usuario) or 'Não disponível.'}"
        ))
    ]
    resposta = get_response_from_openai(messages)
    if resposta.response_metadata.get("finish_reason") == "length":
        return ("Erro: a resposta do modelo foi truncada pelo limite de tokens. O backlog NÃO foi alterado; "
                "peça ao usuário uma instrução que atinja menos histórias.")
    texto = formatar_historias(resposta.content)

    removidos = set()
    m_removidas = re.search(r'^\W*REMOVIDAS\s*:\s*(.*)$', texto, re.IGNORECASE | re.MULTILINE)
    if m_removidas:
        removidos = {normalizar_id_us(m) for m in re.findall(r'US-?\s*\d+', m_removidas.group(1), re.IGNORECASE)}
        texto = texto[:m_removidas.start()] + texto[m_removidas.end():]
    revisadas = [s for s in segmentar_backlog(texto) if s[0]]
    removidos = sorted((removidos & set(historias_antes)) - {id_us for id_us, _ in revisadas},
                       key=lambda s: int(s.split("-")[1]))

    # Substitui as histórias revisadas no lugar; as novas entram logo após a anterior da resposta
    # (ex.: a segunda parte de uma história dividida fica ao lado da primeira)
    alterados, criados = [], []
    posicao = None
    for id_us, bloco in revisadas:
        indice = next((i for i, (sid, _) in enumerate(segmentos) if sid == id_us), None)
        if indice is None:
            indice = posicao + 1 if posicao is not None else len(segmentos)
            segmentos.insert(indice, [id_us, bloco])
            criados.append(id_us)
        else:
            if _sem_espacos(segmentos[indice][1]) != _sem_espacos(bloco) and id_us not in alterados:
                alterados.append(id_us)
            segmentos[indice] = [id_us, bloco]
        posicao = indice
    segmentos = [s for s in segmentos if s[0] not in removidos]

    if not (alterados or criados or removidos):
        return "Nenhuma alteração aplicada: o modelo não devolveu histórias diferentes das atuais. O backlog NÃO foi alterado."

    backlog_revisado = "\n\n".join(bloco for _, bloco in segmentos)
    RESULTADOS["historias"] = [backlog_revisado]
    # Só as histórias afetadas perdem as avaliações; as demais mantêm as notas e não são reavaliadas
    descartar_avaliacoes(set(alterados) | set(criados) | set(removidos))
    RESULTADOS["ids_reavaliar"] = list(dict.fromkeys((RESULTADOS["ids_reavaliar"] or []) + alterados + criados))

    registro = {
        "instrucao": instrucao_usuario,
        "antes": backlog_antes,
        "depois": backlog_revisado,
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "alterados": alterados,
        "criados": criados,
        "removidos": removidos,
    }
    RESULTADOS["refinamentos"].append(registro)
    return (
        f"Refinamento aplicado ao backlog. {descrever_alteracoes(registro)}. "
        f"Total no backlog: {len(ids_no_backlog())}. As avaliações das histórias afetadas foram descartadas; "
        "reexecute as avaliações para reavaliar somente elas."
    )

# --- REAVALIAÇÃO PARCIAL (MODO REFINAMENTO) ---
PADRAO_INICIO_US = re.compile(r'^\W*(US-?\s*\d+)\b', re.IGNORECASE)

def _ordenar_ids(ids) -> list:
    return sorted(ids, key=lambda s: int(s.split("-")[1]))

def blocos_por_us(texto: str) -> dict:
    """Divide um relatório por história ({US-001: trecho}); linhas antes da primeira história são ignoradas."""
    blocos = {}
    atual = None
    for linha in texto.splitlines():
        m = PADRAO_INICIO_US.match(linha)
        if m:
            atual = normalizar_id_us(m.group(1))
            blocos.setdefault(atual, [])
        if atual:
            blocos[atual].append(linha)
    return {us: "\n".join(linhas).strip() for us, linhas in blocos.items()}

def tabela_notas(notas: dict, maximo: int) -> str:
    """Reconstrói a tabela '| US-001 | 6/7 | Atômica |' lida por extrair_notas."""
    if not notas:
        return ""
    linhas = ["| User Story | Nota | Falhas |", "| :--- | :--- | :--- |"]
    linhas += [f"| {us} | {notas[us][0]}/{maximo} | {notas[us][1]} |" for us in _ordenar_ids(notas)]
    return "\n".join(linhas)

def descartar_avaliacoes(ids: set):
    """Remove das avaliações as histórias alteradas, criadas ou removidas, mantendo as das demais."""
    for chave, maximo in (("qus", 7), ("invest", 6)):
        notas = extrair_notas(RESULTADOS[chave], maximo)
        RESULTADOS[chave] = tabela_notas({us: v for us, v in notas.items() if us not in ids}, maximo)
    blocos = blocos_por_us(RESULTADOS["semantica"])
    RESULTADOS["semantica"] = "\n\n".join(blocos[us] for us in _ordenar_ids(blocos) if us not in ids)
    # A matriz de cobertura relaciona as regras ao backlog inteiro: é refeita por completo
    RESULTADOS["cobertura"] = ""

def ids_para_reavaliar(anteriores: dict):
    """No modo refinamento, devolve as histórias alteradas/criadas que ainda existem no backlog.
    None = avaliar o backlog completo (pipeline principal ou sem avaliações anteriores para manter)."""
    if RESULTADOS["ids_reavaliar"] is None or not anteriores:
        return None
    existentes = historias_por_id(backlog_completo())
    return [us for us in RESULTADOS["ids_reavaliar"] if us in existentes]

def historias_para_reavaliar(ids: list) -> str:
    historias = historias_por_id(backlog_completo())
    alvo = "\n\n".join(historias[us] for us in ids)
    # Os títulos das demais dão contexto para critérios relativos ao backlog (ex.: Independent, Minimal)
    demais = "\n".join(historias[us].splitlines()[0] for us in historias if us not in ids)
    return (
        f"Avalie SOMENTE as histórias abaixo:\n{alvo}\n\n"
        f"Para referência (NÃO avalie), títulos das demais histórias do backlog:\n{demais}"
    )

def avaliar_notas(chave: str, maximo: int, instrucoes: str, nome: str) -> str:
    """Executa a avaliação QUS/INVEST: backlog completo ou, no modo refinamento, só as histórias alteradas."""
    anteriores = extrair_notas(RESULTADOS[chave], maximo)
    ids = ids_para_reavaliar(anteriores)
    if ids == []:
        return f"Nenhuma história alterada ou criada para reavaliar em {nome}; as notas anteriores foram mantidas."

    entrada = f"Avalie:\n{backlog_completo()}" if ids is None else historias_para_reavaliar(ids)
    messages = [
        SystemMessage(content=instrucoes),
        HumanMessage(content=entrada)
    ]
    resposta = get_response_from_openai(messages).content

    if ids is None:
        RESULTADOS[chave] = resposta
        return f"Avaliação {nome} concluída para {len(extrair_notas(resposta, maximo))} de {len(ids_no_backlog())} histórias."

    novas = {us: v for us, v in extrair_notas(resposta, maximo).items() if us in ids}
    RESULTADOS[chave] = tabela_notas({**anteriores, **novas}, maximo)
    return (
        f"Reavaliação {nome} concluída para {len(novas)} de {len(ids)} histórias alteradas/criadas "
        f"({', '.join(ids)}); as demais mantêm a nota anterior."
    )

def payload_contexto_e_historias(historias: str = None) -> str:
    return (
        f"CONTEXTO (ANÁLISE NORMATIVA DO DOCUMENTO DE ESCOPO):\n{RESULTADOS['analise_normativa']}\n\n"
        f"HISTÓRIAS DE USUÁRIO GERADAS:\n{backlog_completo() if historias is None else historias}"
    )

@tool
def semantic_consistency_tool(observacao: str = "") -> str:
    """
    Auditoria semântica e verificação de aderência de escopo.
    O contexto e o backlog completo são lidos automaticamente; NÃO copie o conteúdo no argumento.
    """
    anteriores = blocos_por_us(RESULTADOS["semantica"])
    ids = ids_para_reavaliar(anteriores)
    if ids == []:
        return "Nenhuma história alterada ou criada para reavaliar semanticamente; a análise anterior foi mantida."
    historias = None
    if ids is not None:
        historias_backlog = historias_por_id(backlog_completo())
        historias = "\n\n".join(historias_backlog[us] for us in ids)

    payload = payload_contexto_e_historias(historias)
    messages = [
        SystemMessage(content="""
Você é um Auditor Semântico de Requisitos.
Sua função é verificar se CADA User Story PERTENCE ao escopo do projeto.
Uma história pode ser perfeitamente escrita (QUS 7/7), mas ser REPROVADA SEMANTICAMENTE por não constar no escopo.

Para cada User Story responda:
US-XX
Status: [APROVADO SEMANTICAMENTE] ou [REPROVADO SEMANTICAMENTE]
Justificativa: Explicar concisamente se a funcionalidade existe no documento de escopo.
"""),
        HumanMessage(content=f"DADOS PARA ANÁLISE SEMÂNTICA:\n\n{payload}")
    ]
    resposta = get_response_from_openai(messages).content
    if ids is None:
        RESULTADOS["semantica"] = resposta
        return "Análise semântica concluída e armazenada para exibição."

    novos = {us: bloco for us, bloco in blocos_por_us(resposta).items() if us in ids}
    blocos = {**anteriores, **novos}
    RESULTADOS["semantica"] = "\n\n".join(blocos[us] for us in _ordenar_ids(blocos))
    return f"Reanálise semântica concluída para {len(novos)} de {len(ids)} histórias alteradas/criadas ({', '.join(ids)})."

@tool
def requirements_coverage_tool(observacao: str = "") -> str:
    """
    Matriz de Rastreabilidade entre regras de escopo e User Stories.
    O contexto e o backlog completo são lidos automaticamente; NÃO copie o conteúdo no argumento.
    """
    payload = payload_contexto_e_historias()
    messages = [
        SystemMessage(content="Retorne SOMENTE um JSON válido com a matriz de rastreabilidade entre todas as regras do escopo e as User Stories geradas."),
        HumanMessage(content=f"DADOS PARA RASTREABILIDADE:\n\n{payload}\n\nFormat: [{{\"Regra\":\"...\", \"UserStory\":\"US-XX\", \"Observacao\":\"...\"}}]")
    ]
    resposta = get_response_from_openai(messages).content
    RESULTADOS["cobertura"] = resposta
    return "Matriz de rastreabilidade concluída e armazenada para exibição."

FORMATO_TABELA_AVALIACAO = """

FORMATO OBRIGATÓRIO DA RESPOSTA: somente uma tabela Markdown, uma linha por história, avaliando TODAS as histórias recebidas, sem texto antes ou depois:
| User Story | Nota | Falhas |
| :--- | :--- | :--- |
| US-001 | {exemplo} | {falha_exemplo} |
Use 'Nenhuma' na coluna Falhas quando a nota for máxima."""

@tool
def quality_assessment_tool(observacao: str = "") -> str:
    """
    Avaliação estritamente estrutural/sintática no framework QUS (7 dimensões).
    O backlog completo é lido automaticamente; NÃO copie as histórias no argumento.
    """
    return avaliar_notas("qus", 7, """Você é um auditor do framework QUS (Quality of User Stories).
Avalie cada história em 7 critérios binários (1/0):
1. Bem-formada (Well-formed)
2. Atômica (Atomic)
3. Conceitualmente Sólida (Conceptually Sound)
4. Inambígua (Unambiguous)
5. Mínima (Minimal)
6. Sentença Completa (Full Sentence)
7. Estimável (Estimable)

SE A NOTA FOR MENOR QUE 7, VOCÊ É OBRIGADO A NOMEAR EXATAMENTE QUAIS CRITÉRIOS FALHARAM.
Exemplo para nota 6/7: "Falha: Atômica". NUNCA omita a justificativa da perda de ponto.""" + FORMATO_TABELA_AVALIACAO.format(exemplo="6/7", falha_exemplo="Atômica"), "QUS")

@tool
def invest_assessment_tool(observacao: str = "") -> str:
    """
    Avaliação de viabilidade ágil no acrônimo INVEST (6 dimensões).
    O backlog completo é lido automaticamente; NÃO copie as histórias no argumento.
    """
    return avaliar_notas("invest", 6, """Você é um Agile Coach especialista em INVEST.
Avalie cada história em 6 critérios binários (1/0):
1. Independent
2. Negotiable
3. Valuable
4. Estimable
5. Small
6. Testable

SE A NOTA FOR MENOR QUE 6, VOCÊ É OBRIGADO A NOMEAR EXATAMENTE QUAIS CRITÉRIOS FALHARAM.
Exemplo para nota 5/6: "Falha: Small". NUNCA omita a justificativa da perda de ponto.""" + FORMATO_TABELA_AVALIACAO.format(exemplo="5/6", falha_exemplo="Small"), "INVEST")

# --- CONFIGURAÇÃO DO AGENTE E PROMPT ---
# CORREÇÃO: Adicionado 'gap_coverage_verification_tool' à lista de ferramentas
toolkit = [
    rag_indexing_tool,
    normative_analysis_tool,
    user_story_rag_generation_tool,
    gap_coverage_verification_tool,
    semantic_consistency_tool, 
    requirements_coverage_tool, 
    quality_assessment_tool, 
    invest_assessment_tool
]

prompt = ChatPromptTemplate.from_messages([
    ("system", """
Você é um Engenheiro de Software automatizado especialista em Engenharia de Requisitos com suporte a RAG.

IMPORTANTE: as ferramentas compartilham os resultados automaticamente. A análise normativa e TODAS as histórias
geradas ficam armazenadas e são lidas diretamente pelas ferramentas de verificação e avaliação.
NUNCA copie histórias, critérios de aceitação ou relatórios nos argumentos das ferramentas.

Instruções estritas do fluxo com ancoragem e análise de lacunas:

1. Execute 'rag_indexing_tool' enviando a URL informada para vetorizar o documento.
   - SE retornar erro de acesso ao documento, PARE e informe o erro ao usuário.
2. Execute 'normative_analysis_tool' com a busca das principais regras, módulos e personas do projeto para gerar o relatório de lacunas.
3. Execute 'user_story_rag_generation_tool' para gerar o backlog COMPLETO cobrindo TODOS os módulos mapeados na análise normativa.
4. PASSO DE GARANTIA DE COBERTURA 100%:
   - Execute 'gap_coverage_verification_tool'.
   - SE o retorno for 'COBERTURA_TOTAL_CONFIRMADA', avance para o Passo 5.
   - SE a ferramenta listar requisitos/módulos FALTANTES, execute novamente 'user_story_rag_generation_tool' passando em 'payload_contexto' somente a lista de pendências.
   - Faça no máximo UMA rodada de complemento; depois avance para o Passo 5.
5. Os passos a seguir são independentes: chame as quatro ferramentas JUNTAS, na mesma resposta:
   'semantic_consistency_tool', 'requirements_coverage_tool', 'quality_assessment_tool' e 'invest_assessment_tool'.

Ao final, responda APENAS com um resumo curto (no máximo 3 linhas): quantas histórias foram geradas e se a cobertura total foi confirmada.
NÃO reproduza histórias, tabelas ou relatórios na resposta final: a interface exibe os resultados das ferramentas diretamente.
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, toolkit, prompt)
agent_executor = AgentExecutor(agent=agent, tools=toolkit, verbose=True, max_iterations=15)

# --- AGENTE DO MODO REFINAMENTO ---
# Toolkit próprio: sem indexação, análise normativa e geração, que não devem ser reexecutadas
toolkit_refinamento = [
    user_story_refinement_tool,
    semantic_consistency_tool,
    requirements_coverage_tool,
    quality_assessment_tool,
    invest_assessment_tool,
]

prompt_refinamento = ChatPromptTemplate.from_messages([
    ("system", """
Você é um Engenheiro de Software automatizado especialista em Engenharia de Requisitos com suporte a RAG.
O backlog de histórias JÁ FOI GERADO e avaliado. Você está no MODO REFINAMENTO: o usuário pediu correções ou melhorias.

IMPORTANTE: as ferramentas compartilham os resultados automaticamente. O backlog atual, a análise normativa e o
documento indexado são lidos diretamente pelas ferramentas.
NUNCA copie histórias, critérios de aceitação ou relatórios nos argumentos das ferramentas.

Instruções estritas do fluxo de refinamento:

1. Execute 'user_story_refinement_tool' enviando em 'instrucao_usuario' a instrução do usuário EXATAMENTE como foi escrita.
   - SE retornar erro ou informar que nenhuma alteração foi aplicada, PARE e informe o motivo ao usuário.
2. Para reavaliar o backlog corrigido, chame as quatro ferramentas JUNTAS, na mesma resposta:
   'semantic_consistency_tool', 'requirements_coverage_tool', 'quality_assessment_tool' e 'invest_assessment_tool'.
   As avaliações semântica, QUS e INVEST reavaliam automaticamente SOMENTE as histórias alteradas ou criadas;
   a matriz de cobertura é refeita para o backlog inteiro.

Ao final, responda APENAS com um resumo curto (no máximo 3 linhas): quais histórias foram alteradas, criadas ou removidas
e quais foram reavaliadas.
NÃO reproduza histórias, tabelas ou relatórios na resposta final: a interface exibe os resultados das ferramentas diretamente.
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent_refinamento = create_openai_tools_agent(llm, toolkit_refinamento, prompt_refinamento)
agent_executor_refinamento = AgentExecutor(
    agent=agent_refinamento, tools=toolkit_refinamento, verbose=True, max_iterations=6
)

# --- ACOMPANHAMENTO EM TEMPO REAL ---
class PipelineProgressHandler(BaseCallbackHandler):
    """
    Exibe na tela cada passo do agente com o tempo gasto:
    - chamadas das ferramentas (entrada e saída resumidas);
    - chamadas do LLM orquestrador entre as ferramentas ("agente decidindo/escrevendo").
    """

    LIMITE_PREVIA = 1500

    def __init__(self, container):
        self.container = container
        self.passo = 0
        self.ferramenta_ativa = None
        self.agente_ativo = None

    def _previa(self, texto) -> str:
        texto = str(texto)
        if len(texto) > self.LIMITE_PREVIA:
            return texto[: self.LIMITE_PREVIA] + f"\n\n… ({len(texto)} caracteres no total)"
        return texto

    def on_llm_start(self, serialized, prompts, **kwargs):
        # Chamadas internas das ferramentas não entram aqui como passo separado
        if self.ferramenta_ativa is None:
            self.passo += 1
            status = self.container.status(f"🧠 {self.passo}. Agente decidindo o próximo passo...", expanded=False)
            self.agente_ativo = (status, time.time(), self.passo)

    on_chat_model_start = on_llm_start

    def on_llm_end(self, response, **kwargs):
        if self.agente_ativo is not None and self.ferramenta_ativa is None:
            status, inicio, passo = self.agente_ativo
            tokens_saida = (response.llm_output or {}).get("token_usage", {}).get("completion_tokens")
            info_tokens = f" · {tokens_saida} tokens escritos" if tokens_saida else ""
            status.update(
                label=f"🧠 {passo}. Agente decidiu o próximo passo — {time.time() - inicio:.1f}s{info_tokens}",
                state="complete",
            )
            self.agente_ativo = None

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.passo += 1
        nome = (serialized or {}).get("name", "ferramenta")
        status = self.container.status(f"⏳ {self.passo}. Executando {nome}...", expanded=True)
        status.caption(f"Entrada enviada pelo agente ({len(str(input_str))} caracteres):")
        status.code(self._previa(input_str), language=None)
        self.ferramenta_ativa = (status, time.time(), self.passo, nome)

    def on_tool_end(self, output, **kwargs):
        if self.ferramenta_ativa is None:
            return
        status, inicio, passo, nome = self.ferramenta_ativa
        status.caption(f"Saída da ferramenta ({len(str(output))} caracteres):")
        status.code(self._previa(output), language=None)
        status.update(label=f"✅ {passo}. {nome} — {time.time() - inicio:.1f}s", state="complete", expanded=False)
        self.ferramenta_ativa = None

    def on_tool_error(self, error, **kwargs):
        if self.ferramenta_ativa is None:
            return
        status, inicio, passo, nome = self.ferramenta_ativa
        status.error(str(error))
        status.update(label=f"❌ {passo}. {nome} — erro após {time.time() - inicio:.1f}s", state="error")
        self.ferramenta_ativa = None

# --- INTERFACE DO STREAMLIT ---

def renderizar_historico_refinamentos():
    with st.expander(f"Histórico de refinamentos ({len(RESULTADOS['refinamentos'])})"):
        for i, registro in enumerate(RESULTADOS["refinamentos"], start=1):
            st.markdown(f"**{i}. {registro['data_hora']}** — _{registro['instrucao']}_")
            st.caption(descrever_alteracoes(registro))
            antes = historias_por_id(registro["antes"])
            depois = historias_por_id(registro["depois"])
            for id_us in registro["alterados"] + registro["criados"] + registro["removidos"]:
                col_antes, col_depois = st.columns(2)
                with col_antes:
                    st.markdown(f"**Antes — {id_us}**")
                    st.markdown(markdown_com_quebras(antes.get(id_us, "_(não existia)_")))
                with col_depois:
                    st.markdown(f"**Depois — {id_us}**")
                    st.markdown(markdown_com_quebras(depois.get(id_us, "_(removida)_")))
            st.markdown("---")

def renderizar_refinamento(info_execucao: dict):
    st.subheader("✏️ Refinar histórias")
    instrucao_refinamento = st.text_area(
        "Descreva o que deve ser corrigido ou melhorado",
        key="instrucao_refinamento",
        placeholder="Ex.: divida a US-004 em duas; detalhe os critérios de aceitação da US-010; troque a persona 'usuário' por 'advogado'",
    )
    st.caption("Pressione Ctrl+Enter ou clique fora da caixa para habilitar o botão.")
    if st.button(
        "🔁 Reprocessar com este prompt",
        use_container_width=True,
        disabled=not RESULTADOS["historias"] or not instrucao_refinamento.strip(),
    ):
        executar_refinamento(instrucao_refinamento.strip(), info_execucao)

def renderizar_resultados(info_execucao: dict):
    """Exibe a exportação e as abas de resultado a partir de RESULTADOS (chamada em todo rerun)."""
    # Reservado no topo, mas preenchido no fim: um refinamento feito neste rerun já entra no .xlsx
    area_download = st.container()

    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Análise Normativa & Lacunas",
        "📌 Backlog Ancorado (RAG)",
        "📊 Métricas de Qualidade (QUS/INVEST)",
        "🔍 Validação Semântica & Cobertura",
        "⚡ Desempenho & Recursos"
    ])

    with tab0:
        st.header("📋 Análise Normativa e Detecção de Omissões no Documento")
        conteudo_normativa = RESULTADOS["analise_normativa"] or "_A análise normativa não foi executada._"
        st.markdown(conteudo_normativa.strip())
        for i, relatorio_lacunas in enumerate(RESULTADOS["lacunas"], start=1):
            with st.expander(f"Verificação de lacunas — rodada {i}"):
                st.markdown(relatorio_lacunas)
    with tab1:
        st.header("📌 Backlog de User Stories Gerado")
        # O backlog fica acima do refinamento, mas só é desenhado depois dele: um refinamento
        # feito neste rerun já aparece no backlog e nas demais abas
        area_backlog = st.container()
        st.markdown("---")
        renderizar_refinamento(info_execucao)
        with area_backlog:
            st.caption(f"{len(ids_no_backlog())} histórias no backlog")
            if RESULTADOS["refinamentos"]:
                renderizar_historico_refinamentos()
            conteudo_us = backlog_completo() or "_Nenhuma história gerada._"
            st.markdown(markdown_com_quebras(formatar_historias(conteudo_us.strip())))

    conteudo_metricas = montar_secao_metricas() if (RESULTADOS["qus"] or RESULTADOS["invest"]) else "_As avaliações QUS/INVEST não foram executadas._"
    conteudo_semantica = RESULTADOS["semantica"] or "_A validação semântica não foi executada._"
    conteudo_cobertura = RESULTADOS["cobertura"]

    with tab2:
        st.header("📊 Métricas e Auditoria Qualitativa (Estrutura e Sintaxe)")
        st.markdown(conteudo_metricas.strip())

    with tab3:
        st.header("🔍 Relatório do Avaliador (Aderência de Escopo e Semântica)")
        st.markdown(
            """
            <style>
            section[data-testid="stMarkdownContainer"] table { width: 100%; }
            section[data-testid="stMarkdownContainer"] th { background-color: #1E293B; color: white; text-align: center; }
            section[data-testid="stMarkdownContainer"] td { vertical-align: top; white-space: pre-wrap; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### 1. Relatório de Validação de Domínio e Nexo Semântico")
        st.markdown(conteudo_semantica.strip())

        st.markdown("#### 2. Matriz de Cobertura de Requisitos")
        if not conteudo_cobertura:
            st.markdown("_A matriz de cobertura não foi executada._")
        else:
            try:
                json_limpo = re.sub(r'^```(?:json)?\s*|\s*```$', '', conteudo_cobertura.strip())
                st.dataframe(json.loads(json_limpo), use_container_width=True)
            except ValueError:
                st.markdown(conteudo_cobertura)

    with tab4:
        st.header("⚡ Desempenho Técnico do Pipeline")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="⏱ Tempo Total de Execução", value=f"{info_execucao['tempo_s']:.2f} s")
            st.metric(label="💾 Consumo de Memória de Pico", value=f"{info_execucao['memoria_pico_mb']:.2f} MB")

        with col2:
            st.metric(label="📥 Tokens de Entrada (Prompt)", value=f"{info_execucao['tokens_entrada']}")
            st.metric(label="📤 Tokens de Saída (Completion)", value=f"{info_execucao['tokens_saida']}")

        with col3:
            st.metric(label="🔢 Total de Tokens", value=f"{info_execucao['tokens_total']}")
            st.metric(label="💵 Custo Real (gpt-4o-mini)", value=f"${info_execucao['custo_usd']:.5f} USD")
            st.metric(label="🌡️ Temperatura Utilizada", value=f"{info_execucao['temperatura']:.1f}")

        if RESULTADOS["refinamentos"]:
            st.markdown("#### 🔁 Refinamentos")
            colunas = ["Data/hora", "Instrução", "Histórias antes", "Histórias depois", "QUS antes", "QUS depois",
                       "INVEST antes", "INVEST depois", "Tokens de entrada", "Tokens de saída",
                       "Custo estimado (USD)", "Tempo (s)"]
            st.dataframe(
                tabela_refinamentos(info_execucao.get("id_execucao", ""))[colunas],
                use_container_width=True,
                hide_index=True,
            )

    if RESULTADOS["historias"]:
        with area_download:
            st.download_button(
                "📥 Exportar Backlog RAG e Métricas de Qualidade (.xlsx)",
                data=gerar_xlsx(info_execucao),
                file_name=f"backlog_metricas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                on_click="ignore",  # não reexecuta o app: os resultados continuam na tela após o download
                use_container_width=True,
            )

def executar_refinamento(instrucao: str, info_execucao: dict):
    """Executa o agente no modo refinamento e registra o resultado (histórico e Google Sheets)."""
    total_refinamentos = len(RESULTADOS["refinamentos"])
    historias_antes = len(ids_no_backlog())
    qus_antes, invest_antes = totais_qus_invest()
    tempo_inicial = time.time()

    st.markdown("#### 🛰️ Refinamento em tempo real")
    st_callback = PipelineProgressHandler(st.container())

    with st.spinner("O Agente está aplicando as correções e reavaliando o backlog... Aguarde."):
        with get_openai_callback() as cb:
            try:
                result = agent_executor_refinamento.invoke(
                    {
                        "input": (
                            "Refine o backlog atual conforme a instrução do usuário abaixo e reavalie as métricas "
                            f"semântica, de cobertura, QUS e INVEST.\n\nINSTRUÇÃO DO USUÁRIO:\n{instrucao}"
                        )
                    },
                    config={"callbacks": [st_callback]},
                )
            except Exception as e:
                st.error(f"Ocorreu um erro durante o refinamento: {e}")
                if len(RESULTADOS["refinamentos"]) > total_refinamentos:
                    st.warning("O backlog foi alterado, mas as métricas podem não ter sido recalculadas.")
                return
            finally:
                # Volta ao modo normal: as próximas avaliações consideram o backlog completo
                RESULTADOS["ids_reavaliar"] = None

    novos = RESULTADOS["refinamentos"][total_refinamentos:]
    if not novos:
        st.warning(f"Nenhuma alteração foi aplicada ao backlog. Resposta do agente:\n\n{result['output']}")
        return

    qus_depois, invest_depois = totais_qus_invest()
    registro = novos[-1]
    registro.update({
        "historias_antes": historias_antes,
        "historias_depois": len(ids_no_backlog()),
        "qus_antes": qus_antes,
        "qus_depois": qus_depois,
        "invest_antes": invest_antes,
        "invest_depois": invest_depois,
        "temperatura": temperatura,
        "tokens_entrada": cb.prompt_tokens,
        "tokens_saida": cb.completion_tokens,
        "custo_usd": calcular_custo(cb),
        "tempo_s": time.time() - tempo_inicial,
    })
    st.success(f"Refinamento concluído! {result['output']}")

    # Histórico automático: falhas aqui não interrompem a exibição dos resultados
    try:
        with st.spinner("Salvando o refinamento no Google Sheets..."):
            salvar_refinamento_no_google_sheets(info_execucao.get("id_execucao", ""), registro)
        st.info("📚 Refinamento salvo no Google Sheets (aba Refinamentos).")
    except Exception as erro_sheets:
        st.warning(f"Não foi possível salvar o refinamento no Google Sheets: {erro_sheets}")

st.title("Geração de Histórias de Usuário - UFF")
st.subheader("Agentes Multi-Ferramentas")
st.markdown("---")

url_padrao = "https://docs.google.com/document/d/e/2PACX-1vTwj4Yh9UVPzqEpHJMprp875O7bW6XRQek_JNl-1ZxriLWvXvWInIxlxaYY4-yTRRTvxNIvUSPkuFbm/pub"
url_documento = st.text_input("Cole aqui a URL pública do documento de escopo (Google Docs publicado na Web ou site):", value=url_padrao)

if st.button("🚀 Iniciar Pipeline de IA", use_container_width=True):
    tracemalloc.start()
    tempo_inicial = time.time()

    # Acompanhamento em tempo real: cada ferramenta chamada pelo agente aparece abaixo com entrada e saída
    st.markdown("#### 🛰️ Execução em tempo real")
    st_callback = PipelineProgressHandler(st.container())
    novo_estado_execucao()
    VECTOR_STORE = None
    st.session_state.pop("vector_store", None)
    st.session_state.pop("info_execucao", None)

    with st.spinner("O Agente está processando o documento, mapeando todos os módulos e gerando o backlog completo... Aguarde."):
        with get_openai_callback() as cb:
            try:
                result = agent_executor.invoke(
                    {
                        "input": f"Execute todo o pipeline de engenharia de requisitos com auditoria semântica, de cobertura, QUS e INVEST para o projeto em: {url_documento}"
                    },
                    config={"callbacks": [st_callback]},
                )

                tempo_final = time.time()
                memoria_atual, memoria_pico = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                # Guardados para os próximos reruns (refinamento, troca de aba, download)
                st.session_state["vector_store"] = VECTOR_STORE
                info_execucao = {
                    "id_execucao": novo_id_execucao(),
                    "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "url": url_documento,
                    "temperatura": temperatura,
                    "tempo_s": tempo_final - tempo_inicial,
                    "memoria_pico_mb": memoria_pico / (1024 * 1024),
                    "tokens_entrada": cb.prompt_tokens,
                    "tokens_saida": cb.completion_tokens,
                    "tokens_total": cb.total_tokens,
                    "custo_usd": calcular_custo(cb),
                }
                st.session_state["info_execucao"] = info_execucao

                # Os conteúdos vêm direto das ferramentas (RESULTADOS), não da resposta final do agente
                if not RESULTADOS["historias"]:
                    st.warning(f"O pipeline terminou sem gerar histórias. Resposta do agente:\n\n{result['output']}")
                else:
                    st.success(f"Processamento Concluído com Sucesso! {result['output']}")

                    # Histórico automático: falhas aqui não interrompem a exibição dos resultados
                    try:
                        with st.spinner("Salvando o resultado no Google Sheets..."):
                            id_execucao = salvar_no_google_sheets(info_execucao)
                        st.info(f"📚 Resultado salvo no Google Sheets (execução {id_execucao}).")
                    except Exception as erro_sheets:
                        st.warning(f"Não foi possível salvar no Google Sheets: {erro_sheets}")

            except Exception as e:
                st.error(f"Ocorreu um erro durante a execução do agente: {e}")

# Resultados ficam fora do if do botão para continuarem na tela em qualquer rerun
# (o refinamento fica dentro da aba do backlog)
if "info_execucao" in st.session_state:
    renderizar_resultados(st.session_state["info_execucao"])
