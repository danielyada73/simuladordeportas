import json
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .llm import complete_json, complete_text


SCOPES = ["https://www.googleapis.com/auth/adwords"]
API_VERSION = os.environ.get("GOOGLE_ADS_API_VERSION", "v23")
BASE_URL = f"https://googleads.googleapis.com/{API_VERSION}"


def format_customer_id(customer_id: str) -> str:
    customer_id = str(customer_id or "")
    customer_id = "".join(char for char in customer_id if char.isdigit())
    return customer_id.zfill(10) if customer_id else ""


def micros(reais: float) -> int:
    return int(round(float(reais) * 1_000_000))


def parse_json(value: Any) -> Any:
    if isinstance(value, str):
        clean = value.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    return value


def _credentials_path() -> str:
    return os.getenv("GOOGLE_ADS_CREDENTIALS_PATH", "").strip()


def _credentials_json() -> str:
    return os.getenv("GOOGLE_ADS_CREDENTIALS_JSON", "").strip()


def _developer_token() -> str:
    return os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()


def _login_customer_id() -> str:
    return format_customer_id(os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").strip())


def _auth_type() -> str:
    return os.getenv("GOOGLE_ADS_AUTH_TYPE", "oauth").strip().lower() or "oauth"


def _load_credentials_from_env_json() -> Optional[Credentials]:
    raw = _credentials_json()
    if not raw:
        return None
    data = json.loads(raw)
    if _auth_type() == "service_account":
        creds = service_account.Credentials.from_service_account_info(data, scopes=SCOPES)
        impersonation_email = os.getenv("GOOGLE_ADS_IMPERSONATION_EMAIL", "").strip()
        if impersonation_email:
            creds = creds.with_subject(impersonation_email)
        return creds
    if "installed" in data or "web" in data:
        return _oauth_credentials_from_client_config(data)
    return Credentials.from_authorized_user_info(data, SCOPES)


def _load_credentials_from_refresh_token_env() -> Optional[Credentials]:
    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "").strip()
    if not client_id or not client_secret or not refresh_token:
        return None
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def _oauth_credentials_from_client_config(client_config: Dict[str, Any]) -> Credentials:
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    return flow.run_local_server(port=0)


def get_credentials():
    creds = _load_credentials_from_env_json() or _load_credentials_from_refresh_token_env()
    path = _credentials_path()

    if creds and creds.valid:
        return creds

    if _auth_type() == "service_account":
        if creds:
            return creds
        if not path or not os.path.exists(path):
            raise ValueError("GOOGLE_ADS_CREDENTIALS_PATH or GOOGLE_ADS_CREDENTIALS_JSON must be configured")
        sa_creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
        impersonation_email = os.getenv("GOOGLE_ADS_IMPERSONATION_EMAIL", "").strip()
        if impersonation_email:
            sa_creds = sa_creds.with_subject(impersonation_email)
        return sa_creds

    client_config = None
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        if "installed" in loaded or "web" in loaded:
            client_config = loaded
        else:
            creds = Credentials.from_authorized_user_info(loaded, SCOPES)

    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None

    if not creds:
        if not client_config:
            client_id = os.getenv("GOOGLE_ADS_CLIENT_ID", "").strip()
            client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "").strip()
            if not client_id or not client_secret:
                raise ValueError("Missing Google Ads OAuth credentials.")
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
        creds = _oauth_credentials_from_client_config(client_config)
        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(creds.to_json())

    return creds


def get_headers(creds) -> Dict[str, str]:
    developer_token = _developer_token()
    if not developer_token:
        raise ValueError("Missing GOOGLE_ADS_DEVELOPER_TOKEN")
    if not creds.valid:
        creds.refresh(Request())
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "developer-token": developer_token,
        "content-type": "application/json",
    }
    login_customer_id = _login_customer_id()
    if login_customer_id:
        headers["login-customer-id"] = login_customer_id
    return headers


