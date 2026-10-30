# Triagem de Leads com IA

API em **FastAPI** que lê as mensagens que chegam dos clientes (WhatsApp, site, Instagram), usa um **LLM (Claude)** para classificar cada uma e devolve a **fila de atendimento ordenada por prioridade**.

## O problema

Num time de vendas, as mensagens chegam misturadas: pedido de orçamento, dúvida simples, cliente reclamando de instalação. Quando ninguém faz triagem, uma reclamação urgente pode ficar horas esperando atrás de dúvidas simples, e um cliente com prazo curto esfria.

## Como funciona

```
mensagem do cliente
        │
        ▼
Claude devolve JSON ──► Pydantic valida o formato
        │                   │
        │          inválido? devolve o erro ao modelo e tenta 1 vez mais
        │                   │
        │          falhou de novo ou API fora do ar? usa regras (plano B)
        ▼
intenção + urgência + produto + cidade + resumo + próxima ação
        │
        ▼
prioridade de 1 a 5 ──► /leads/fila devolve tudo em ordem de atendimento
```

Exemplo de resposta:

```json
{
  "modo": "ia",
  "prioridade": 2,
  "classificacao": {
    "intencao": "orcamento",
    "urgencia": "alta",
    "produto": "piscina com aquecedor",
    "cidade": "Guará",
    "resumo": "Quer piscina com aquecedor instalada antes do fim do ano.",
    "proxima_acao": "Ligar hoje, confirmar medidas e enviar orçamento."
  }
}
```

## Decisões técnicas

- **Saída estruturada validada:** o modelo é obrigado a responder num formato fixo. O Pydantic recusa qualquer valor fora da lista (ex.: intenção "comprar").
- **Autocorreção:** se o JSON vier errado, o próprio erro de validação volta para o modelo corrigir.
- **Nunca deixa o cliente sem resposta:** se a IA falhar duas vezes ou a API cair, entram regras por palavras-chave.
- **Proteção contra prompt injection:** a mensagem do cliente vai delimitada e o prompt avisa que o texto é dado, não instrução.
- **Prioridade calculada no código**, não pela IA: a regra de negócio fica explícita, testável e fácil de mudar.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sua_chave   # opcional; sem ela roda em modo demo
uvicorn app.main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs

```bash
curl -X POST http://127.0.0.1:8000/leads/fila -H "Content-Type: application/json" -d '{
  "leads": [
    {"mensagem": "Vocês abrem sábado?"},
    {"mensagem": "Quero orçamento de um spa"},
    {"mensagem": "O deck quebrou, quero falar com alguém"}
  ]
}'
```

## Testes

```bash
pytest -q
```

Cobrem: regras do modo demo, ordenação da fila, JSON cercado por Markdown, autocorreção após JSON inválido e queda da API (tudo com o modelo simulado, sem gastar chamadas).

> Projeto de portfólio com mensagens fictícias, inspirado na rotina de atendimento de uma equipe comercial.
