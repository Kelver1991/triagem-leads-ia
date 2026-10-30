from enum import Enum

from pydantic import BaseModel, Field


class Intencao(str, Enum):
    orcamento = "orcamento"
    duvida = "duvida"
    pos_venda = "pos_venda"
    reclamacao = "reclamacao"
    outro = "outro"


class Urgencia(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class Lead(BaseModel):
    mensagem: str = Field(min_length=3, max_length=4000)
    canal: str = Field(default="whatsapp")


class Classificacao(BaseModel):
    """Formato que a IA é obrigada a devolver. Se vier fora disso, é rejeitado."""
    intencao: Intencao
    urgencia: Urgencia
    produto: str | None = Field(default=None, description="Produto citado, se houver")
    cidade: str | None = None
    resumo: str = Field(max_length=200)
    proxima_acao: str = Field(max_length=200)


class Resultado(BaseModel):
    modo: str  # "ia" ou "demo"
    prioridade: int = Field(ge=1, le=5, description="1 = atender primeiro")
    classificacao: Classificacao


class Lote(BaseModel):
    leads: list[Lead] = Field(min_length=1, max_length=50)
