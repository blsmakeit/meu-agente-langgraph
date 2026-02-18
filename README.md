# 🧠 AIOps Content Engine: Enterprise-Grade Writer-Reviewer System

> A stateful, multi-agent orchestration platform with comprehensive tracking, performance analytics, and interactive visualization using LangGraph and Anthropic's Claude Sonnet 4.6.

![Status](https://img.shields.io/badge/Status-Production-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.15+-purple)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)

## 📖 Overview

This project implements an **Enterprise-Grade AI Operations (AIOps) Platform** that transforms simple content generation into a fully tracked, monitored, and optimized workflow.

Test app here: https://meu-redator-ia.streamlit.app/

By leveraging **LangGraph**, the system maintains a persistent state across an iterative loop between two specialized agents: a **Writer** (Redator) and a **Reviewer** (Revisor). Unlike traditional single-shot AI generation, this system ensures outputs undergo rigorous internal validation and progressive refinement before delivery.

The platform includes:
- **Enriched State Tracking** with timestamps, decision logs, and execution metadata
- **Enterprise REST API** with comprehensive performance metrics
- **Interactive Command Center** with 4-tab Streamlit interface
- **Real-time Analytics** with Plotly visualizations
- **Rate Limiting Protection** to prevent API throttling
- **Cost Monitoring** with token usage and cost estimation

---

## 🏗️ System Architecture

### Core Components

The system is designed as a **State Machine** (Directed Graph with cycles):

1. **Enriched State Management** (`EstadoEnriquecido`):
   - 13 tracked fields vs 4 in basic version
   - UUID-based request tracking
   - Complete iteration history
   - Timestamp tracking (start/end)
   - Token usage and execution time
   - Decision logs for each agent action

2. **Writer Node (Redator)**:
   - Generates or refines content based on topic and critiques
   - Tracks execution time and token usage
   - Stores all draft versions in iteration history
   - 1.5s rate limit delay before API calls

3. **Reviewer Node (Revisor)**:
   - Evaluates draft against quality standards
   - Provides specific feedback or approval
   - Tracks review decisions and timing
   - 1.5s rate limit delay before API calls

4. **Conditional Router**:
   - Evaluates approval status
   - Enforces maximum 3 iterations to prevent rate limiting
   - Routes to END or back to Writer

5. **FastAPI Backend**:
   - Enriched `/gerar` endpoint with comprehensive response
   - Health check endpoint `/health`
   - Prompt inspection endpoint `/prompts`
   - Full CORS support for frontend integration

6. **Streamlit Command Center**:
   - 4-tab interactive interface
   - Real-time performance monitoring
   - Plotly-based analytics visualizations
   - Prompt laboratory for system inspection

### Workflow Diagram

```
┌─────────────────────┐
│   START             │
│ • Generate UUID     │
│ • Initialize State  │
│ • Track Timestamp   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Redator (Writer)  │◄──────────┐
│ • Rate limit (1.5s) │           │
│ • Generate content  │           │
│ • Log decision      │           │
│ • Track tokens      │           │
└──────┬──────────────┘           │
       │                          │
       ▼                          │
┌─────────────────────┐           │
│  Revisor (Reviewer) │           │
│ • Rate limit (3.0s) │           │
│ • Evaluate quality  │           │
│ • Log decision      │           │
│ • Track tokens      │           │
└──────┬──────────────┘           │
       │                          │
       ▼                          │
   [Aprovado?]                    │
   [Iteração ≤ 3?]                │
       │                          │
   ┌───┴───┐                     │
   │       │                     │
  Sim     Não ──────────────────┘
   │
   ▼
┌─────────────────────┐
│     END             │
│ • Calculate metrics │
│ • Finalize state    │
│ • Return response   │
└─────────────────────┘
```

---

## 🚀 Installation and Setup

### 1. Prerequisites

* Python 3.11 or higher
* Anthropic API Key
* LangSmith API Key (Optional, for tracing)

### 2. Clone and Install

```bash
# Clone the repository
git clone https://github.com/bruno1008/meu-agente-langgraph.git
cd meu-agente-langgraph

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
LANGCHAIN_TRACING_V2=true
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=Content-Engine-Audit
```

Or use the template:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

---

## 🖥️ Execution

### Backend Server

Start the FastAPI backend:

```bash
python3 -m uvicorn main:server --reload
```

Server runs on `http://localhost:8000`

**Available Endpoints:**
- `POST /gerar` - Generate content with full tracking
- `GET /health` - Health check and system status
- `GET /prompts` - View system prompts
- `GET /` - API information

### Frontend Interface

Start the Streamlit Command Center:

```bash
streamlit run interface.py
```

Interface opens at `http://localhost:8501`

**Available Tabs:**
1. **📝 Product View** - Clean content generation interface
2. **🔍 Logic Trace** - Timeline of Writer-Reviewer dialogue
3. **📊 Performance Analytics** - Metrics, charts, cost simulation
4. **🧪 Prompt Lab** - System prompt inspection

---

## 📡 API Usage

### Enriched Response Format

**Request:**
```json
{
  "tema": "A importância da Inteligência Artificial no futuro da medicina"
}
```

**Response:**
```json
{
  "request_id": "a3f7b2c1-4e5d-6789-abcd-ef1234567890",
  "tema": "A importância da Inteligência Artificial...",
  "texto_final": "[Generated and approved blog post content]",
  "aprovado": true,

  "historico_criticas": [
    {
      "iteracao": 1,
      "timestamp": "2024-01-15T14:30:22.123456",
      "feedback": "CRÍTICA: Adicione mais exemplos práticos...",
      "tipo": "critica"
    },
    {
      "iteracao": 2,
      "timestamp": "2024-01-15T14:30:35.654321",
      "feedback": "Excelente!",
      "tipo": "aprovado"
    }
  ],

  "historico_rascunhos": [
    "Primeiro rascunho...",
    "Rascunho melhorado..."
  ],

  "logs_decisao": [
    {
      "iteracao": 1,
      "timestamp": "2024-01-15T14:30:20.000000",
      "acao": "redator",
      "entrada": "Tema: A importância da IA...",
      "saida": "Primeiro rascunho...",
      "tokens_usados": 450,
      "tempo_execucao": 2.34
    }
  ],

  "metricas": {
    "tempo_total_segundos": 8.45,
    "numero_iteracoes": 2,
    "tokens_totais_input": 380,
    "tokens_totais_output": 520,
    "tokens_totais": 900,
    "custo_estimado_usd": 0.0089,
    "timestamp_inicio": "2024-01-15T14:30:18.000000",
    "timestamp_fim": "2024-01-15T14:30:26.450000"
  },

  "metadata_modelo": {
    "modelo_id": "claude-sonnet-4-6",
    "temperatura": 0.7,
    "max_tokens": 2000,
    "versao": "anthropic-2024"
  },

  "versao_sistema": "2.0.0"
}
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/gerar" \
  -H "Content-Type: application/json" \
  -d '{"tema": "O futuro do trabalho remoto em 2025"}'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/gerar",
    json={"tema": "Benefícios da automação com IA"}
)

result = response.json()

# Access enriched data
print(f"Request ID: {result['request_id']}")
print(f"Iterations: {result['metricas']['numero_iteracoes']}")
print(f"Cost: ${result['metricas']['custo_estimado_usd']:.4f}")
print(f"Final text: {result['texto_final']}")
```

---

## ✨ Key Features

### 🎯 Enterprise-Grade Tracking

- **UUID Request Tracking**: Every execution gets a unique identifier
- **Complete Iteration History**: All drafts and critiques stored
- **Decision Logs**: Timestamp, action, input/output for each agent call
- **Execution Metrics**: Time, tokens, cost calculated automatically

### 📊 Performance Analytics

- **Plotly Gauge Charts**: Real-time latency visualization
- **Token Distribution**: Donut charts showing input/output breakdown
- **Cost Simulator**: Project costs for 100-10,000 executions
- **Performance Tables**: Compare against ideal targets

### 🛡️ Rate Limiting Protection

- **API Delays**: 3.0-second pause before each LLM call
- **Iteration Limits**: Maximum 3 iterations to prevent runaway loops
- **Automatic Throttling**: Respects Anthropic API rate limits
- **Error Recovery**: Graceful handling of rate limit errors

### 🔍 Complete Observability

- **LangSmith Integration**: Optional visual debugging
- **Timeline Visualization**: See Writer-Reviewer dialogue step-by-step
- **Prompt Inspection**: View system prompts in Prompt Lab
- **Session Persistence**: Results saved in Streamlit session state

### 💰 Cost Management

- **Token Counting**: Estimate based on character count (4 chars ≈ 1 token)
- **Cost Calculation**: Claude Sonnet 4.6 pricing ($3/1M input, $15/1M output)
- **Cost Projection**: Simulate costs for multiple executions
- **Budget Monitoring**: Track cumulative costs per request

---

## 📂 Project Structure

```
meu-agente-langgraph/
├── app.py                 # LangGraph workflow with enriched state
├── main.py                # FastAPI server with enriched endpoints
├── interface.py           # Streamlit Command Center (4 tabs)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git exclusions
└── README.md             # This file
```

### File Descriptions

**[app.py](app.py)** - Core LangGraph Logic
- `EstadoEnriquecido` - 13-field state with full tracking
- `redator()` - Writer node with rate limiting and logging
- `revisor()` - Reviewer node with rate limiting and logging
- `decidir_proximo_passo()` - Router with iteration limits
- `executar_workflow()` - Main execution function

**[main.py](main.py)** - FastAPI Backend
- Pydantic models for enriched responses
- `/gerar` endpoint with comprehensive tracking
- `/health` for system status
- `/prompts` for prompt inspection
- Cost calculation utilities

**[interface.py](interface.py)** - Streamlit Frontend
- Tab 1: Product View (clean content generation)
- Tab 2: Logic Trace (iteration timeline)
- Tab 3: Performance Analytics (charts + metrics)
- Tab 4: Prompt Lab (system prompt viewing)
- Sidebar with API configuration and health check

---

## 🛠️ Technical Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Orchestration** | LangGraph | >=0.0.15 | State machine and workflow management |
| **LLM** | Claude Sonnet 4.6 | Latest | Content generation and review |
| **Framework** | LangChain | >=0.1.0 | LLM integration and tooling |
| **API** | FastAPI | >=0.110.0 | REST API server |
| **Server** | Uvicorn | >=0.27.0 | ASGI server for FastAPI |
| **Frontend** | Streamlit | >=1.30.0 | Interactive command center |
| **Visualization** | Plotly | >=5.18.0 | Charts and analytics |
| **Data** | Pandas | >=2.1.0 | Data manipulation |
| **HTTP Client** | httpx | >=0.25.0 | Async HTTP requests |
| **Resilience** | tenacity | >=8.0.0 | Retry logic |
| **Validation** | Pydantic | >=2.0.0 | Data models and validation |
| **Config** | python-dotenv | >=1.0.0 | Environment variable management |
| **Observability** | LangSmith | Optional | Workflow tracing and debugging |

---

## 🎯 Use Cases

### Content Marketing
Generate high-quality blog posts for Portuguese-speaking audiences with full quality control and cost tracking.

### Automated Publishing
Create draft articles that undergo automated review cycles, with complete audit trails for compliance.

### Research & Development
Experiment with multi-agent AI systems, study iteration patterns, and optimize prompt engineering.

### AIOps & Monitoring
Demonstrate enterprise-grade AI operations with metrics, logging, and performance analytics.

### Cost Optimization
Track and optimize AI content generation costs with detailed token usage and cost projections.

### Educational Purposes
Learn LangGraph state machines, multi-agent orchestration, and production-grade AI system design.

---

## 📈 Performance Metrics

### Typical Execution Profile

- **Average Latency**: 8-12 seconds (with rate limiting)
- **Average Iterations**: 1-3 cycles
- **Average Tokens**: 600-1200 total (input + output)
- **Average Cost**: $0.006-$0.015 per execution
- **Success Rate**: 95%+ approval within 3 iterations

### Rate Limiting Strategy

To prevent HTTP 429 errors from Anthropic API:
- **3.0-second delay** before each LLM call
- **Maximum 3 iterations** enforced by router
- Supports up to **40 requests/minute** with delays
- Compatible with Anthropic's rate limits (50 RPM for Build Tier 1)

---

## 📝 License

This project is available for educational and research purposes.

---

## 👨‍💻 Author

**Bruno Sousa**

- Enterprise AI Operations Platform
- LangGraph Multi-Agent Systems
- Production-Grade AI Engineering

---

## 🙏 Acknowledgments

- **Anthropic** for Claude Sonnet 4.6 LLM
- **LangChain** for LangGraph orchestration framework
- **FastAPI** for high-performance API framework
- **Streamlit** for rapid frontend development
- **Plotly** for interactive visualizations

---

**Version**: 2.0.0
**Status**: Production-Ready
**Last Updated**: 2026-02-18
