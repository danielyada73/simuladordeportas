"""
config.py — Configurações e constantes do Simulador de Portas
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ENABLED   = os.getenv("TELEGRAM_ENABLED", "True").lower() == "true"

# ─── Google Sheets ────────────────────────────────────────────────────────────
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON  = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")

# ─── Gemini / Google AI ──────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── Replicate (fallback) ─────────────────────────────────────────────────────
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# ─── Storage temporário ───────────────────────────────────────────────────────
TEMP_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "temp_images")
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

# ─── Planos de Acesso ────────────────────────────────────────────────────────
PLANS = {
    "alpha": {"credits": 10,  "label": "Alpha",  "paid": False},
    "beta":  {"credits": 20,  "label": "Beta",   "paid": False},
    "omega": {"credits": 200, "label": "Omega",  "paid": True},
}
DEFAULT_PLAN  = "alpha"

# ─── Estados da Conversa ─────────────────────────────────────────────────────
class State:
    NOVO               = "NOVO"
    AGUARDANDO_AMBIENTE = "AGUARDANDO_AMBIENTE"
    AGUARDANDO_PORTA    = "AGUARDANDO_PORTA"
    GERANDO             = "GERANDO"
    AGUARDANDO_FEEDBACK = "AGUARDANDO_FEEDBACK"
    ENCERRADO           = "ENCERRADO"
    SEM_CREDITOS        = "SEM_CREDITOS"

# ─── Mensagens do Bot ─────────────────────────────────────────────────────────
class Msg:
    BOAS_VINDAS = (
        "Olá\\! 👋 Seja bem\\-vindo ao *Simulador de Portas*\\!\n\n"
        "Aqui você pode ver como ficaria o seu ambiente com a porta que deseja instalar\\.\n\n"
        "📸 Vamos começar\\! Envie a foto do *ambiente* onde você quer instalar a porta\\.\n"
        "_\\(Ex\\: entrada da casa, quarto, corredor, sala\\)_\n\n"
        "💡 *Dica:* Foto bem iluminada, mostrando a porta atual, quanto mais clara melhor\\!"
    )

    BOAS_VINDAS_RETORNO = (
        "Olá, *{nome}*\\! 😊 Que bom te ver de volta\\!\n\n"
        "Você tem *{creditos}* simulação\\(ões\\) disponível\\(eis\\) no plano *{plano}*\\.\n\n"
        "Quer fazer uma nova simulação? Envie a foto do *ambiente*\\!"
    )

    PEDIU_NOME = (
        "Olá\\! 👋 Prazer em te conhecer\\!\n\n"
        "Antes de continuar, qual é o seu nome?"
    )

    PEDIR_PORTA = (
        "✅ Foto do ambiente recebida\\!\n\n"
        "Agora envie a foto do *modelo de porta* que você deseja experimentar\\.\n"
        "_\\(Dica: foto da porta com fundo claro e porta centralizada\\)_"
    )

    GERANDO = (
        "⏳ *Gerando a simulação\\.\\.\\.*\n\n"
        "Estou processando as imagens com inteligência artificial\\.\n"
        "Aguarde alguns instantes\\!"
    )

    RESULTADO = (
        "✅ *Aqui está seu ambiente com a nova porta instalada\\!*\n\n"
        "O que você achou? Escolha uma opção:"
    )

    MENU_FEEDBACK = (
        "1️⃣ Gerar novamente \\(mesmas fotos, novo resultado\\)\n"
        "2️⃣ Simular outro ambiente \\(enviar novas fotos\\)\n"
        "3️⃣ Estou satisfeito\\! Encerrar atendimento"
    )

    ENCERRAMENTO = (
        "Obrigado por usar o *Simulador de Portas*\\! 🚪\n\n"
        "Ficou satisfeito com o resultado\\? Entre em contato para fechar o pedido\\!\n\n"
        "_Até logo\\! 👋_"
    )

    SEM_CREDITOS = (
        "❌ Você usou todas as suas *{creditos_total}* simulações do plano *{plano}*\\.\n\n"
        "Para continuar gerando simulações, faça upgrade para o *Plano Omega* com *200 gerações*\\:\n\n"
        "🔗 \\[Link de assinatura\\] \\(em breve\\)\n\n"
        "Ou entre em contato conosco para mais informações\\!"
    )

    AGUARDANDO_IMAGEM = (
        "📸 Por favor, envie uma *imagem* \\(foto\\)\\.\n"
        "Não consigo processar esse tipo de arquivo agora\\."
    )

    ERRO_GERACAO = (
        "😔 Ops\\! Houve um problema ao gerar a imagem\\.\n\n"
        "Por favor, tente novamente em instantes\\.\n"
        "Se o problema persistir, entre em contato conosco\\."
    )

    OPCAO_INVALIDA = (
        "Por favor, escolha uma das opções:\n\n"
        "Digite *1*, *2* ou *3*\\."
    )
