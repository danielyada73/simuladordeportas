# Guia de Configuração: Webhook Kiwify

Para que o seu bot receba as vendas automaticamente e libere o Plano Omega, siga estes passos no painel da Kiwify.

## 1. Localizar o Menu de Webhooks
1. Acesse o seu painel da [Kiwify](https://dashboard.kiwify.com.br/).
2. No menu lateral, clique em **Apps** (ícone de grade ou "Integrações").
3. Selecione a opção **Webhooks**.

## 2. Criar Novo Webhook
1. Clique em **Criar Webhook**.
2. Preencha os campos abaixo:
   - **Nome:** Bot Simulador de Portas
   - **URL para receber as notificações:** `https://simuladordeportas.onrender.com/kiwify`
   - **Status do Pedido:** Marque as opções **Pedido Aprovado** e **Pedido Pago**.
   - **Produto:** Selecione o seu produto "Plano Omega".

## 3. Salvar
1. Clique em **Salvar Webhook**.

---

## Como testar?
Você pode usar a ferramenta de teste da própria Kiwify ("Testar envio") ou gerar um **Boleto** ou **PIX** de teste no seu checkout:
1. Acesse o seu link de checkout.
2. Gere um PIX de teste (não precisa pagar, se a Kiwify enviar o evento de "Gerado", o bot pode até avisar, mas a liberação ocorre no "Aprovado").
3. Verifique se o log do seu bot no Render mostra: `💰 Venda confirmada via Kiwify`.

> [!TIP]
> **Dica Extra:** Se o cliente comprar mas ainda não estiver cadastrado no bot, o bot apenas registrará a venda no log. O ideal é que o cliente passe pela Landing Page primeiro para já estar na planilha quando a Kiwify avisar da compra!
