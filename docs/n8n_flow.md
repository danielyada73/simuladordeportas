# Fluxo n8n — Simulador de Ambientes

Documentação detalhada do workflow principal no n8n.

---

## Workflow Principal: `simulador-whatsapp-main`

### Visão Geral dos Nós

```
[Webhook Trigger]
      ↓
[Switch: GET ou POST]
      ├── GET → [Respond: hub.challenge]
      └── POST → [Set: Extrair Dados]
                      ↓
              [Google Sheets: Buscar Usuário]
                      ↓
              [IF: Usuário existe?]
                  ├── NÃO → [GSheets: Criar Usuário] → [WA: Pedir foto ambiente]
                  └── SIM → [Switch: Estado do usuário]
                                ├── AGUARDANDO_AMBIENTE → [IF: é imagem?]
                                │       ├── SIM → [GSheets: salvar foto_amb] → [WA: Pedir foto porta]
                                │       └── NÃO → [WA: Pedir imagem]
                                └── AGUARDANDO_PORTA → [IF: é imagem?]
                                        ├── SIM → [IF: tem créditos?]
                                        │       ├── SIM → [Sub-fluxo: Gerar Imagem]
                                        │       └── NÃO → [WA: Mensagem de upgrade]
                                        └── NÃO → [WA: Pedir imagem]
```

---

## Configuração do Nó Webhook

```
Tipo: Webhook
Path: whatsapp-simulador
Método: GET e POST
Modo de Resposta: Manual (Respond to Webhook)
```

---

## Nó: Set — Extrair Dados da Mensagem

Expressões para mapear os dados do payload do WhatsApp:

```javascript
// Número do cliente
numero: {{ $json.body.entry[0].changes[0].value.messages[0].from }}

// Tipo da mensagem (text, image, audio, etc)
tipo_msg: {{ $json.body.entry[0].changes[0].value.messages[0].type }}

// Media ID (se for imagem)
media_id: {{ $json.body.entry[0].changes[0].value.messages[0].image.id }}

// Texto (se for texto)
texto: {{ $json.body.entry[0].changes[0].value.messages[0].text.body }}
```

---

## Nó: Google Sheets — Buscar Usuário

```
Operation: Read Rows
Document ID: [ID da sua planilha]
Sheet Name: Usuarios
Lookup Column: numero_whatsapp
Lookup Value: {{ $json.numero }}
```

---

## Nó: Google Sheets — Criar Usuário

```
Operation: Append Row
Document ID: [ID da sua planilha]
Sheet Name: Usuarios
Columns:
  numero_whatsapp: {{ $json.numero }}
  plano: alpha
  creditos_restantes: 2
  total_geracoes: 0
  estado: AGUARDANDO_AMBIENTE
  data_cadastro: {{ $now.format('dd/MM/yyyy') }}
```

---

## Nó: HTTP Request — Enviar Mensagem de Texto (WhatsApp)

```
Method: POST
URL: https://graph.facebook.com/v25.0/1115376094990099/messages
Headers:
  Authorization: Bearer {{ $vars.WHATSAPP_TOKEN }}
  Content-Type: application/json
Body:
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.numero }}",
  "type": "text",
  "text": {
    "body": "Olá! 👋 Bem-vindo ao Simulador de Portas!\n\nEnvie a foto do *ambiente* onde deseja instalar a porta (entrada da casa, quarto, cozinha, etc)"
  }
}
```

---

## Sub-fluxo: Gerar Imagem

### Nó 1: Download da Foto Ambiente (pegar URL)

```
Method: GET
URL: https://graph.facebook.com/v25.0/{{ $json.foto_ambiente_id }}
Headers:
  Authorization: Bearer {{ $vars.WHATSAPP_TOKEN }}
```

### Nó 2: Download binário da foto ambiente

```
Method: GET
URL: {{ $json.url }}
Headers:
  Authorization: Bearer {{ $vars.WHATSAPP_TOKEN }}
Response Format: File
```

### Nó 3: Upload para Cloudflare R2

```
Method: PUT
URL: https://[ACCOUNT_ID].r2.cloudflarestorage.com/[BUCKET]/ambiente_{{ $json.numero }}.jpg
Headers:
  Authorization: [R2 Auth]
  Content-Type: image/jpeg
Body: [binário da imagem]
```

_(Repita os nós 1, 2 e 3 para a foto da porta)_

