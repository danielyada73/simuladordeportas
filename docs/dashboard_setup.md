# Dashboard Alpha OS — Setup completo

Guia passo a passo pra subir o painel (Vercel) + a API (Render) + o agente WhatsApp Caim (segundo Render).

---

## 0. Antes de tudo: revogue o token da Meta

Você compartilhou o token permanente do WhatsApp em chat. **Vá agora em**:

Meta Business Manager → Configurações da Empresa → Usuários do Sistema → seu user → Tokens de Acesso → **Revogar** o token atual → Gerar novo.

Use o novo token só nas variáveis de ambiente do Render. Nunca em arquivo do repo.

---

## 1. Supabase

1. Acesse [supabase.com](https://supabase.com) → seu projeto `xxfamyzffuliqelljatl`
2. SQL Editor → New Query → cola o conteúdo de `supabase/schema.sql` → **Run**
3. Vai em **Project Settings → API** e copia:
   - `Project URL` → vai virar `SUPABASE_URL`
   - `service_role key` (não a anon!) → vai virar `SUPABASE_SERVICE_KEY`
4. Guarda esses dois valores. Nunca commite o `service_role`.

---

## 2. Render — API Alpha OS (serviço existente)

No serviço **existente** (`simuladordeportas` no Render), adiciona/atualiza estas envs:

```
DASHBOARD_API_TOKEN=<gera uma string aleatoria forte, ex: openssl rand -hex 32>
DASHBOARD_ALLOWED_ORIGINS=https://SEU-PROJETO.vercel.app
SUPABASE_URL=https://xxfamyzffuliqelljatl.supabase.co
SUPABASE_SERVICE_KEY=<service_role do supabase>
```

Mantém todas as envs já existentes (MONDAY_API_TOKEN, etc).

Depois do deploy, valida:

```
curl https://SEU-RENDER.onrender.com/api/health
# deve retornar {"status":"ok",...}

curl -H "Authorization: Bearer SEU_DASHBOARD_API_TOKEN" \
     "https://SEU-RENDER.onrender.com/api/tasks?window=today"
# deve retornar JSON com tarefas do Monday
```

---

## 3. Vercel — Dashboard Next.js

### 3.1 Subir o código no GitHub

Como o `dashboard/` está no mesmo repo (`simuladordeportas`), você não precisa de repo separado.

### 3.2 Criar projeto na Vercel

1. [vercel.com/new](https://vercel.com/new) → Import Git Repository → escolhe `simuladordeportas`
2. Em **Configure Project**:
   - **Root Directory**: clica em Edit → seleciona `dashboard`
   - **Framework Preset**: Next.js (auto-detecta)
   - **Build Command**: deixa padrão (`next build`)
3. Em **Environment Variables**, adiciona:
   ```
   API_BASE_URL=https://SEU-RENDER.onrender.com
   API_TOKEN=<o mesmo DASHBOARD_API_TOKEN do Render>
   DASHBOARD_PASSWORD=<senha forte pra acessar o painel>
   ```
4. Deploy.

Vai gerar URL tipo `alpha-os-dashboard-xxxx.vercel.app`. Acessa, faz login com a senha → painel aparece.

### 3.3 Liberar CORS no Render

Depois que tiver a URL final da Vercel, volta no Render e atualiza:

```
DASHBOARD_ALLOWED_ORIGINS=https://alpha-os-dashboard-xxxx.vercel.app
```

Reinicia o serviço.

---

## 4. Render — Agente Caim (segundo serviço)

### 4.1 Criar serviço novo no Render

1. Render dashboard → **New** → **Web Service**
2. Conecta o mesmo repo `simuladordeportas`
3. Configurações:
   - **Name**: `alpha-os-agent` (vai virar `alpha-os-agent.onrender.com`)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r bot/requirements.txt`
   - **Start Command**: `uvicorn whatsapp.agent_server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Starter ($7/mês) — não use Free, dorme em 15min.

### 4.2 Variáveis de ambiente

```
AGENT_WHATSAPP_TOKEN=<NOVO token permanente Meta — o que voce gerou depois de revogar>
AGENT_WHATSAPP_PHONE_NUMBER_ID=1164158606774078
AGENT_WHATSAPP_VERIFY_TOKEN=alpha_caim_2026
MONDAY_API_TOKEN=<seu token Monday principal>
ANTHROPIC_API_KEY=<sk-ant-... pega em console.anthropic.com>

# Mapeamento numero WhatsApp → usuario (preencha quando souber os numeros):
AGENT_USER_DANIEL_PHONE=5511XXXXXXXXX
AGENT_USER_JEFFERSON_PHONE=5511XXXXXXXXX
AGENT_USER_GUSTAVO_PHONE=5511XXXXXXXXX

# Opcional (Fase 3): tokens Monday individuais pra ações ficarem atribuídas certo
AGENT_USER_DANIEL_MONDAY_TOKEN=
AGENT_USER_JEFFERSON_MONDAY_TOKEN=
AGENT_USER_GUSTAVO_MONDAY_TOKEN=
```

### 4.3 Conectar webhook na Meta

Depois do serviço subir, copia a URL: `https://alpha-os-agent.onrender.com/webhook`

Meta for Developers → seu App → WhatsApp → Configuration → no número do **Caim**:
- Callback URL: `https://alpha-os-agent.onrender.com/webhook`
- Verify Token: `alpha_caim_2026` (o mesmo que você botou no Render)
- Subscribe fields: `messages`

Teste enviando mensagem do seu WhatsApp pessoal pro Caim. Vai chegar resposta de ack ("Oi Daniel, recebi sua mensagem…").

---

## 5. Estado da Fase 1

✅ Backend: 3 endpoints (`/api/tasks`, `/api/tasks/by-assignee`, `/api/clients/stages`)
✅ Frontend: 3 telas (Demandas, Responsáveis, Clientes & Etapas)
✅ Auth: senha única pra agência + middleware Next.js
✅ Auto-refresh: 60s no painel
✅ Agente Caim stub: webhook funciona, autorização por número, responde ack

### O que vem na Fase 2 (saldos)

- `/api/balances/meta` lendo direto `act_*/funding_source_details`
- `/api/balances/google` lendo `customer.account_budget`
- 4ª tela `/saldos`

### O que vem na Fase 3 (agente Claude)

- Substituir o `_handle_incoming` stub por loop de tool-calling
- Tools: `list_tasks`, `find_task`, `create_task`, `create_subtask`, `add_update`, `add_comment`, `change_status`, `get_balance`, `duplicate_template`
- Sem `delete_*`
- Memória persistente em `agent_memory` (Supabase)

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `401 Bearer token obrigatorio` | `API_TOKEN` no Vercel != `DASHBOARD_API_TOKEN` no Render | Alinha os dois |
| Tela em branco no painel | CORS bloqueando | Confere `DASHBOARD_ALLOWED_ORIGINS` no Render |
| `503 Monday indisponivel` | Token Monday inválido/expirado | Regera em monday.com → Admin → API |
| Caim não responde | Webhook não verificado | Refaz o flow do step 4.3 |
| Painel diz "Acesso restrito" | Cookie expirou | Re-login |
