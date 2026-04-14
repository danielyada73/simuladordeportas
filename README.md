# 🚪 Simulador de Ambientes — Porta na Sua Casa

> Chatbot no WhatsApp com Inteligência Artificial que mescla a foto do ambiente do cliente com o modelo de porta da loja, gerando uma visualização realista de como ficaria o ambiente após a instalação.

---

## 🎯 Como Funciona

```
Cliente envia foto do ambiente (ex: entrada da casa)
        ↓
Bot responde e pede a foto do modelo de porta escolhido
        ↓
IA faz a fusão das imagens (Stable Diffusion Inpainting)
        ↓
Cliente recebe a imagem montada de volta no WhatsApp
```

---

## 🏗️ Arquitetura

```
Cliente (WhatsApp)
       ↓
[WhatsApp Cloud API — Meta]
       ↓
[n8n — Orquestrador Central]
   ├─→ [Google Sheets — Controle de Créditos e Planos]
   ├─→ [Replicate API — IA de Inpainting]
   └─→ [Stripe / MercadoPago — Assinaturas Omega]
       ↓
Cliente recebe imagem pelo WhatsApp
```

---

## 📦 Planos de Acesso

| Plano | Créditos | Valor |
|-------|----------|-------|
| **Alpha** | 2 gerações gratuitas | Gratuito |
| **Beta** | 5 gerações gratuitas | Gratuito |
| **Omega** | 50 gerações/mês | Pago (assinatura) |

---

## 🛠️ Stack de Tecnologias

| Ferramenta | Função |
|------------|--------|
| **WhatsApp Cloud API (Meta)** | Canal de comunicação com o cliente |
| **n8n** | Orquestrador de fluxos e automações |
| **Replicate API** | IA de geração de imagens (Inpainting) |
| **Google Sheets** | Banco de dados de usuários e créditos |
| **Cloudflare R2** | Storage temporário de imagens |
| **Stripe / MercadoPago** | Gateway de pagamento para plano Omega |

---

## 📁 Estrutura do Repositório

```
simuladordeportas/
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── implementation_plan.md     # Plano completo de implementação
│   ├── whatsapp_setup.md         # Configuração do WhatsApp Cloud API
│   ├── n8n_flow.md               # Documentação do fluxo n8n
│   └── replicate_api.md          # Guia de integração com Replicate
├── n8n/
│   ├── workflow_main.json        # Workflow principal exportado do n8n
│   └── workflow_pagamento.json   # Workflow de webhook de pagamento
└── sheets/
    └── estrutura_planilha.md     # Estrutura das abas do Google Sheets
```

---

## 🚀 Setup Rápido

### Pré-requisitos

- Conta no [Meta for Developers](https://developers.facebook.com) com app existente
- n8n instalado e rodando com URL pública (VPS/VPN)
- Conta no [Replicate](https://replicate.com) com créditos
- Google Workspace com Google Sheets
- Chip virgem para número WhatsApp

### 1. Configurar WhatsApp

Siga o guia completo em [`docs/whatsapp_setup.md`](./docs/whatsapp_setup.md)

**Dados necessários:**
```
WHATSAPP_TOKEN=         # Token permanente do Usuário do Sistema
PHONE_NUMBER_ID=        # ID do número de telefone
WABA_ID=               # WhatsApp Business Account ID
WEBHOOK_VERIFY_TOKEN=  # String de verificação do webhook
```

### 2. Configurar Replicate

```bash
# Instale a SDK (opcional para testes locais)
pip install replicate

# Ou use direto via HTTP no n8n
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Importar Workflow no n8n

1. Abra seu n8n
2. Vá em Workflows → Import
3. Selecione o arquivo `n8n/workflow_main.json`
4. Configure as credenciais: WhatsApp Token, Google Sheets, Replicate

### 4. Configurar Google Sheets

Crie uma planilha com a seguinte estrutura (aba "Usuarios"):

| numero_whatsapp | plano | creditos_restantes | total_geracoes | estado | data_cadastro |
|---|---|---|---|---|---|
| 5511999999999 | alpha | 2 | 0 | AGUARDANDO_AMBIENTE | 14/04/2026 |

---

## 💰 Estimativa de Custos

| Item | Custo |
|------|-------|
| n8n + VPS | Já pago |
| Google Workspace | Já pago |
| Chip WhatsApp | R$ 15–30 (único) |
| WhatsApp API (até 1.000 conv./mês) | **Gratuito** |
| Replicate IA por geração | ~US$ 0,012/imagem |
| **Total para começar** | **~R$ 70–100** |

---

## 📅 Cronograma

| Semana | Entregável |
|--------|-----------|
| 1 | WhatsApp Cloud API configurada + Webhook n8n funcionando |
| 2 | Integração Replicate + fusão de imagens testada |
| 3 | Lógica de estados + controle de créditos Alpha/Beta |
| 4 | Gateway de pagamento + plano Omega + testes finais |

---

## ⚠️ Alertas Importantes

- **Token permanente:** Nunca use o token temporário da tela de início rápido. Gere um permanente via Usuário do Sistema no Business Manager.
- **Segurança Meta:** Ative 2FA no Business Manager. Perder acesso admin derruba toda a automação.
- **Templates:** Mensagens proativas (você → cliente) precisam de template aprovado pela Meta. Conversa livre só dentro de 24h após o cliente ter mandado mensagem.
- **Chip virgem:** O número não pode ter WhatsApp cadastrado anteriormente.

---

## 📄 Licença

Projeto privado — todos os direitos reservados.

---

*Projeto desenvolvido com n8n + WhatsApp Cloud API + Stable Diffusion Inpainting*
