-- Alpha OS — Supabase schema
-- Rode esse SQL no Supabase Studio → SQL Editor → New Query → Run
-- Pode rodar mais de uma vez, é idempotente.

-- ============================================================
-- 1. Cache de saldos das contas de anúncio
-- Atualizado periodicamente (cron) ou sob demanda.
-- O painel sempre lê daqui (rápido). Só atualiza quando expira.
-- ============================================================
create table if not exists balances_cache (
  id uuid primary key default gen_random_uuid(),
  client_name text not null,
  platform text not null check (platform in ('meta', 'google')),
  account_id text not null,
  funding_balance numeric,         -- saldo carregado (fundos)
  spend_cap numeric,                -- limite total
  amount_spent numeric,             -- gasto até agora no ciclo
  daily_budget numeric,             -- soma dos orçamentos diários ativos
  currency text default 'BRL',
  runway_days numeric,              -- saldo / daily_budget
  status text check (status in ('ok', 'attention', 'critical')),
  last_synced_at timestamptz default now(),
  raw_payload jsonb,
  unique (client_name, platform, account_id)
);

create index if not exists balances_cache_client_idx on balances_cache (client_name);
create index if not exists balances_cache_status_idx on balances_cache (status);

-- ============================================================
-- 2. Memória do agente (por usuário do WhatsApp)
-- Replica o padrão memory.md do Claude Cowork.
-- Cada usuário (Daniel/Jefferson/Gustavo) tem seu próprio arquivo.
-- ============================================================
create table if not exists agent_memory (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,             -- número WhatsApp normalizado, ex: 5511999999999
  user_name text,                    -- Daniel, Jefferson, Gustavo
  memory_type text not null,         -- 'preference', 'fact', 'instruction'
  content text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists agent_memory_user_idx on agent_memory (user_id);

-- ============================================================
-- 3. Log de ações do agente (auditoria)
-- Toda ação Monday/Meta/Google que o agente executar fica aqui.
-- ============================================================
create table if not exists agent_actions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  user_name text,
  intent text not null,              -- 'create_task', 'change_status', 'add_update', etc
  target_type text,                  -- 'monday_item', 'meta_campaign', etc
  target_id text,
  parameters jsonb,
  result jsonb,
  status text check (status in ('success', 'error', 'pending_confirmation')),
  created_at timestamptz default now()
);

create index if not exists agent_actions_user_idx on agent_actions (user_id, created_at desc);

-- ============================================================
-- 4. Acesso do cliente final ao painel individual
-- Cada cliente recebe um token único para acessar SEU painel.
-- Sem token, não vê nada. Token != token de outro cliente.
-- ============================================================
create table if not exists client_access (
  id uuid primary key default gen_random_uuid(),
  client_name text not null unique,  -- bate com nome no Monday
  access_token text not null unique, -- gerado: gen_random_uuid()
  contact_name text,
  contact_email text,
  contact_phone text,
  is_active boolean default true,
  created_at timestamptz default now(),
  last_login_at timestamptz
);

create index if not exists client_access_token_idx on client_access (access_token) where is_active = true;

-- ============================================================
-- 5. Config por cliente (mapeia cliente Monday → contas Meta/Google)
-- Substituí o JSON em alpha_os/store.py por isso pra ficar fonte única.
-- ============================================================
create table if not exists client_config (
  id uuid primary key default gen_random_uuid(),
  client_name text not null unique,
  meta_ad_account_id text,
  meta_page_id text,
  google_customer_id text,
  google_manager_customer_id text,
  landing_page_url text,
  monthly_budget numeric,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================================
-- 6. Cache do Monday (snapshot completo)
-- Job sync periodico faz UMA query pesada no Monday, salva aqui.
-- Painel sempre le daqui (zero consumo de Monday por usuario).
-- ============================================================
create table if not exists monday_snapshot (
  id uuid primary key default gen_random_uuid(),
  kind text unique not null,        -- 'tasks_full' (todo o list_all_tasks)
  payload jsonb not null,           -- dados brutos
  item_count int default 0,
  last_synced_at timestamptz default now(),
  duration_ms int,
  status text check (status in ('ok', 'error')),
  error text
);

create index if not exists monday_snapshot_kind_idx on monday_snapshot (kind);

-- ============================================================
-- RLS (Row Level Security) — manter desligado por enquanto
-- A API do backend usa service_role key (bypassa RLS).
-- Vamos ligar quando expor leitura direta pro frontend do cliente.
-- ============================================================
