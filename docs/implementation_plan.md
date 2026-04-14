# Plano Completo de Implementação — Simulador de Ambientes

## Visão Geral

Um chatbot no WhatsApp que recebe **duas fotos** do cliente (ambiente + modelo de porta) e devolve uma **imagem gerada por IA** mostrando como ficaria o ambiente com aquela porta instalada, de forma natural e sem distorção. O sistema tem três planos de acesso com limites de crédito diferentes.

---

## Arquitetura Técnica

```
Cliente (WhatsApp)
       ↓
[WhatsApp Cloud API - Meta]
       ↓
[n8n — Orquestrador Central]
   ├─→ [Google Sheets — Controle de Créditos e Planos]
   ├─→ [Replicate API — IA de Inpainting (Fusão de Imagem)]
   └─→ [Stripe / MercadoPago — Pagamento Plano Omega]
       ↓
Cliente recebe imagem de volta via WhatsApp
```

---

## Componente 1: Canal de Comunicação — WhatsApp Cloud API

Ver guia completo em: [`docs/whatsapp_setup.md`](./whatsapp_setup.md)

**Dados já configurados:**
```
Phone Number ID:              1115376094990099
WhatsApp Business Account ID: 952620424037700
Número de teste:              +1 555 630 3616
```

**Custo:** R$ 15–30 (chip) + primeiras 1.000 conversas/mês gratuitas.

---

## Componente 2: Webhook — Conectando WhatsApp ao n8n

### Fluxo de verificação

```
Meta (GET) → n8n Webhook → Respond to Webhook → hub.challenge
```

O n8n deve responder ao GET da Meta com o valor de `hub.challenge`:
```
{{ $json.query["hub.challenge"] }}
```

---

## Componente 3: Banco de Dados — Google Sheets

### Estrutura da planilha (aba "Usuarios")

| numero_whatsapp | plano | creditos_restantes | total_geracoes | estado | data_cadastro |
|---|---|---|---|---|---|
| 5511999999999 | alpha | 2 | 0 | AGUARDANDO_AMBIENTE | 14/04/2026 |

### Planos e Limites

| Plano | Créditos Iniciais | Valor |
|-------|-------------------|-------|
| **Alpha** | 2 gerações gratuitas | R$ 0 |
| **Beta** | 5 gerações gratuitas | R$ 0 |
| **Omega** | 50 gerações/mês | R$ 47–97/mês |

---

## Componente 4: Lógica do Fluxo n8n

### Estados da Conversa

```
NOVO_USUARIO       → pede foto do ambiente
AGUARDANDO_AMBIENTE → esperando foto 1
AGUARDANDO_PORTA   → esperando foto 2
GERANDO            → processando na IA
CONCLUIDO          → retornou imagem
SEM_CREDITOS       → oferece upgrade de plano
```

### Fluxo Completo (nó por nó)

```
[Webhook]
  → [Switch: GET ou POST?]
     → GET:  [Respond to Webhook: retorna hub.challenge]
     → POST: [Set: extrai numero, tipo_msg, body, media_id]
               → [Google Sheets Read: busca usuario pelo numero]
               → [IF: usuario existe?]
                  → NÃO: [Google Sheets Append: cria usuario alpha 2 créditos]
                         [HTTP: envia "Olá! Envie a foto do AMBIENTE"]
                  → SIM: [Switch: qual o estado do usuario?]
                          → AGUARDANDO_AMBIENTE:
                              [IF: msg é imagem?]
                                → SIM: [Salva media_id como foto_ambiente]
                                       [Google Sheets Update: estado = AGUARDANDO_PORTA]
                                       [HTTP: envia "Ótimo! Agora envie a foto da PORTA"]
                                → NÃO: [HTTP: envia "Por favor, envie uma imagem"]
                          → AGUARDANDO_PORTA:
                              [IF: msg é imagem?]
                                → SIM: [Salva media_id como foto_porta]
                                       [IF: creditos > 0?]
                                          → SIM: [Sub-fluxo de Geração de Imagem]
                                          → NÃO: [Envia msg de upgrade do plano]
                                → NÃO: [HTTP: envia "Por favor, envie uma imagem"]
```

---

## Componente 5: Inteligência Artificial — Replicate + SD Inpainting

### Por que Inpainting?

Modelos de geração normais (texto → imagem) **não preservam o ambiente**.
O **Inpainting** recebe:
- A imagem original (ambiente do cliente)
- Uma máscara (área onde a porta será inserida — gerada automaticamente pelo SAM)
- A imagem de referência (modelo de porta escolhido)

E devolve o ambiente com a porta mesclada naturalmente.

### Estratégia de Detecção Automática da Porta (SAM)

```
foto_ambiente → SAM (Segment Anything Model) → máscara da porta
                                                      ↓
foto_porta + foto_ambiente + máscara → SD Inpainting → imagem_final
```

### Requisição para o Replicate (n8n: HTTP Request)

