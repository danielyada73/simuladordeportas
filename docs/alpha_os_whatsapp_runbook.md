# Alpha OS WhatsApp Runbook

Este documento separa o que fica no Render, o que fica no n8n e o que precisa existir nas plataformas externas para o Alpha OS operar do briefing ate a publicacao.

## 1. O que o Render faz

O servico `simuladordeportas` recebe as mensagens do WhatsApp, interpreta os comandos do Alpha OS e dispara os fluxos certos.

Comandos atuais:

- `config`
- `novo cliente Nome do Cliente`
- `status Nome ou ID`
- `rodar Nome ou ID monday`
- `rodar Nome ou ID fase2`
- `rodar Nome ou ID google`
- `rodar Nome ou ID meta`
- `validar Nome ou ID`

## 2. Variaveis do Render

Estas variaveis precisam estar no servico do Render:

- `ALPHA_OS_MODE=true`
- `WHATSAPP_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_VERIFY_TOKEN`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_CREDENTIALS_JSON`
- `MONDAY_API_TOKEN`
- `N8N_ONBOARDING_WEBHOOK_URL`
- `N8N_PHASE2_WEBHOOK_URL`
- `N8N_GOOGLE_PUBLISH_WEBHOOK_URL`
- `N8N_META_PUBLISH_WEBHOOK_URL`

Opcionais:

- `MONDAY_API_URL`
- `ALPHA_OS_ONBOARDING_PRAZO`
- `ALPHA_OS_ONBOARDING_SEGMENTO`
- `N8N_DAILY_ANALYSIS_WEBHOOK_URL`
- `N8N_WEEKLY_ANALYSIS_WEBHOOK_URL`

## 3. O que o n8n faz

O n8n continua sendo o orquestrador das tarefas pesadas e dos conectores externos.

Mapeamento atual:

- Fluxo 01 `01 - Monday Express - Alpha (1).json`
  - Cria o cliente no Monday
  - Gera o briefing no Google Docs
  - Cria os boards e grupos
- Fluxo 02 `02 - AIs Agentes da Alpha.json`
  - Gera copy de LP
  - Gera copy de criativos
  - Gera estrutura Google Ads
  - Gera estrutura Meta Ads
- Fluxo 04 `04 - IA Google Ads.json`
  - Publica Google Ads a partir do item aprovado no Monday
- Fluxo 03 `03 - Execução Meta Ads - Alpha (1).json`
  - Publica Meta Ads a partir do item aprovado no Monday

## 4. O que precisa estar configurado no n8n

Credenciais minimas:

- Monday API
- Google Docs OAuth
- Google Gemini
- Google Ads OAuth e developer token
- Meta access token do usuario do sistema

Webhooks ou endpoints ativos:

- Form URL do fluxo 01
- `/webhook/status_monday`
- `/webhook/aprovacao_campads`
- `/webhook/publicar_meta`

## 5. O que ainda depende de configuracao por cliente

Mesmo com o WhatsApp no centro, estes dados precisam existir em algum lugar:

- Conta ou MCC correta do Google Ads
- Conta de anuncio correta da Meta
- `page_id` da pagina do Facebook
- URL final da landing page
- Pixel, eventos e conversoes quando aplicavel
- Metodo de pagamento da conta

Sem isso, o Alpha OS consegue disparar os fluxos, mas a publicacao pode sair na conta errada ou com placeholders.

## 6. Fluxo operacional ideal

1. Cliente manda o briefing no WhatsApp:
   `novo cliente Nome`
2. Alpha OS registra a operacao
3. Operador roda:
   `rodar <id> monday`
4. Operador valida boards e item:
   `validar <id>`
5. Operador roda:
   `rodar <id> fase2`
6. Depois de revisar no Monday:
   `rodar <id> google`
7. Depois:
   `rodar <id> meta`

## 7. O que ainda nao esta 100 por cento automatico

- Criacao de BM na Meta
- Escolha dinamica da conta certa da Meta por cliente
- Escolha dinamica da conta certa do Google Ads por cliente
- Instalacao de tags e pixels na LP
- Analises diaria e semanal sem webhook dedicado no n8n
- Publicacao multi-plataforma com validacao de acessos antes de subir

## 8. Meta final recomendada

Deixar o WhatsApp como cockpit e o n8n como executor.

O proximo passo tecnico mais importante e padronizar os payloads de publicacao de Google e Meta para que:

- o Monday entregue sempre o mesmo formato
- o Alpha OS saiba qual conta usar
- o n8n publique sem campos hardcoded
