"""
core/config_niche.py — Configurações específicas do nicho (Ex: Portas).
Fácil de alterar para replicar para outros negócios.
"""

NICHE = "Portas"
NICHE_LABEL = "Simulador de Portas"

# Mensagens base
MESSAGES = {
    "welcome": (
        "Olá! 👋 Seja bem-vindo ao *{niche_label}*!\n\n"
        "Aqui você pode ver como ficaria o seu ambiente com a {niche} que deseja instalar.\n\n"
        "📸 Vamos começar! Envie a foto do *ambiente*.\n"
    ),
    "ask_item": "✅ Foto do ambiente recebida!\n\nAgora envie a foto do *modelo de {niche}* que você deseja experimentar.",
    "generating": "⏳ *Gerando a simulação...*\nAguarde alguns instantes!",
    "result": "✅ *Aqui está seu ambiente com a nova {niche} instalada!*",
    "menu": "1️⃣ Gerar novamente\n2️⃣ Simular outro ambiente\n3️⃣ Encerrar atendimento",
    "no_credits": "❌ Você usou todas as suas simulações do plano *{plano}*.\n\nFaça upgrade para o *Plano Omega*!",
}

# Prompts para a IA
AI_PROMPTS = {
    "system_instruction": (
        "Você é um especialista em design de interiores focado em substituição de {niche}. "
        "Sua tarefa é pegar a foto de um ambiente e a foto de uma {niche} separada, "
        "e gerar uma imagem realista daquela {niche} instalada no local correto do ambiente."
    )
}

def get_msg(key, **kwargs):
    msg = MESSAGES.get(key, "")
    return msg.format(niche=NICHE.lower(), niche_label=NICHE_LABEL, **kwargs)
