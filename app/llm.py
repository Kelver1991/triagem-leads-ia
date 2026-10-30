"""Cliente do modelo de linguagem (LLM).

Se a variável ANTHROPIC_API_KEY existir, usa a API do Claude.
Se não existir, o projeto roda em "modo demo" (sem IA), para que
qualquer pessoa consiga testar sem precisar de chave.
"""
import os

MODELO_PADRAO = "claude-haiku-5-5"


def ia_disponivel() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def gerar_texto(sistema: str, mensagem: str, max_tokens: int = 1024) -> str:
    """Envia um prompt ao Claude e devolve só o texto da resposta."""
    from anthropic import Anthropic  # import aqui para o modo demo não exigir a lib configurada

    cliente = Anthropic()
    resposta = cliente.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", MODELO_PADRAO),
        max_tokens=max_tokens,
        system=sistema,
        messages=[{"role": "user", "content": mensagem}],
    )
    return "".join(bloco.text for bloco in resposta.content if bloco.type == "text").strip()
