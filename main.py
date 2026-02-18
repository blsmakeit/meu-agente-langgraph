from fastapi import FastAPI
from pydantic import BaseModel
from app import app as grafo

server = FastAPI(title="Agente Redator LangGraph")

# Define o formato do que a API recebe
class PedidoPost(BaseModel):
    tema: str

@server.post("/gerar")
async def gerar_post(pedido: PedidoPost):
    # O invoke inicia o ciclo Redator -> Revisor -> Redator...
    resultado = grafo.invoke({
        "tema": pedido.tema,
        "rascunho": "",
        "critica": "",
        "aprovado": False
    })
    return {
        "tema": pedido.tema,
        "texto_final": resultado["rascunho"],
        "feedback_revisor": resultado["critica"]
    }