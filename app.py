from typing import TypedDict, Literal, Optional, List, Dict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from datetime import datetime
from uuid import uuid4
import time
import os

load_dotenv()

# ===========================
# 1. DEFINIÇÕES DE ESTADO ENRIQUECIDAS
# ===========================

class LogDecisao(TypedDict):
    """Log detalhado de cada decisão do agente"""
    iteracao: int
    timestamp: str
    acao: str  # "redator" ou "revisor"
    entrada: str
    saida: str
    tokens_usados: Optional[int]
    tempo_execucao: float

class MetadataModelo(TypedDict):
    """Metadados sobre o modelo LLM usado"""
    modelo_id: str
    temperatura: float
    max_tokens: int
    versao: str

class EstadoEnriquecido(TypedDict):
    # Campos originais
    tema: str
    rascunho: str
    critica: Optional[str]
    aprovado: bool

    # Novos campos de rastreamento empresarial
    request_id: str
    timestamp_inicio: str
    timestamp_fim: Optional[str]
    iteracao_atual: int
    logs_decisao: List[LogDecisao]
    metadata_modelo: MetadataModelo
    historico_rascunhos: List[str]
    historico_criticas: List[str]
    tempo_total_execucao: Optional[float]

# ===========================
# 2. INICIALIZAÇÃO DO MODELO
# ===========================

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    temperature=0.7,
    max_tokens=2000
)

# Prompts do sistema (para referência no Prompt Lab)
PROMPT_REDATOR = """És um redator profissional.
Escreve um post curto sobre: {tema}.
Crítica anterior para melhorar: {critica}.
Responde APENAS com o texto do post."""

PROMPT_REVISOR = """És um editor rigoroso. Avalia este post:
'{rascunho}'

Se o post for excelente, responde apenas com a palavra 'APROVADO'.
Se precisar de melhorias, escreve uma crítica curta começando com 'CRÍTICA:'."""

# ===========================
# 3. FUNÇÕES DE NÓS COM TRACKING
# ===========================

def redator(state: EstadoEnriquecido) -> Dict:
    """
    Nó Redator: Gera ou melhora o rascunho com base no tema e críticas anteriores.
    Adiciona tracking completo de execução.
    """
    print(f"--- NÓ: REDATOR (Iteração {state['iteracao_atual']}) ---")

    # Timestamp de início da execução deste nó
    inicio_execucao = time.time()
    timestamp_atual = datetime.now().isoformat()

    # Preparar entrada
    tema = state["tema"]
    critica = state.get("critica", "Nenhuma")

    prompt = PROMPT_REDATOR.format(tema=tema, critica=critica)

    # Executar LLM
    resposta = llm.invoke(prompt)
    novo_rascunho = resposta.content

    # Calcular tempo de execução
    tempo_execucao = time.time() - inicio_execucao

    # Estimativa de tokens (aproximação baseada em caracteres)
    # Nota: Para contagem precisa, usar callbacks do LangChain
    tokens_entrada_estimados = len(prompt) // 4
    tokens_saida_estimados = len(novo_rascunho) // 4
    tokens_totais = tokens_entrada_estimados + tokens_saida_estimados

    # Criar log de decisão
    log_decisao: LogDecisao = {
        "iteracao": state["iteracao_atual"],
        "timestamp": timestamp_atual,
        "acao": "redator",
        "entrada": f"Tema: {tema}\nCrítica: {critica}",
        "saida": novo_rascunho,
        "tokens_usados": tokens_totais,
        "tempo_execucao": tempo_execucao
    }

    # Atualizar históricos
    historico_rascunhos = state.get("historico_rascunhos", []).copy()
    historico_rascunhos.append(novo_rascunho)

    logs_decisao = state.get("logs_decisao", []).copy()
    logs_decisao.append(log_decisao)

    print(f"✍️ Redator completou em {tempo_execucao:.2f}s ({tokens_totais} tokens)")

    return {
        "rascunho": novo_rascunho,
        "aprovado": False,
        "logs_decisao": logs_decisao,
        "historico_rascunhos": historico_rascunhos,
        "iteracao_atual": state["iteracao_atual"] + 1
    }

def revisor(state: EstadoEnriquecido) -> Dict:
    """
    Nó Revisor: Avalia o rascunho e decide aprovar ou criticar.
    Adiciona tracking completo de execução.
    """
    print(f"--- NÓ: REVISOR (Iteração {state['iteracao_atual']}) ---")

    # Timestamp de início da execução deste nó
    inicio_execucao = time.time()
    timestamp_atual = datetime.now().isoformat()

    # Preparar entrada
    rascunho = state["rascunho"]

    prompt = PROMPT_REVISOR.format(rascunho=rascunho)

    # Executar LLM
    resposta = llm.invoke(prompt)
    conteudo_resposta = resposta.content
    conteudo_upper = conteudo_resposta.upper()

    # Calcular tempo de execução
    tempo_execucao = time.time() - inicio_execucao

    # Estimativa de tokens
    tokens_entrada_estimados = len(prompt) // 4
    tokens_saida_estimados = len(conteudo_resposta) // 4
    tokens_totais = tokens_entrada_estimados + tokens_saida_estimados

    # Determinar aprovação
    aprovado = "APROVADO" in conteudo_upper
    critica_final = "Excelente!" if aprovado else conteudo_resposta

    # Criar log de decisão
    log_decisao: LogDecisao = {
        "iteracao": state["iteracao_atual"],
        "timestamp": timestamp_atual,
        "acao": "revisor",
        "entrada": f"Rascunho a avaliar:\n{rascunho}",
        "saida": conteudo_resposta,
        "tokens_usados": tokens_totais,
        "tempo_execucao": tempo_execucao
    }

    # Atualizar históricos
    historico_criticas = state.get("historico_criticas", []).copy()
    historico_criticas.append(critica_final)

    logs_decisao = state.get("logs_decisao", []).copy()
    logs_decisao.append(log_decisao)

    status_emoji = "✅" if aprovado else "⚠️"
    print(f"{status_emoji} Revisor completou em {tempo_execucao:.2f}s - {'APROVADO' if aprovado else 'PRECISA REVISÃO'}")

    return {
        "aprovado": aprovado,
        "critica": critica_final,
        "logs_decisao": logs_decisao,
        "historico_criticas": historico_criticas
    }

