# Configuração do WhatsApp Cloud API — Meta

Guia completo para ativar e configurar o canal de comunicação WhatsApp no projeto Simulador de Ambientes.

---

## Dados do App (já configurados)

```
Phone Number ID:              1115376094990099
WhatsApp Business Account ID: 952620424037700
Número de teste:              +1 555 630 3616
```

---

## Passo 1 — Gerar o Token de Acesso Permanente

> ⚠️ O token que aparece na tela "Início Rápido" é **temporário** — expira em horas. Você precisa de um **permanente**.

1. No painel da Meta, vá em **Configurações → Básico**
2. Desça até o campo **"Chave secreta do app"** — copie ela
3. Acesse o [Business Manager](https://business.facebook.com/settings/)
4. Em **Usuários → Usuários do sistema** → clique em **"Adicionar"**
5. Preencha:
   - **Nome:** `n8n-bot`
   - **Função:** Administrador
6. Clique em **Salvar**
7. Clique no usuário criado → **"Gerar novo token"**
8. Selecione seu app e marque as permissões:
   - ✅ `whatsapp_business_messaging`
   - ✅ `whatsapp_business_management`
9. Clique **"Gerar token"** → **copie e salve em local seguro** (só aparece uma vez!)

**Salve no seu `.env`:**
```
WHATSAPP_TOKEN=seu_token_permanente_aqui
```

---

## Passo 2 — Configurar o Webhook (conectar ao n8n)

### 2A — Criar o Webhook no n8n

1. No seu n8n, crie um novo Workflow em branco
2. Adicione o nó **Webhook** como gatilho
3. Configure:
   - **Método:** GET e POST
   - **Path:** `whatsapp-simulador`
4. Clique em **"Listen for Test Event"** para ativar
5. Copie a URL gerada:
   ```
   https://SEU-N8N.com/webhook/whatsapp-simulador
   ```

### 2B — Registrar o Webhook na Meta

1. No painel da Meta → **WhatsApp → Configuração**
2. Clique em **"Configurar Webhooks"** (Etapa 3)
3. Preencha:
   - **URL de callback:** URL do n8n copiada acima
   - **Token de verificação:** `simulador2026` (ou qualquer string)
4. Clique **"Verificar e salvar"**

> ⚠️ A Meta faz uma requisição **GET** com o parâmetro `hub.challenge`. O n8n precisa responder com esse valor para a verificação passar.

### 2C — Nó de Resposta ao hub.challenge no n8n

No Webhook do n8n, adicione um nó **"Respond to Webhook"**:

| Campo | Valor |
|-------|-------|
| Respond With | Text |
| Response Body | `{{ $json.query["hub.challenge"] }}` |
| Condição | Só atua se `$json.query["hub.mode"] === "subscribe"` |

### 2D — Assinar os Eventos

Após a verificação, no painel da Meta, assine:
- ✅ `messages`
- ✅ `messaging_postbacks` (opcional)

---

## Passo 3 — Adicionar Número Real

> ⚠️ Só faça isso quando tiver o **chip virgem** em mãos (número sem WhatsApp cadastrado).

1. No painel da Meta, clique em **"Adicionar número de telefone"** (Etapa 5)
2. Preencha:
   - **Nome de exibição da empresa:** nome da loja
   - **Fuso horário:** Brasil
   - **Moeda:** BRL
3. Clique em **continuar** → insira o número do chip
4. A Meta envia um SMS → digite o código de verificação
5. Após confirmação, selecione o número no campo **"De"**

---

## Passo 4 — Adicionar Forma de Pagamento

1. No painel da Meta, clique em **"Adicionar forma de pagamento"** (Etapa 6)
2. Use cartão de crédito internacional
3. Isso libera mensagens além das **1.000 gratuitas/mês**

---

## Teste Imediato (sem chip)

Enquanto o chip não chega, teste com o número de teste:

1. Na Etapa 1, clique em **"Selecione um número de destinatário"**
2. Adicione seu número pessoal de WhatsApp
3. Clique **"Enviar mensagem"** — você receberá o template `hello_world`

---

## Envio de Mensagem via API (curl para testes)

```bash
curl -X POST \
  https://graph.facebook.com/v25.0/1115376094990099/messages \
  -H "Authorization: Bearer SEU_TOKEN_PERMANENTE" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "template",
    "template": {
      "name": "hello_world",
      "language": { "code": "en_US" }
    }
  }'
```

---

## Envio de Imagem via API

```bash
# Passo 1: Upload da imagem
curl -X POST \
  https://graph.facebook.com/v25.0/1115376094990099/media \
  -H "Authorization: Bearer SEU_TOKEN_PERMANENTE" \
  -F "messaging_product=whatsapp" \
  -F "file=@/caminho/para/imagem.jpg" \
  -F "type=image/jpeg"
# Retorna: { "id": "MEDIA_ID" }

# Passo 2: Enviar a imagem
curl -X POST \
  https://graph.facebook.com/v25.0/1115376094990099/messages \
  -H "Authorization: Bearer SEU_TOKEN_PERMANENTE" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "image",
    "image": {
      "id": "MEDIA_ID",
      "caption": "Aqui está seu ambiente simulado! 🚪"
    }
  }'
```

---

## Download de Mídia Recebida

Quando o cliente envia uma imagem, a API retorna um `media_id`. Para baixar:

```bash
# Passo 1: Pegar a URL da mídia
curl -X GET \
  https://graph.facebook.com/v25.0/MEDIA_ID \
  -H "Authorization: Bearer SEU_TOKEN_PERMANENTE"
# Retorna: { "url": "https://...", "mime_type": "image/jpeg" }

# Passo 2: Baixar o arquivo
curl -X GET "URL_RETORNADA" \
  -H "Authorization: Bearer SEU_TOKEN_PERMANENTE" \
  --output imagem_recebida.jpg
```

---

## Checklist de Configuração

```
[ ] Token permanente gerado via Usuário do Sistema (Business Manager)
[ ] Webhook criado no n8n com resposta ao hub.challenge
[ ] URL do webhook registrada no painel da Meta
[ ] Evento "messages" assinado no webhook
[ ] Teste de envio para número pessoal funcionando
[ ] Chip virgem comprado (R$ 15–30)
[ ] Número real adicionado e verificado
[ ] Forma de pagamento adicionada
```

---

## Segurança

- ✅ Ative **autenticação em dois fatores** no Business Manager
- ✅ Use apenas computadores confiáveis para acessar o painel da Meta
- ✅ Nunca exponha o token permanente em código público ou repositórios
- ✅ Armazene o token em variáveis de ambiente (`.env`) e nunca commite o `.env`
