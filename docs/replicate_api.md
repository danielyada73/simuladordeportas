# API de Geração de Imagens — Replicate

Guia de integração do Replicate com Stable Diffusion Inpainting para o Simulador de Ambientes.

---

## Cadastro e Configuração

1. Acesse [replicate.com](https://replicate.com) e crie uma conta
2. Vá em **Settings → API Tokens**
3. Clique em **"Create token"** → copie o token
4. Adicione créditos em **Billing → Add credits** (comece com US$ 10)

**Salve no seu `.env`:**
```
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Modelos Usados

### 1. SAM — Detecção Automática de Porta

**Segment Anything Model** detecta automaticamente onde está a porta na foto do ambiente, gerando a máscara necessária para o Inpainting.

```
Modelo: meta/sam-2.1-hiera-large
Custo: ~US$ 0,003 por chamada
```

### 2. Stable Diffusion Inpainting

Substitui apenas a área da porta (definida pela máscara) pelo novo modelo de porta, preservando todo o resto do ambiente.

```
Modelo: stability-ai/stable-diffusion-inpainting
Custo: ~US$ 0,009 por geração
```

**Custo total por simulação: ~US$ 0,012 (≈ R$ 0,06)**

---

## Fluxo de Geração

```
foto_ambiente + foto_porta
        ↓
1. SAM: detecta porta na foto_ambiente → máscara
        ↓
2. SD Inpainting: substitui área da máscara pela foto_porta
        ↓
imagem_final (ambiente com nova porta, sem distorção)
```

---

## Requisição SAM (Detecção da Porta)

```bash
curl -X POST \
  https://api.replicate.com/v1/predictions \
  -H "Authorization: Token SEU_REPLICATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "meta/sam-2.1-hiera-large:latest",
    "input": {
      "image": "URL_PUBLICA_FOTO_AMBIENTE",
      "multimask_output": false
    }
  }'
```

**Resposta:**
```json
{
  "id": "prediction_id_xxx",
  "status": "starting",
  "urls": {
    "get": "https://api.replicate.com/v1/predictions/prediction_id_xxx"
  }
}
```

---

## Verificar Status (Polling)

```bash
curl -X GET \
  https://api.replicate.com/v1/predictions/prediction_id_xxx \
  -H "Authorization: Token SEU_REPLICATE_TOKEN"
```

**Aguardar até `"status": "succeeded"`**, então usar o `output`.

---

## Requisição SD Inpainting (Fusão das Imagens)

```bash
curl -X POST \
  https://api.replicate.com/v1/predictions \
  -H "Authorization: Token SEU_REPLICATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "stability-ai/stable-diffusion-inpainting:...",
    "input": {
      "image": "URL_FOTO_AMBIENTE",
      "mask": "URL_MASCARA_DO_SAM",
      "prompt": "Replace the door with the provided door model, photorealistic, natural lighting, same perspective, no distortion, high quality",
      "negative_prompt": "distorted, blurry, unrealistic, watermark, low quality, bad anatomy",
      "inpaint_full_res": true,
      "inpaint_full_res_padding": 32,
      "num_inference_steps": 50,
      "guidance_scale": 7.5,
      "strength": 0.85
    }
  }'
```

---

## Parâmetros Importantes

| Parâmetro | Valor Recomendado | Descrição |
|-----------|-------------------|-----------|
| `num_inference_steps` | 50 | Mais passos = melhor qualidade, mais lento |
| `guidance_scale` | 7.5 | Quão fiel ao prompt (7–9 é ideal) |
| `strength` | 0.85 | Intensidade da substituição (0.8–0.9) |
| `inpaint_full_res` | true | Processa a região da máscara em alta resolução |
| `inpaint_full_res_padding` | 32 | Pixels de contexto ao redor da máscara |

---

## Qualidade dos Resultados — Dicas

Para melhores fusões:

1. **Fotos do ambiente:** bem iluminadas, sem filtros, resolução mínima 720p
2. **Fotos da porta:** fundo neutro (preferencialmente branco), porta centralizada
3. **Prompt adicional:** adicione características do ambiente (madeira, concreto, etc.) para manter coerência
4. **Se resultar distorcido:** reduza `strength` para 0.75 ou ajuste o padding

---

## Custos Detalhados

| Ação | Custo (USD) | Custo (BRL ~5.00) |
|------|-------------|-------------------|
| SAM (por detecção) | ~US$ 0.003 | ~R$ 0,015 |
| SD Inpainting (por geração) | ~US$ 0.009 | ~R$ 0,045 |
| **Total por simulação** | **~US$ 0.012** | **~R$ 0,06** |
| US$ 10 de crédito | ~833 simulações | ~833 clientes |

---

## Estratégia de Precificação dos Planos

Com custo de ~R$ 0,06 por geração:

| Plano | Gerações | Custo IA | Preço ao Cliente | Margem |
|-------|----------|----------|-----------------|--------|
| Alpha (free) | 2 | R$ 0,12 | R$ 0 | -R$ 0,12 (aquisição) |
| Beta (free) | 5 | R$ 0,30 | R$ 0 | -R$ 0,30 (aquisição) |
| Omega (pago) | 50/mês | R$ 3,00 | R$ 47–97/mês | R$ 44–94/mês |

---

## Alternativas ao Replicate

Se quiser rodar localmente ou com outros provedores:

| Opção | Vantagem | Custo |
|-------|---------|-------|
| **Replicate** | Sem infra, API simples | Pay-per-use |
| **RunPod** | GPU dedicada, mais barato em volume | ~US$ 0,0002/seg |
| **Stability AI API** | Acesso direto ao SD | Plano mensal |
| **ComfyUI local** | Gratuito, total controle | Hardware próprio |