def google_ads_request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    creds = get_credentials()
    headers = get_headers(creds)
    response = requests.request(method, f"{BASE_URL}{path}", headers=headers, json=body, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(response.text)
    if not response.text:
        return {}
    return response.json()


def mutate(customer_id: str, resource: str, operations: List[Dict[str, Any]], validate_only: bool = False) -> Dict[str, Any]:
    body: Dict[str, Any] = {"operations": operations}
    if validate_only:
        body["validateOnly"] = True
    return google_ads_request("POST", f"/customers/{format_customer_id(customer_id)}/{resource}:mutate", body)


def execute_gaql(customer_id: str, query: str) -> Dict[str, Any]:
    return google_ads_request("POST", f"/customers/{format_customer_id(customer_id)}/googleAds:search", {"query": query})


def first_result_resource_name(response: Dict[str, Any], label: str) -> str:
    results = response.get("results") or []
    if not results:
        raise RuntimeError(f"{label} mutate returned no results")
    resource_name = results[0].get("resourceName")
    if not resource_name:
        raise RuntimeError(f"{label} mutate did not include resourceName")
    return resource_name


def campaign_bidding_payload(strategy: str, target_cpa_reais: Optional[float]) -> Dict[str, Any]:
    if strategy == "MANUAL_CPC":
        return {"manualCpc": {}}
    if strategy == "MAXIMIZE_CONVERSIONS":
        return {"maximizeConversions": {}}
    if strategy == "TARGET_CPA":
        return {"targetCpa": {"targetCpaMicros": micros(target_cpa_reais or 0)}}
    raise ValueError(f"Unsupported bidding strategy: {strategy}")


def validate_headlines_descriptions(headlines: List[str], descriptions: List[str]):
    if len(headlines) != 15:
        raise ValueError("Responsive search ads require exactly 15 headlines.")
    if len(descriptions) != 4:
        raise ValueError("Responsive search ads require exactly 4 descriptions.")
    too_long_headlines = [text for text in headlines if len(text) > 30]
    too_long_descriptions = [text for text in descriptions if len(text) > 90]
    if too_long_headlines:
        raise ValueError(f"Headlines over 30 characters: {too_long_headlines}")
    if too_long_descriptions:
        raise ValueError(f"Descriptions over 90 characters: {too_long_descriptions}")


def query_first_constant(customer_id: str, query: str, entity_name: str) -> Optional[str]:
    response = execute_gaql(customer_id, query)
    results = response.get("results") or []
    if not results:
        return None
    entity = results[0].get(entity_name) or {}
    return entity.get("resourceName")


def find_geo_target(customer_id: str, country_name: str) -> Optional[str]:
    country = country_name.replace("'", "\\'")
    query = f"""
        SELECT geo_target_constant.resource_name, geo_target_constant.name, geo_target_constant.target_type
        FROM geo_target_constant
        WHERE geo_target_constant.name = '{country}'
        AND geo_target_constant.target_type = 'Country'
        LIMIT 1
    """
    return query_first_constant(customer_id, query, "geoTargetConstant")


def find_language(customer_id: str, language_name: str) -> Optional[str]:
    language = language_name.replace("'", "\\'")
    query = f"""
        SELECT language_constant.resource_name, language_constant.name
        FROM language_constant
        WHERE language_constant.name = '{language}'
        LIMIT 1
    """
    return query_first_constant(customer_id, query, "languageConstant")


def create_campaign_criteria(customer_id: str, campaign_resource: str, geo_targets: List[str], language: str, validate_only: bool) -> Dict[str, Any]:
    operations = []
    for country in geo_targets:
        resource_name = country if str(country).startswith("geoTargetConstants/") else find_geo_target(customer_id, country)
        if not resource_name:
            raise RuntimeError(f"Geo target not found: {country}")
        operations.append({"create": {"campaign": campaign_resource, "location": {"geoTargetConstant": resource_name}}})

    language_resource = language if str(language).startswith("languageConstants/") else find_language(customer_id, language)
    if not language_resource:
        raise RuntimeError(f"Language not found: {language}")
    operations.append({"create": {"campaign": campaign_resource, "language": {"languageConstant": language_resource}}})
    return mutate(customer_id, "campaignCriteria", operations, validate_only)


def extract_payload_from_text(source_text: str, client_name: str = "") -> Dict[str, Any]:
    prompt = f"""
Voce e um Especialista Senior em Google Ads API com foco em automacao multi-conta via MCC.

Sua tarefa e gerar um JSON tecnico completo e validado, pronto para ser processado por um sistema automatizado que:

Pode criar uma nova conta Google Ads dentro de uma MCC
Pode usar uma conta existente
Pode criar campanhas, grupos, keywords, anuncios e segmentacoes automaticamente

REGRAS OBRIGATORIAS:
Nao use hifen no customer_id.
Valores monetarios devem ser numericos simples (ex: 150, nao 150.00).
Paises devem estar em ingles.
Keywords devem conter:
texto
match_type (EXACT | PHRASE | BROAD)
Cada anuncio deve conter:
15 headlines (maximo 30 caracteres cada)
4 descriptions (maximo 90 caracteres cada)
final_url
path1
path2
Estrategia de lance deve ser uma das:
MANUAL_CPC
MAXIMIZE_CONVERSIONS
TARGET_CPA
Se estrategia for TARGET_CPA, incluir target_cpa_reais.
Idioma deve estar em ingles (ex: English, Portuguese).
Nao inclua markdown.
Retorne apenas JSON valido.
Nao inclua comentarios.
Todos os arrays devem conter pelo menos 1 item valido.
Se a conta for nova, deixe customer_id vazio ("").

ESTRUTURA OBRIGATORIA:
{{
"cliente": {{
"nome": "",
"customer_id": "",
"landing_page_url": "",
"conversion_action": {{
"nome": "",
"category": "SUBMIT_LEAD_FORM | PURCHASE | SIGNUP | CONTACT",
"valor_padrao_reais": 0
}},
"configuracao_conta": {{
"descriptive_name": "",
"currency_code": "ISO 4217",
"time_zone": "IANA format ex: Europe/Lisbon",
"pais_faturamento": "Country in English"
}}
}},
"campanhas": [
{{
"nome_campanha": "",
"tipo": "SEARCH",
"status_inicial": "PAUSED",
"orcamento_diario_reais": 0,
"estrategia_lance": "",
"target_cpa_reais": 0,
"geo_targets": [
"Country in English"
],
"idioma": "Language in English",
"grupos_anuncios": [
{{
"nome_grupo": "",
"lance_cpc_max_reais": 0,
"keywords": [
{{
"texto": "",
"match_type": ""
}}
],
"keywords_negativas": [
""
],
"anuncios": [
{{
"headlines": [],
"descriptions": [],
"final_url": "",
"path1": "",
"path2": ""
}}
]
}}
]
}}
]
}}

COMPORTAMENTO OBRIGATORIO:
Se o cliente for novo, deixar "customer_id": "".
Se for conta existente, preencher customer_id apenas com numeros.
Sempre preencher configuracao_conta mesmo que customer_id exista.
Garantir coerencia entre idioma e geo_targets.
Garantir pelo menos 5 keywords por grupo.
Garantir exatamente 15 headlines por anuncio.
Garantir exatamente 4 descriptions por anuncio.
Garantir que todos os textos estejam dentro dos limites de caracteres do Google Ads.
Garantir que campanhas iniciem como PAUSED.
Nao incluir nenhum campo fora da estrutura definida.

OBJETIVO:
O JSON gerado deve permitir que um sistema automatizado crie conta, acao de conversao, orcamento, campanha, grupos, keywords, anuncios, geo e idioma.

Cliente: {client_name}

TEXTO DA CAMPANHA:
{source_text}
"""
    return complete_json(prompt)


def publish_search_structure(payload_json: Any, manager_customer_id: str = "", validate_only: bool = False) -> Dict[str, Any]:
    payload = parse_json(payload_json)
    cliente = payload["cliente"]
    customer_id = format_customer_id(cliente.get("customer_id"))

    created: Dict[str, Any] = {
        "validate_only": validate_only,
        "cliente": cliente.get("nome"),
        "customer_id": customer_id,
        "conversion_action": None,
        "campaigns": [],
    }

    if not customer_id:
        manager_id = format_customer_id(manager_customer_id or _login_customer_id())
        customer_response = google_ads_request(
            "POST",
            f"/customers/{manager_id}:createCustomerClient",
            {
                "customerClient": {
                    "descriptiveName": cliente["configuracao_conta"]["descriptive_name"],
                    "currencyCode": cliente["configuracao_conta"]["currency_code"],
                    "timeZone": cliente["configuracao_conta"]["time_zone"],
                },
                "validateOnly": validate_only,
            },
        )
        created["customer_client"] = customer_response
        if validate_only:
            customer_id = manager_id
            created["customer_id"] = "validate_only"
        else:
            resource_name = customer_response["resourceName"]
            customer_id = format_customer_id(resource_name.split("/")[-1])
            created["customer_id"] = customer_id

    conversion = cliente["conversion_action"]
    conversion_response = mutate(
        customer_id,
        "conversionActions",
        [
            {
                "create": {
                    "name": conversion["nome"],
                    "category": conversion["category"],
                    "type": "WEBPAGE",
                    "status": "ENABLED",
                    "valueSettings": {
                        "defaultValue": float(conversion.get("valor_padrao_reais", 0)),
                        "alwaysUseDefaultValue": True,
                    },
                }
            }
        ],
        validate_only,
    )
    created["conversion_action"] = conversion_response

    for campaign in payload["campanhas"]:
        budget_response = mutate(
            customer_id,
            "campaignBudgets",
            [{"create": {"name": f"{campaign['nome_campanha']} - Budget", "amountMicros": micros(campaign["orcamento_diario_reais"]), "explicitlyShared": False}}],
            validate_only,
        )
        budget_resource = first_result_resource_name(budget_response, "campaign budget")

        campaign_payload = {
            "name": campaign["nome_campanha"],
            "advertisingChannelType": "SEARCH",
            "status": "PAUSED",
            "campaignBudget": budget_resource,
            "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING",
            "networkSettings": {
                "targetGoogleSearch": True,
                "targetSearchNetwork": True,
                "targetContentNetwork": False,
                "targetPartnerSearchNetwork": False,
            },
        }
        campaign_payload.update(campaign_bidding_payload(campaign["estrategia_lance"], campaign.get("target_cpa_reais", 0)))
        campaign_response = mutate(customer_id, "campaigns", [{"create": campaign_payload}], validate_only)
        campaign_resource = first_result_resource_name(campaign_response, "campaign")

        criteria_response = create_campaign_criteria(customer_id, campaign_resource, campaign["geo_targets"], campaign["idioma"], validate_only)

        campaign_result = {
            "name": campaign["nome_campanha"],
            "budget": budget_response,
            "campaign": campaign_response,
            "criteria": criteria_response,
            "ad_groups": [],
        }

        for group in campaign["grupos_anuncios"]:
            ad_group_response = mutate(
                customer_id,
                "adGroups",
                [{"create": {"name": group["nome_grupo"], "campaign": campaign_resource, "status": "ENABLED", "type": "SEARCH_STANDARD", "cpcBidMicros": micros(group["lance_cpc_max_reais"])}}],
                validate_only,
            )
            ad_group_resource = first_result_resource_name(ad_group_response, "ad group")

            keyword_operations = []
            for keyword in group["keywords"]:
                keyword_operations.append(
                    {
                        "create": {
                            "adGroup": ad_group_resource,
                            "status": "ENABLED",
                            "keyword": {"text": keyword["texto"], "matchType": keyword["match_type"]},
                        }
                    }
                )
            for keyword in group.get("keywords_negativas", []):
                keyword_operations.append(
                    {"create": {"adGroup": ad_group_resource, "negative": True, "keyword": {"text": keyword, "matchType": "BROAD"}}}
                )
            keywords_response = mutate(customer_id, "adGroupCriteria", keyword_operations, validate_only)

            ad_responses = []
            for ad in group["anuncios"]:
                validate_headlines_descriptions(ad["headlines"], ad["descriptions"])
                ad_response = mutate(
                    customer_id,
                    "adGroupAds",
                    [
                        {
                            "create": {
                                "adGroup": ad_group_resource,
                                "status": "PAUSED",
                                "ad": {
                                    "finalUrls": [ad["final_url"]],
                                    "responsiveSearchAd": {
                                        "headlines": [{"text": text} for text in ad["headlines"]],
                                        "descriptions": [{"text": text} for text in ad["descriptions"]],
                                        "path1": ad.get("path1", ""),
                                        "path2": ad.get("path2", ""),
                                    },
                                },
                            }
                        }
                    ],
                    validate_only,
                )
                ad_responses.append(ad_response)

            campaign_result["ad_groups"].append(
                {
                    "name": group["nome_grupo"],
                    "ad_group": ad_group_response,
                    "keywords": keywords_response,
                    "ads": ad_responses,
                }
            )

        created["campaigns"].append(campaign_result)

    return created


def _resolve_period(period: str) -> Tuple[str, str]:
    period = str(period or "30d").strip().lower()
    today = date.today()
    if period in ("diaria", "diario", "hoje", "1d"):
        start = today
    elif period in ("semanal", "7d"):
        start = today - timedelta(days=7)
    elif period in ("mensal", "30d"):
        start = today - timedelta(days=30)
    elif period in ("trimestral", "90d"):
        start = today - timedelta(days=90)
    elif period in ("semestral", "180d"):
        start = today - timedelta(days=180)
    elif period in ("anual", "365d"):
        start = today - timedelta(days=365)
    else:
        raise ValueError("Periodo invalido. Use diaria, semanal, mensal, trimestral, semestral ou anual.")
    return start.isoformat(), today.isoformat()


def fetch_campaign_metrics(customer_id: str, period: str) -> Dict[str, Any]:
    start, end = _resolve_period(period)
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          metrics.impressions,
          metrics.clicks,
          metrics.ctr,
          metrics.average_cpc,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY metrics.cost_micros DESC
    """
    raw = execute_gaql(customer_id, query)
    campaigns = []
    for row in raw.get("results") or []:
        campaign = row.get("campaign") or {}
        metrics = row.get("metrics") or {}
        campaigns.append(
            {
                "id": campaign.get("id"),
                "name": campaign.get("name"),
                "status": campaign.get("status"),
                "impressions": int(metrics.get("impressions") or 0),
                "clicks": int(metrics.get("clicks") or 0),
                "ctr": float(metrics.get("ctr") or 0),
                "average_cpc": float(metrics.get("averageCpc") or 0) / 1_000_000 if metrics.get("averageCpc") else 0,
                "cost_reais": float(metrics.get("costMicros") or 0) / 1_000_000,
                "conversions": float(metrics.get("conversions") or 0),
                "conversions_value": float(metrics.get("conversionsValue") or 0),
            }
        )
    return {"period": period, "start": start, "end": end, "campaigns": campaigns, "raw": raw}


def summarize_metrics(metrics: Dict[str, Any], client_name: str, period: str) -> str:
    prompt = f"""
Analise estes dados reais de Google Ads e me devolva um relatorio executivo curto em portugues.

Cliente: {client_name}
Periodo: {period}
Dados:
{json.dumps(metrics.get("campaigns", []), ensure_ascii=False)}

Quero:
- veredito geral
- campanhas vencedoras
- gargalos claros
- 3 proximas acoes objetivas

Fale como diretor de trafego senior. Seja direto.
"""
    return complete_text(prompt)