### Nó 4: Chamar Replicate API (SAM para máscara)

```
Method: POST
URL: https://api.replicate.com/v1/predictions
Headers:
  Authorization: Token {{ $vars.REPLICATE_TOKEN }}
  Content-Type: application/json
Body:
{
  "version": "meta/sam-2.1-hiera-large:...",
  "input": {
    "image": "URL_PUBLICA_FOTO_AMBIENTE"
  }
}
```

### Nó 5: Aguardar Resultado SAM

```
Tipo: Wait
Duração: 10 segundos
(depois: HTTP GET no endpoint de status do Replicate)
```

### Nó 6: Chamar SD Inpainting

```
Method: POST
URL: https://api.replicate.com/v1/predictions
Headers:
  Authorization: Token {{ $vars.REPLICATE_TOKEN }}
  Content-Type: application/json
Body:
{
  "version": "stability-ai/stable-diffusion-inpainting:...",
  "input": {
    "image": "URL_FOTO_AMBIENTE",
    "mask": "URL_MASCARA_SAM",
    "prompt": "Replace door with provided door model, photorealistic, natural lighting, same perspective, no distortion",
    "negative_prompt": "distorted, blurry, unrealistic, watermark, low quality",
    "inpaint_full_res": true,
    "num_inference_steps": 50,
    "guidance_scale": 7.5
  }
}
```

### Nó 7: Aguardar e baixar resultado

```
GET https://api.replicate.com/v1/predictions/[ID_DA_PREDICTION]
(polling a cada 5s até status = "succeeded")
→ Baixar imagem da URL de output
```

### Nó 8: Upload da imagem gerada para o WhatsApp

```
Method: POST
URL: https://graph.facebook.com/v25.0/1115376094990099/media
Headers:
  Authorization: Bearer {{ $vars.WHATSAPP_TOKEN }}
Body (multipart/form-data):
  messaging_product: whatsapp
  file: [binário da imagem gerada]
  type: image/jpeg
```

### Nó 9: Enviar Imagem ao Cliente

```
Method: POST
URL: https://graph.facebook.com/v25.0/1115376094990099/messages
Headers:
  Authorization: Bearer {{ $vars.WHATSAPP_TOKEN }}
  Content-Type: application/json
Body:
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.numero }}",
  "type": "image",
  "image": {
    "id": "{{ $json.media_id_gerado }}",
    "caption": "✅ Aqui está seu ambiente com a porta escolhida!\n\nGostou? Entre em contato para fechar o pedido. 🚪"
  }
}
```

### Nó 10: Descontar Crédito e Resetar Estado

```
Google Sheets Update:
  creditos_restantes: {{ $json.creditos_restantes - 1 }}
  total_geracoes: {{ $json.total_geracoes + 1 }}
  estado: AGUARDANDO_AMBIENTE
```

---

## Variáveis de Ambiente (n8n Credentials)

Configure no n8n em **Settings → Credentials**:

| Nome | Tipo | Valor |
|------|------|-------|
| `WHATSAPP_TOKEN` | Header Auth | Token permanente da Meta |
| `REPLICATE_TOKEN` | Header Auth | Token do Replicate |
| `PHONE_NUMBER_ID` | String | `1115376094990099` |
| `WABA_ID` | String | `952620424037700` |

---

## Mensagens do Bot

### Boas-vindas / Pedido de foto do ambiente
```
Olá! 👋 Bem-vindo ao Simulador de Portas!

Por favor, envie a foto do *ambiente* onde deseja instalar a porta.
(Ex: entrada da casa, quarto, cozinha, corredor)

📸 Dica: Use uma foto bem iluminada e em boa resolução para melhor resultado!
```

### Pedido de foto da porta
```
✅ Foto do ambiente recebida!

Agora envie a foto do *modelo de porta* que você deseja experimentar.
```

### Processando
```
⏳ Gerando a simulação do seu ambiente com a porta escolhida...

Isso pode levar alguns instantes. Aguarde!
```

### Créditos esgotados
```
❌ Você atingiu o limite de simulações gratuitas do plano *Alpha*.

Para continuar gerando simulações, faça upgrade para o plano *Omega*:

🔗 [Link de pagamento aqui]

Com o plano Omega você tem *50 simulações por mês*!
```

### Envio do resultado
```
✅ Aqui está seu ambiente com a porta escolhida!

Gostou do resultado? Entre em contato para fechar o pedido. 🚪
```