# ===========================
# 4. ARESTA CONDICIONAL
# ===========================

def decidir_proximo_passo(state: EstadoEnriquecido):
    """
    Decide se o conteúdo está aprovado (END) ou precisa de mais iterações (redator).
    """
    if state["aprovado"]:
        print("🎯 Conteúdo APROVADO - Finalizando workflow")
        return END
    print("🔄 Conteúdo precisa de revisão - Voltando ao Redator")
    return "redator"

# ===========================
# 5. MONTAGEM DO GRAFO
# ===========================

workflow = StateGraph(EstadoEnriquecido)

# Adicionar nós
workflow.add_node("redator", redator)
workflow.add_node("revisor", revisor)

# Definir ponto de entrada
workflow.set_entry_point("redator")

# Adicionar arestas
workflow.add_edge("redator", "revisor")
workflow.add_conditional_edges(
    "revisor",
    decidir_proximo_passo,
    {END: END, "redator": "redator"}
)

# Compilar grafo
app = workflow.compile()

# ===========================
# 6. FUNÇÕES AUXILIARES
# ===========================

def criar_estado_inicial(tema: str) -> EstadoEnriquecido:
    """
    Cria o estado inicial enriquecido para uma nova execução.
    """
    request_id = str(uuid4())
    timestamp_inicio = datetime.now().isoformat()

    metadata_modelo: MetadataModelo = {
        "modelo_id": "claude-sonnet-4-6",
        "temperatura": 0.7,
        "max_tokens": 2000,
        "versao": "anthropic-2024"
    }

    estado_inicial: EstadoEnriquecido = {
        # Campos originais
        "tema": tema,
        "rascunho": "",
        "critica": None,
        "aprovado": False,

        # Tracking fields
        "request_id": request_id,
        "timestamp_inicio": timestamp_inicio,
        "timestamp_fim": None,
        "iteracao_atual": 1,
        "logs_decisao": [],
        "metadata_modelo": metadata_modelo,
        "historico_rascunhos": [],
        "historico_criticas": [],
        "tempo_total_execucao": None
    }

    print(f"🆔 Request ID: {request_id}")
    print(f"⏰ Início: {timestamp_inicio}")

    return estado_inicial

def finalizar_estado(estado: EstadoEnriquecido) -> EstadoEnriquecido:
    """
    Finaliza o estado calculando métricas finais.
    """
    timestamp_fim = datetime.now().isoformat()

    # Calcular tempo total
    inicio = datetime.fromisoformat(estado["timestamp_inicio"])
    fim = datetime.fromisoformat(timestamp_fim)
    tempo_total = (fim - inicio).total_seconds()

    estado["timestamp_fim"] = timestamp_fim
    estado["tempo_total_execucao"] = tempo_total

    print(f"⏱️ Tempo total de execução: {tempo_total:.2f}s")
    print(f"🔄 Total de iterações: {len(estado['historico_rascunhos'])}")

    return estado

def obter_prompts_sistema() -> Dict[str, str]:
    """
    Retorna os prompts do sistema para visualização no Prompt Lab.
    """
    return {
        "redator": PROMPT_REDATOR,
        "revisor": PROMPT_REVISOR
    }

# ===========================
# 7. FUNÇÃO DE EXECUÇÃO PRINCIPAL
# ===========================

def executar_workflow(tema: str) -> EstadoEnriquecido:
    """
    Executa o workflow completo com tracking empresarial.

    Args:
        tema: Tema do artigo a ser gerado

    Returns:
        EstadoEnriquecido: Estado final com todos os metadados e históricos
    """
    print("=" * 60)
    print("🚀 INICIANDO WORKFLOW DE GERAÇÃO DE CONTEÚDO")
    print("=" * 60)

    # Criar estado inicial
    estado_inicial = criar_estado_inicial(tema)

    # Executar grafo
    estado_final = app.invoke(estado_inicial)

    # Finalizar estado com métricas
    estado_final = finalizar_estado(estado_final)

    print("=" * 60)
    print("✅ WORKFLOW CONCLUÍDO COM SUCESSO")
    print("=" * 60)

    return estado_final

# ===========================
# 8. TESTE LOCAL (OPCIONAL)
# ===========================

if __name__ == "__main__":
    # Teste local do workflow
    tema_teste = "A importância da Inteligência Artificial no futuro da medicina"
    resultado = executar_workflow(tema_teste)

    print("\n📊 RESUMO DA EXECUÇÃO:")
    print(f"Request ID: {resultado['request_id']}")
    print(f"Iterações: {len(resultado['historico_rascunhos'])}")
    print(f"Tempo total: {resultado['tempo_total_execucao']:.2f}s")
    print(f"Status: {'APROVADO ✅' if resultado['aprovado'] else 'REJEITADO ❌'}")
    print(f"\n📝 TEXTO FINAL:\n{resultado['rascunho']}")
