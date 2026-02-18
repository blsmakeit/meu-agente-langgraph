from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Importar funções do app.py
from app import executar_workflow, obter_prompts_sistema

# ===========================
# CONFIGURAÇÃO DO SERVIDOR
# ===========================

server = FastAPI(
    title="🧠 AIOps Content Engine",
    description="Sistema empresarial de geração de conteúdo com tracking completo",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir requisições do Streamlit
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================
# MODELOS PYDANTIC
# ===========================

class TemaInput(BaseModel):
    """Modelo de entrada para geração de conteúdo"""
    tema: str = Field(..., min_length=5, description="Tema do artigo a ser gerado")

class LogDecisaoResponse(BaseModel):
    """Log de decisão individual"""
    iteracao: int
    timestamp: str
    acao: str
    entrada: str
    saida: str
    tokens_usados: Optional[int]
    tempo_execucao: float

class CriticaHistorico(BaseModel):
    """Histórico de críticas do revisor"""
    iteracao: int
    timestamp: str
    feedback: str
    tipo: str  # "aprovado" ou "critica"

class MetricasExecucao(BaseModel):
    """Métricas de performance da execução"""
    tempo_total_segundos: float
    numero_iteracoes: int
    tokens_totais_input: int
    tokens_totais_output: int
    tokens_totais: int
    custo_estimado_usd: float
    timestamp_inicio: str
    timestamp_fim: str

class MetadataModelo(BaseModel):
    """Metadados do modelo LLM usado"""
    modelo_id: str
    temperatura: float
    max_tokens: int
    versao: str

class RespostaEnriquecida(BaseModel):
    """Resposta completa da API com todos os metadados"""
    # Identificação
    request_id: str
    tema: str

    # Resultado final
    texto_final: str
    aprovado: bool

    # Históricos completos
    historico_criticas: List[CriticaHistorico]
    historico_rascunhos: List[str]
    logs_decisao: List[LogDecisaoResponse]

    # Métricas de performance
    metricas: MetricasExecucao

    # Metadata técnica
    metadata_modelo: MetadataModelo
    versao_sistema: str

class HealthResponse(BaseModel):
    """Resposta do endpoint de health check"""
    status: str
    timestamp: str
    versao: str
    modelo_ativo: str

class PromptsResponse(BaseModel):
    """Resposta com os prompts do sistema"""
    prompts: Dict[str, str]
    versao: str

# ===========================
# FUNÇÕES AUXILIARES
# ===========================

def calcular_custo_estimado(tokens_input: int, tokens_output: int) -> float:
    """
    Calcula o custo estimado baseado nos tokens usados.

    Pricing Claude Sonnet 4.6 (aproximado):
    - Input: $3.00 / 1M tokens
    - Output: $15.00 / 1M tokens
    """
    custo_input = (tokens_input / 1_000_000) * 3.00
    custo_output = (tokens_output / 1_000_000) * 15.00
    return custo_input + custo_output

def processar_estado_para_resposta(estado: dict) -> RespostaEnriquecida:
    """
    Converte o estado enriquecido para o modelo de resposta da API.
    """
    # Calcular tokens totais
    tokens_input = sum(
        log.get("tokens_usados", 0) // 2
        for log in estado["logs_decisao"]
    )
    tokens_output = sum(
        log.get("tokens_usados", 0) // 2
        for log in estado["logs_decisao"]
    )
    tokens_totais = tokens_input + tokens_output

    # Calcular custo estimado
    custo = calcular_custo_estimado(tokens_input, tokens_output)

    # Criar histórico de críticas formatado
    historico_criticas = []
    for i, critica in enumerate(estado["historico_criticas"]):
        tipo = "aprovado" if "aprovado" in critica.lower() or "excelente" in critica.lower() else "critica"

        # Encontrar o timestamp correspondente nos logs
        timestamp_critica = estado["timestamp_inicio"]
        for log in estado["logs_decisao"]:
            if log["acao"] == "revisor" and log["iteracao"] == i + 1:
                timestamp_critica = log["timestamp"]
                break

        historico_criticas.append(CriticaHistorico(
            iteracao=i + 1,
            timestamp=timestamp_critica,
            feedback=critica,
            tipo=tipo
        ))

    # Criar métricas de execução
    metricas = MetricasExecucao(
        tempo_total_segundos=estado["tempo_total_execucao"] or 0.0,
        numero_iteracoes=len(estado["historico_rascunhos"]),
        tokens_totais_input=tokens_input,
        tokens_totais_output=tokens_output,
        tokens_totais=tokens_totais,
        custo_estimado_usd=custo,
        timestamp_inicio=estado["timestamp_inicio"],
        timestamp_fim=estado["timestamp_fim"] or datetime.now().isoformat()
    )

    # Converter logs de decisão
    logs_decisao_response = [
        LogDecisaoResponse(**log)
        for log in estado["logs_decisao"]
    ]

    # Criar metadata do modelo
    metadata_modelo = MetadataModelo(**estado["metadata_modelo"])

    # Criar resposta enriquecida
    resposta = RespostaEnriquecida(
        request_id=estado["request_id"],
        tema=estado["tema"],
        texto_final=estado["rascunho"],
        aprovado=estado["aprovado"],
        historico_criticas=historico_criticas,
        historico_rascunhos=estado["historico_rascunhos"],
        logs_decisao=logs_decisao_response,
        metricas=metricas,
        metadata_modelo=metadata_modelo,
        versao_sistema="2.0.0"
    )

    return resposta

# ===========================
# ENDPOINTS DA API
# ===========================

@server.get("/", tags=["Sistema"])
async def root():
    """Endpoint raiz com informações básicas"""
    return {
        "nome": "AIOps Content Engine",
        "versao": "2.0.0",
        "status": "online",
        "endpoints": {
            "gerar": "/gerar",
            "health": "/health",
            "prompts": "/prompts",
            "docs": "/docs"
        }
    }

@server.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """
    Health check endpoint para monitoramento do sistema.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        versao="2.0.0",
        modelo_ativo="claude-sonnet-4-6"
    )

@server.get("/prompts", response_model=PromptsResponse, tags=["Prompt Lab"])
async def obter_prompts():
    """
    Retorna os prompts do sistema para visualização no Prompt Lab.
    """
    prompts = obter_prompts_sistema()
    return PromptsResponse(
        prompts=prompts,
        versao="2.0.0"
    )

@server.post("/gerar", response_model=RespostaEnriquecida, tags=["Geração de Conteúdo"])
async def gerar_conteudo_enriquecido(tema_input: TemaInput):
    """
    Gera conteúdo usando o workflow Writer-Reviewer com tracking completo.

    Este endpoint executa o ciclo iterativo de geração e revisão de conteúdo,
    retornando não apenas o texto final, mas também:
    - Histórico completo de todas as iterações
    - Métricas de performance (tempo, tokens, custo)
    - Logs detalhados de cada decisão do agente
    - Metadata do modelo e da execução

    Args:
        tema_input: Objeto com o tema do artigo

    Returns:
        RespostaEnriquecida: Resposta completa com tracking empresarial

    Raises:
        HTTPException: Em caso de erro na execução
    """
    try:
        logger.info(f"📥 Nova requisição recebida - Tema: {tema_input.tema}")

        # Executar workflow completo
        estado_final = executar_workflow(tema_input.tema)

        # Processar estado para resposta
        resposta = processar_estado_para_resposta(estado_final)

        logger.info(
            f"✅ Requisição {resposta.request_id} concluída - "
            f"{resposta.metricas.numero_iteracoes} iterações, "
            f"{resposta.metricas.tempo_total_segundos:.2f}s"
        )

        return resposta

    except Exception as e:
        logger.error(f"❌ Erro na geração de conteúdo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar conteúdo: {str(e)}"
        )

@server.post("/prompts/test", tags=["Prompt Lab"])
async def testar_prompt_customizado(
    prompt_customizado: Dict[str, str]
):
    """
    Endpoint para testar prompts customizados (funcionalidade futura).

    Args:
        prompt_customizado: Dicionário com o prompt a testar

    Returns:
        Resultado do teste
    """
    return {
        "status": "feature_in_development",
        "mensagem": "Funcionalidade de teste de prompts em desenvolvimento",
        "prompt_recebido": prompt_customizado
    }

@server.get("/analytics/summary", tags=["Analytics"])
async def obter_analytics():
    """
    Endpoint para analytics agregados (funcionalidade futura).

    Retornará métricas agregadas de todas as execuções:
    - Média de iterações
    - Média de tempo de execução
    - Custos totais
    - Taxa de aprovação

    Nota: Requer implementação de persistência (banco de dados)
    """
    return {
        "status": "feature_in_development",
        "mensagem": "Analytics agregados requerem implementação de banco de dados"
    }

# ===========================
# INICIALIZAÇÃO
# ===========================

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Iniciando servidor AIOps Content Engine...")

    uvicorn.run(
        "main:server",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
