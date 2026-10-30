from fastapi import FastAPI, HTTPException

from . import classificador, llm
from .schemas import Lead, Lote, Resultado

app = FastAPI(
    title="Triagem de Leads com IA",
    description="Classifica mensagens de clientes (intenção, urgência, produto) e ordena a fila de atendimento.",
    version="1.0.0",
)


def _processar(lead: Lead) -> Resultado:
    try:
        modo, c = classificador.classificar(lead)
    except Exception:
        # API fora do ar: o atendimento continua com as regras
        modo, c = "demo", classificador.classificar_por_regras(lead)
    return Resultado(modo=modo, prioridade=classificador.prioridade(c), classificacao=c)


@app.get("/saude")
def saude():
    return {"status": "ok", "modo": "ia" if llm.ia_disponivel() else "demo"}


@app.post("/leads/classificar", response_model=Resultado)
def classificar(lead: Lead):
    if not lead.mensagem.strip():
        raise HTTPException(status_code=422, detail="Mensagem vazia.")
    return _processar(lead)


@app.post("/leads/fila", response_model=list[Resultado])
def fila(lote: Lote):
    """Classifica vários leads e devolve na ordem em que devem ser atendidos."""
    resultados = [_processar(lead) for lead in lote.leads]
    return sorted(resultados, key=lambda r: r.prioridade)  # sort estável mantém a ordem de chegada no empate
