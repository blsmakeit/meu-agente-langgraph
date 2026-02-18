# 📝 LangGraph Content Engine: Autonomous Writer-Reviewer Loop

> A stateful, multi-agent orchestration system for iterative content generation using LangGraph and Anthropic's Claude Sonnet 4.6.

![Status](https://img.shields.io/badge/Status-Ongoing-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.15+-purple)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal)

## 📖 Overview

This project implements a **Cyclic Multi-Agent System** designed to solve the limitations of single-prompt AI generation.

By leveraging **LangGraph**, the system maintains a persistent state across an iterative loop between two specialised agents: a **Writer** (Redator) and a **Reviewer** (Revisor). This ensures that the output is not merely a first-draft response but a refined product that has undergone rigorous internal validation and correction before being returned to the user.

The system is optimized for Portuguese language content generation, making it ideal for Brazilian and Portuguese markets requiring high-quality AI-generated blog posts and articles.

### 🏗️ Architecture

The system is designed as a **State Machine** (Directed Graph with cycles allowed):

1. **State Definition:** A global `TypedDict` tracks the topic (`tema`), draft content (`rascunho`), reviewer feedback (`critica`), and the approval status (`aprovado`).

2. **The Writer Node (Redator):** Receives the topic and any previous critiques to generate or improve a draft. Uses Claude Sonnet 4.6 with specialized prompts to create professional, concise blog posts.

3. **The Reviewer Node (Revisor):** Evaluates the draft against quality standards. It provides specific feedback prefixed with "CRÍTICA:" or returns "APROVADO" status when the content meets quality requirements.

4. **Conditional Routing:** A router function evaluates the approval flag. If approved, the process terminates at `END`; otherwise, it routes back to the Writer for a new iteration with the reviewer's feedback.

5. **FastAPI Wrapper:** The graph is compiled and exposed via an asynchronous REST API at the `/gerar` endpoint.

#### Workflow Diagram

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Redator   │◄──────┐
│  (Writer)   │       │
└──────┬──────┘       │
       │              │
       ▼              │
┌─────────────┐       │
│   Revisor   │       │
│  (Reviewer) │       │
└──────┬──────┘       │
       │              │
       ▼              │
   [Aprovado?]        │
       │              │
   ┌───┴───┐         │
   │       │         │
  Sim     Não        │
   │       │         │
   │       └─────────┘
   │
   ▼
┌─────────────┐
│     END     │
└─────────────┘
```

## 🔧 Installation and Setup

### 1. Prerequisites

* Python 3.11 or higher
* Anthropic API Key
* LangSmith API Key (Optional, for tracing and observability)

### 2. Local Configuration

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

### 3. Environment Variables

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
LANGCHAIN_TRACING_V2=true
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=Content-Engine-Audit
```

You can use the provided `.env.example` as a template:

```bash
cp .env.example .env
# Then edit .env with your actual API keys
```

## 🚀 Execution

### Start the Backend Server

```bash
python3 -m uvicorn main:server --reload
```

The server will start on `http://localhost:8000`

### API Usage

Send a POST request to `http://localhost:8000/gerar`:

**Request:**
```json
{
  "tema": "O impacto da Inteligência Artificial Generativa na medicina clínica até 2026"
}
```

**Response:**
```json
{
  "tema": "O impacto da Inteligência Artificial Generativa na medicina clínica até 2026",
  "texto_final": "[Generated and approved blog post content]",
  "feedback_revisor": "APROVADO"
}
```

### Example using cURL

```bash
curl -X POST "http://localhost:8000/gerar" \
  -H "Content-Type: application/json" \
  -d '{"tema": "A evolução do LangGraph em 2024"}'
```

### Example using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/gerar",
    json={"tema": "Benefícios da automação com IA"}
)

