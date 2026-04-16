"""
core/payments.py — Handler genérico para Webhooks de Pagamento.
"""
import logging
from .sheets import SheetsManager
from .config_base import PLANS

logger = logging.getLogger(__name__)

def process_payment_webhook(data: dict):
    """
    Processa um webhook de pagamento bem-sucedido.
    Assume que o payload contém o telefone do comprador e o código do produto/plano.
    """
    sheets = SheetsManager()
    
    # Exemplo de extração (Adaptar conforme a plataforma: Kiwify, Stripe, etc.)
    # Kiwify usa: data['customer']['mobile'] e data['product_id']
    phone = data.get("customer", {}).get("mobile") or data.get("phone")
    plan_type = "omega" # Simplificado: assumindo que o webhook é para o Omega
    
    if not phone:
        logger.error("Webhook recebido sem número de telefone.")
        return False

    user = sheets.get_user_by_phone(phone)
    
    if user:
        # Se o usuário já existe, adiciona 200 créditos ao saldo atual (10/210 logic)
        current_credits = int(user.get("creditos_restantes", 0))
        new_credits = current_credits + PLANS["omega"]["credits"]
        
        sheets.update_user(phone, "telefone", "plano", "omega")
        sheets.update_user(phone, "telefone", "creditos_restantes", new_credits)
        logger.info(f"Upgrade realizado para {phone}: {current_credits} -> {new_credits}")
    else:
        # Se não existe, cria um novo usuário Omega já com 200 créditos
        sheets.create_user(phone=phone, plano="omega")
        logger.info(f"Novo usuário Omega criado via pagamento: {phone}")
        
    return True
