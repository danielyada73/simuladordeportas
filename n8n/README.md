# Fluxo 01 limpo - Monday Express Alpha

Arquivo principal:
- `01 - Monday Express - Alpha - clean.json`

## O que este fluxo faz
1. Recebe `nome do cliente`, `segmento`, `prazo de entrega` e um arquivo `.txt` via webhook.
2. Extrai o texto do briefing.
3. Gera um resumo inicial com OpenAI via `HTTP Request`.
4. Cria um Google Doc e grava resumo + transcricao.
5. Cria um workspace na Monday.
6. Duplica os 5 boards modelo:
   - `1. BRIEFING`
   - `2. CRIACAO DE LP`
   - `3. CAMPANHAS`
   - `4. OTIMIZACOES`
   - `5. SALDO`
7. Atualiza o item `CRIAR RESUMO DO CLIENTE` com o link do Google Doc.
8. Responde em JSON com IDs e URL do doc.

## Variaveis de ambiente esperadas no n8n
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (opcional, default sugerido: `gpt-4.1-mini`)
- `MONDAY_API_TOKEN`
- `MONDAY_TEMPLATE_BOARD_BRIEFING_ID` (opcional)
- `MONDAY_TEMPLATE_BOARD_LP_ID` (opcional)
- `MONDAY_TEMPLATE_BOARD_CAMPANHAS_ID` (opcional)
- `MONDAY_TEMPLATE_BOARD_OTIMIZACOES_ID` (opcional)
- `MONDAY_TEMPLATE_BOARD_SALDO_ID` (opcional)

Se voce nao definir os IDs de template, o fluxo usa estes valores como fallback:
- Briefing: `18400903329`
- LP: `18400903643`
- Campanhas: `18400904092`
- Otimizacoes: `18400904407`
- Saldo: `18400904467`

## Credenciais que ainda precisam ser ligadas manualmente
- Node `Criar Doc do Briefing`
- Node `Adicionar Conteudo no Doc`

Ambos precisam da sua credencial `Google Docs` dentro do n8n.

## Como testar
Importe o JSON, conecte a credencial do Google Docs e use o `Test URL` do webhook com `multipart/form-data`.

Campos esperados:
- `cliente_nome`
- `segmento`
- `prazo_entrega`
- arquivo `.txt` no corpo multipart

## Exemplo com curl
```bash
curl -X POST "https://SEU-N8N/webhook-test/alpha-monday-express" \
  -F "cliente_nome=Impera Imobiliaria" \
  -F "segmento=Imobiliaria" \
  -F "prazo_entrega=15 dias" \
  -F "briefing=@C:/caminho/briefing.txt;type=text/plain"
```

## Observacoes
- Este fluxo evita nodes `LangChain` e `formTrigger`, que eram os maiores pontos de quebra no export antigo.
- O fluxo foi montado para ser mais facil de importar e depurar.
- Se voce quiser, o proximo passo natural e fazer uma versao 2 com:
  - fallback sem arquivo, aceitando texto puro
  - notificacoes no WhatsApp ou Telegram
  - retorno formatado para o Alpha OS chamar direto