result = response.json()
print(result["texto_final"])
```

## ✨ Core Features

* **Persistence of State:** The agent remembers previous critiques across iterations, preventing repetitive errors and enabling progressive refinement.

* **Granular Observability:** Integrated with LangSmith for real-time visual debugging of the graph's decision-making process, allowing you to trace each iteration and decision point.

* **Separation of Concerns:** Distinct system prompts for writing and auditing roles to maximize LLM performance. The Writer focuses on content creation, while the Reviewer focuses on quality assurance.

* **REST Integration:** Fully compatible with modern frontend frameworks through FastAPI, making it easy to integrate into web applications, mobile apps, or other services.

* **Automatic Quality Assurance:** Content is automatically refined through multiple iterations until it meets quality standards, eliminating the need for manual review loops.

* **Portuguese Language Optimized:** Prompts and content generation are specifically designed for Portuguese language markets, ensuring natural and culturally appropriate content.

* **Iterative Refinement Loop:** Unlike single-shot generation, this system can perform multiple improvement cycles, each building on previous feedback.

## 📂 Project Structure

* [app.py](app.py): Contains the LangGraph logic, state definitions, agent nodes (Redator and Revisor), conditional routing function, and graph compilation.

* [main.py](main.py): FastAPI server configuration, endpoint definitions, request/response models, and graph invocation logic.

* [requirements.txt](requirements.txt): Project dependencies with version specifications for reproducibility.

* [.env.example](.env.example): Template for required environment credentials and configuration variables.

* [.gitignore](.gitignore): Configuration to prevent sensitive data leakage (API keys, environment files, Python cache).

## 🔍 How It Works

### State Management

The workflow maintains a shared state throughout the execution:

```python
class Estado(TypedDict):
    tema: str              # The blog post topic/theme
    rascunho: str          # Current draft content
    critica: Optional[str] # Reviewer's feedback (if any)
    aprovado: bool         # Approval flag
```

### Writer Node

The Writer node generates or refines content based on:
- Initial topic (first iteration)
- Previous draft + reviewer feedback (subsequent iterations)

It always sets `aprovado=False` to ensure the content goes through review.

### Reviewer Node

The Reviewer node evaluates the draft and:
- Returns "APROVADO" if the content meets quality standards
- Returns "CRÍTICA: [specific feedback]" if improvements are needed
- Updates the `aprovado` flag accordingly

### Conditional Logic

After each review, the system decides:
- **If approved:** End the workflow and return the final content
- **If not approved:** Send feedback back to the Writer for improvement

This creates a continuous improvement loop that only terminates when quality standards are met.

## 🛠️ Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | LangGraph >=0.0.15 | State machine and workflow management |
| LLM | Claude Sonnet 4.6 | Content generation and review |
| Framework | LangChain >=0.1.0 | LLM integration and tooling |
| API | FastAPI >=0.110.0 | REST API server |
| Server | Uvicorn >=0.27.0 | ASGI server for FastAPI |
| Config | python-dotenv >=1.0.0 | Environment variable management |
| Observability | LangSmith (optional) | Workflow tracing and debugging |

## 🎯 Use Cases

This system is ideal for:

- **Content Marketing:** Generate high-quality blog posts for Portuguese-speaking audiences
- **Automated Publishing:** Create draft articles that undergo automated quality checks
- **Research Projects:** Experiment with multi-agent AI systems and iterative refinement
- **Content Quality Assurance:** Demonstrate automated review and improvement cycles
- **Educational Purposes:** Learn LangGraph, state machines, and multi-agent orchestration

## 🚧 Future Enhancements

Potential improvements for this project:

- Support for multiple languages beyond Portuguese
- Configurable quality criteria for the Reviewer
- Export to different formats (Markdown, HTML, PDF)
- Persistent storage of generated content
- User feedback integration for continuous learning
- Streaming responses for real-time content generation
- Multiple reviewer agents with specialized focus areas

## 📝 License

This project is available for educational and research purposes.

---

Developed by **Bruno Sousa**
