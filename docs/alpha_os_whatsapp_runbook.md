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
- `validar Nome ou ID`
- `definir Nome ou ID common.landing_page_url https://site.com`
- `definir Nome ou ID google.customer_id 1234567890`
- `definir Nome ou ID google.manager_customer_id 0987654321`
- `definir Nome ou ID meta.ad_account_id 377601641828660`
- `definir Nome ou ID meta.page_id 123456789012345`
- `preparar google Nome ou ID`
- `preparar meta Nome ou ID`
- `publicar google Nome ou ID`
- `publicar meta Nome ou ID`
- `analisar google Nome ou ID mensal`
- `analisar meta Nome ou ID mensal`
- `o que falta Nome ou ID`

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

Para publicacao e analise diretas:

- `GEMINI_API_KEY` ou `OPENAI_API_KEY`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- `META_ACCESS_TOKEN`

Se ainda quiser manter os webhooks de publicacao no n8n:

- `N8N_GOOGLE_PUBLISH_WEBHOOK_URL`
- `N8N_META_PUBLISH_WEBHOOK_URL`
- `N8N_DAILY_ANALYSIS_WEBHOOK_URL`
- `N8N_WEEKLY_ANALYSIS_WEBHOOK_URL`

Opcionais:

- `MONDAY_API_URL`
- `ALPHA_OS_ONBOARDING_PRAZO`
- `ALPHA_OS_ONBOARDING_SEGMENTO`
- `GOOGLE_ADS_CREDENTIALS_JSON`
- `GOOGLE_ADS_CREDENTIALS_PATH`
- `GOOGLE_ADS_API_VERSION`
- `META_GRAPH_VERSION`

## 3. O que o n8n faz hoje

O n8n continua sendo o orquestrador das tarefas pesadas e dos conectores externos nas fases 1 e 2.

Mapeamento atual:

- Fluxo 01 `01 - Monday Express - Alpha (1).json`
  - cria o cliente no Monday
  - gera o briefing no Google Docs
  - cria os boards e grupos
- Fluxo 02 `02 - AIs Agentes da Alpha.json`
  - gera copy de LP
  - gera copy de criativos
  - gera estrutura Google Ads
  - gera estrutura Meta Ads

## 4. O que o Alpha OS ja pode fazer de forma direta

Sem depender dos fluxos 03 e 04, o servico do WhatsApp ja pode:

- localizar os itens certos no Monday
- ler o update mais recente de Google Ads
- ler o update mais recente de Meta Ads
- transformar esse texto em JSON tecnico
- publicar Google Ads em modo pausado
- publicar Meta Ads em modo pausado
- analisar Google Ads por periodo
- analisar Meta Ads por periodo

## 5. O que ainda depende de configuracao por cliente

Mesmo com o WhatsApp no centro, estes dados precisam existir em algum lugar:

- conta ou MCC correta do Google Ads
- conta de anuncio correta da Meta
- `page_id` da pagina do Facebook
- URL final da landing page
- pixel, eventos e conversoes quando aplicavel
- metodo de pagamento da conta

Sem isso, o Alpha OS consegue montar e tentar publicar, mas a publicacao pode sair na conta errada ou com placeholders.

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
   `preparar google <id>`
7. Se estiver tudo certo:
   `publicar google <id>`
8. Depois:
   `preparar meta <id>`
9. E por fim:
   `publicar meta <id>`
10. Quando quiser leitura real de performance:
   `analisar google <id> semanal`
11. Ou:
   `analisar meta <id> mensal`

## 7. O que ainda nao esta 100 por cento automatico

- criacao de BM na Meta
- escolha dinamica da conta certa da Meta por cliente
- escolha dinamica da conta certa do Google Ads por cliente
- instalacao de tags e pixels na LP
- publicacao multi-plataforma com validacao de acessos antes de subir
- leitura automatica de briefing via Google Docs quando o Monday nao tiver informacao suficiente

## 8. Meta final recomendada

Deixar o WhatsApp como cockpit, o n8n como executor das fases 1 e 2, e o Alpha OS como cerebro de operacao para:

- configuracao por cliente
- publicacao Google Ads
- publicacao Meta Ads
- analise por periodo
- status operacional da conta
