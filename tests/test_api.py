import json

import pytest
from fastapi.testclient import TestClient

from app import classificador
from app.main import app

cliente = TestClient(app)


@pytest.fixture(autouse=True)
def sem_chave(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def classificar(texto):
    return cliente.post("/leads/classificar", json={"mensagem": texto}).json()


def test_reclamacao_vem_com_prioridade_maxima():
    r = classificar("A piscina instalada semana passada está vazando, um absurdo!")
    assert r["modo"] == "demo"
    assert r["classificacao"]["intencao"] == "reclamacao"
    assert r["prioridade"] == 1


def test_orcamento_detecta_produto_e_urgencia():
    r = classificar("Quanto custa uma piscina com aquecedor? Preciso pra essa semana")
    c = r["classificacao"]
    assert c["intencao"] == "orcamento"
    assert c["urgencia"] == "alta"
    assert c["produto"] == "aquecedor"


def test_fila_ordena_por_prioridade():
    leads = [
        {"mensagem": "Vocês abrem sábado?"},
        {"mensagem": "Quero orçamento de um spa"},
        {"mensagem": "O deck quebrou, quero falar com alguém"},
    ]
    fila = cliente.post("/leads/fila", json={"leads": leads}).json()
    assert [r["classificacao"]["intencao"] for r in fila] == ["reclamacao", "orcamento", "duvida"]


def test_ia_com_json_cercado_por_markdown(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "teste")
    resposta = {"intencao": "orcamento", "urgencia": "media", "produto": "piscina", "cidade": "Guará",
                "resumo": "Quer orçamento", "proxima_acao": "Enviar orçamento"}
    monkeypatch.setattr(classificador.llm, "gerar_texto",
                        lambda *a, **k: "```json\n" + json.dumps(resposta) + "\n```")
    r = classificar("Quero orçamento de piscina no Guará")
    assert r["modo"] == "ia" and r["classificacao"]["cidade"] == "Guará"


def test_ia_corrige_depois_de_json_invalido(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "teste")
    respostas = iter([
        '{"intencao": "comprar", "urgencia": "media"}',  # inválido: intenção fora da lista
        '{"intencao": "orcamento", "urgencia": "media", "produto": null, "cidade": null, '
        '"resumo": "ok", "proxima_acao": "ok"}',
    ])
    pedidos = []

    def falso(sistema, mensagem, max_tokens=400):
        pedidos.append(mensagem)
        return next(respostas)

    monkeypatch.setattr(classificador.llm, "gerar_texto", falso)
    r = classificar("Quero comprar")
    assert r["modo"] == "ia"
    assert "inválida" in pedidos[1]  # o erro foi devolvido ao modelo


def test_ia_fora_do_ar_cai_nas_regras(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "teste")

    def quebra(*a, **k):
        raise ConnectionError

    monkeypatch.setattr(classificador.llm, "gerar_texto", quebra)
    r = classificar("Quero orçamento")
    assert r["modo"] == "demo" and r["classificacao"]["intencao"] == "orcamento"


def test_mensagem_vazia_recusada():
    assert cliente.post("/leads/classificar", json={"mensagem": "   "}).status_code == 422
