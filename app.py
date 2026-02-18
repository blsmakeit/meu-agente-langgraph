from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os

load_dotenv()

# 1. Definição do Estado (Adicionei mensagens para o histórico)
class Estado(TypedDict):
    tema: str
    rascunho: str
    critica: Optional[str]
    aprovado: bool

# Inicializar o Modelo
llm = ChatAnthropic(model="claude-sonnet-4-6")
# 2. Definição dos Nós
def redator(state: Estado):
    print("--- NÓ: REDATOR ---")
    tema = state["tema"]
    critica = state.get("critica", "Nenhuma")
    
    prompt = f"""És um redator profissional. 
    Escreve um post curto sobre: {tema}.
    Crítica anterior para melhorar: {critica}.
    Responde APENAS com o texto do post."""
    
    resposta = llm.invoke(prompt)
    return {"rascunho": resposta.content, "aprovado": False}

def revisor(state: Estado):
    print("--- NÓ: REVISOR ---")
    rascunho = state["rascunho"]
    
    prompt = f"""És um editor rigoroso. Avalia este post:
    '{rascunho}'
    
    Se o post for excelente, responde apenas com a palavra 'APROVADO'.
    Se precisar de melhorias, escreve uma crítica curta começando com 'CRÍTICA:'."""
    
    resposta = llm.invoke(prompt)
    conteudo = resposta.content.upper()
    
    if "APROVADO" in conteudo:
        return {"aprovado": True, "critica": "Excelente!"}
    
    return {"aprovado": False, "critica": resposta.content}

# 3. Aresta Condicional
def decidir_proximo_passo(state: Estado):
    if state["aprovado"]:
        return END
    return "redator"

# 4. Montagem do Grafo (Igual ao teu, mas com as funções atualizadas)
workflow = StateGraph(Estado)
workflow.add_node("redator", redator)
workflow.add_node("revisor", revisor)
workflow.set_entry_point("redator")
workflow.add_edge("redator", "revisor")
workflow.add_conditional_edges("revisor", decidir_proximo_passo, {END: END, "redator": "redator"})

app = workflow.compile()