```json
POST https://api.replicate.com/v1/predictions
Authorization: Token SEU_TOKEN_REPLICATE
Content-Type: application/json

{
  "version": "stability-ai/stable-diffusion-inpainting:...",
  "input": {
    "image": "URL_DA_FOTO_AMBIENTE",
    "mask": "URL_DA_MASCARA_AUTO_GERADA",
    "prompt": "Replace the door with the provided door model, photorealistic, natural lighting, no distortion, same perspective",
    "negative_prompt": "distorted, blurry, unrealistic, watermark",
    "inpaint_full_res": true,
    "num_inference_steps": 50,
    "guidance_scale": 7.5
  }
}
```

### Custo Replicate
- ~US$ 0,012 por geração (GPU T4, ~3 segundos de processamento)
- US$ 10 = ~833 gerações
- Cadastro: [replicate.com](https://replicate.com) → Settings → API Tokens

---

## Componente 6: Download e Upload de Mídia

### Sequência para obter imagem do WhatsApp no n8n

```
1. webhook recebe { media_id: "xxx" }
2. GET https://graph.facebook.com/v25.0/{media_id}
   → retorna { url: "https://..." }
3. GET {url} com header Authorization: Bearer TOKEN
   → retorna binário da imagem
4. Upload para Cloudflare R2 ou Google Drive
   → obtém URL pública para enviar ao Replicate
```

### Storage Temporário

**Cloudflare R2** (recomendado — gratuito até 10GB/mês):
- Crie um bucket público em [dash.cloudflare.com](https://dash.cloudflare.com)
- Use a API S3-compatible para upload via n8n (nó HTTP Request com multipart/form-data)

---

## Componente 7: Envio da Imagem ao Cliente

```
Replicate retorna URL da imagem gerada
        ↓
n8n baixa a imagem (binário)
        ↓
POST https://graph.facebook.com/v25.0/{phone_number_id}/media
  (upload da imagem para o WhatsApp)
        ↓
Retorna: { media_id: "NOVO_MEDIA_ID" }
        ↓
POST https://graph.facebook.com/v25.0/{phone_number_id}/messages
  {
    "to": "55119XXXXXXXX",
    "type": "image",
    "image": {
      "id": "NOVO_MEDIA_ID",
      "caption": "✅ Aqui está seu ambiente com a porta escolhida!"
    }
  }
        ↓
n8n desconta 1 crédito no Google Sheets
```

---

## Componente 8: Monetização — Plano Omega

### MercadoPago (recomendado para Brasil)

1. Acesse [developers.mercadopago.com](https://developers.mercadopago.com)
2. Use a API de **Assinaturas (Subscriptions)**
3. Configure Webhook do MercadoPago → n8n
4. Evento `payment` com status `approved`:
   - n8n atualiza planilha: `plano = omega`, `creditos = 50`

### Stripe

1. Acesse [stripe.com](https://stripe.com)
2. Crie Products + Prices com billing mensal
3. Use Stripe Checkout para link de pagamento
4. Configure Webhook Stripe → n8n: evento `invoice.payment_succeeded`

---

## Custo Total Estimado

| Item | Custo |
|------|-------|
| n8n (já tem) | R$ 0 |
| VPS/VPN (já tem) | R$ 0 |
| Google Workspace (já tem) | R$ 0 |
| App Meta (já tem) | R$ 0 |
| Chip virgem para WhatsApp | R$ 15–30 (único) |
| WhatsApp Cloud API (até 1.000 conv./mês) | R$ 0 (gratuito) |
| WhatsApp Cloud API (acima de 1.000) | ~US$ 0,01/conversa |
| Replicate (IA) — créditos iniciais | US$ 10 (~833 gerações) |
| MercadoPago / Stripe | Taxa sobre transação (~4%) |
| **TOTAL PARA COMEÇAR** | **~R$ 70–100** |

---

## Cronograma de Execução

| Semana | O que fazer | Horas |
|--------|-------------|-------|
| **1** | WhatsApp Cloud API + Webhook n8n funcionando | 6–8h |
| **2** | Integração Replicate + testes de fusão de imagens | 10–14h |
| **3** | Lógica de estados + Google Sheets Alpha/Beta | 8–10h |
| **4** | Gateway de pagamento + plano Omega + testes finais | 6–8h |

---

## Próximos Passos

```
[ ] Gerar Token Permanente via Usuário do Sistema (Business Manager)
[ ] Criar Webhook no n8n e copiar a URL
[ ] Registrar URL do webhook no painel da Meta
[ ] Configurar resposta ao hub.challenge no n8n
[ ] Assinar evento "messages" no webhook
[ ] Testar envio para número pessoal (com número de teste)
[ ] Criar conta no Replicate e adicionar US$ 10
[ ] Criar planilha Google Sheets com estrutura de usuários
[ ] [Com chip] Adicionar número real e verificar via SMS
[ ] [Semana 4] Integrar gateway de pagamento
```
