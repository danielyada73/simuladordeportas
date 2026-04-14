# Estrutura do Google Sheets — Simulador de Ambientes

Banco de dados usando Google Sheets para controle de usuários, créditos e planos.

---

## Planilha: `simulador-db`

### Aba 1: Usuarios

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| A — `numero_whatsapp` | String | Número no formato internacional | `5511999999999` |
| B — `plano` | String | alpha / beta / omega | `alpha` |
| C — `creditos_restantes` | Número | Créditos disponíveis para gerar | `2` |
| D — `total_geracoes` | Número | Total histórico de gerações | `0` |
| E — `estado` | String | Estado atual na conversa | `AGUARDANDO_AMBIENTE` |
| F — `foto_ambiente_id` | String | media_id temporário da foto 1 | `wamid.xxx` |
| G — `foto_porta_id` | String | media_id temporário da foto 2 | `wamid.yyy` |
| H — `data_cadastro` | Data | Data de primeiro contato | `14/04/2026` |
| I — `data_ultimo_acesso` | Data | Última interação | `14/04/2026` |
| J — `email` | String | Email (opcional, para Omega) | `cliente@email.com` |

**Dados de exemplo:**
```
5511999999999 | alpha | 2 | 0 | AGUARDANDO_AMBIENTE | | | 14/04/2026 | 14/04/2026 |
5511888888888 | beta  | 3 | 2 | AGUARDANDO_PORTA    | | | 10/04/2026 | 14/04/2026 |
5511777777777 | omega | 47| 3 | AGUARDANDO_AMBIENTE | | | 05/04/2026 | 14/04/2026 |
```

---

### Estados Válidos

| Estado | Descrição |
|--------|-----------|
| `AGUARDANDO_AMBIENTE` | Bot pediu a foto do ambiente, aguardando resposta |
| `AGUARDANDO_PORTA` | Bot pediu a foto da porta, aguardando resposta |
| `GERANDO` | IA está processando (evita duplo processamento) |
| `CONCLUIDO` | Última geração concluída com sucesso |
| `SEM_CREDITOS` | Usuário sem créditos, aguardando upgrade |

---

### Aba 2: Planos

| Coluna | Descrição |
|--------|-----------|
| A — `plano` | Nome do plano |
| B — `creditos_iniciais` | Créditos ao criar conta ou renovar |
| C — `valor_mensal` | Valor em reais (0 = gratuito) |
| D — `descricao` | Descrição para o cliente |

**Dados:**
```
alpha | 2  | 0  | 2 simulações gratuitas para conhecer o serviço
beta  | 5  | 0  | 5 simulações gratuitas para parceiros
omega | 50 | 97 | 50 simulações por mês — acesso completo
```

---

### Aba 3: Transacoes

Registro de pagamentos e upgrades de plano.

| Coluna | Descrição |
|--------|-----------|
| A — `numero_whatsapp` | Número do cliente |
| B — `plano_anterior` | Plano antes do upgrade |
| C — `plano_novo` | Novo plano |
| D — `valor_pago` | Valor em reais |
| E — `gateway` | mercadopago / stripe |
| F — `payment_id` | ID da transação no gateway |
| G — `data` | Data/hora da transação |

---

## Configuração no n8n

### Credencial Google Sheets

1. No n8n, vá em **Credentials → Add Credential**
2. Selecione **Google Sheets OAuth2**
3. Siga o fluxo de autenticação com sua conta do Google Workspace

### IDs Necessários

```
Document ID: [aparece na URL da planilha: /spreadsheets/d/XXXXX/edit]
Sheet Name: Usuarios
```

### Operações Usadas

| Operação | Quando usar |
|----------|-------------|
| `Read Rows` | Buscar usuário pelo número |
| `Append Row` | Criar novo usuário |
| `Update Row` | Atualizar estado, créditos, etc. |

---

## Fórmulas Úteis na Planilha

### Dashboard de estatísticas (aba separada)

```
Total de usuários:          =COUNTA(Usuarios!A2:A)
Total Alpha:                =COUNTIF(Usuarios!B2:B,"alpha")
Total Beta:                 =COUNTIF(Usuarios!B2:B,"beta")
Total Omega (pagantes):     =COUNTIF(Usuarios!B2:B,"omega")
Total de gerações feitas:   =SUM(Usuarios!D2:D)
Custo estimado IA (USD):    =SUM(Usuarios!D2:D)*0.012
Receita Omega (mês):        =COUNTIF(Usuarios!B2:B,"omega")*97
```
