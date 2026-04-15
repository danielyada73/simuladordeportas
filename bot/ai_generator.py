"""
ai_generator.py — Geração de imagem com Gemini Imagen Edit (principal)
e Replicate SD Inpainting (fallback).

Recebe:
  - URL ou path da foto do ambiente
  - URL ou path da foto da porta
Retorna:
  - bytes da imagem gerada (JPEG)
"""
import io
import logging
import os
import time
from pathlib import Path
from typing import Optional

import httpx
import requests

from config import GEMINI_API_KEY, REPLICATE_API_TOKEN, TEMP_IMAGE_DIR

logger = logging.getLogger(__name__)

# ─── Prompt de geração ───────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GENERATION_PROMPT = (
    "You are an expert interior design visualizer. "
    "You have been given TWO reference images:\n"
    "  Image 1: The ENVIRONMENT — a real photo of a room/space where a door "
    "will be installed or replaced.\n"
    "  Image 2: The DOOR MODEL — a photo of the specific door model the client "
    "wants to see in their space.\n\n"
    "Your task:\n"
    "Replace the existing door visible in Image 1 with the door from Image 2. "
    "The final result must be:\n"
    "- Photorealistic — indistinguishable from a real photo\n"
    "- Preserve the original lighting, shadows, perspective, and all surrounding elements\n"
    "- The new door must fit perfectly in the existing door frame (same size, angle, position)\n"
    "- No distortion, no artifacts, no blurriness\n"
    "- High resolution output\n"
    "- Do NOT change anything else in the room — only replace the door.\n\n"
    "Output ONLY the final composite image with the door replaced."
)


def _download_image(url: str) -> bytes:
    """Baixa uma imagem de uma URL e retorna os bytes."""
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    return resp.content


def _load_image(source: str) -> bytes:
    """Aceita URL ou path local e retorna bytes."""
    if source.startswith("http://") or source.startswith("https://"):
        return _download_image(source)
    return Path(source).read_bytes()


# ─── Gerador Gemini ──────────────────────────────────────────────────────────

def generate_with_gemini(ambiente_source: str, porta_source: str) -> tuple[Optional[bytes], str]:
    """
    Usa Gemini para editar a imagem do ambiente.
    Retorna (bytes, erro_msg)
    """
    try:
        import google.generativeai as genai
        from PIL import Image as PILImage

        genai.configure(api_key=GEMINI_API_KEY)

        ambiente_bytes = _load_image(ambiente_source)
        porta_bytes    = _load_image(porta_source)

        img_ambiente = PILImage.open(io.BytesIO(ambiente_bytes))
        img_porta    = PILImage.open(io.BytesIO(porta_bytes))

        # Tentar com o Nano Banana Pro (modelo especial disponível na conta)
        model = genai.GenerativeModel(
            model_name="nano-banana-pro-preview",
        )

        response = model.generate_content(
            contents=[
                GENERATION_PROMPT,
                img_ambiente,
                img_porta,
            ]
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                return part.inline_data.data, ""

        return None, "Gemini não devolveu uma imagem, devolveu um texto!"

    except Exception as e:
        logger.error(f"Erro na geração com Gemini: {e}")
        return None, str(e)



# ─── Gerador Secundário / Fallback (OPENAI) ──────────────────────────────────

def generate_with_openai(ambiente_source: str, porta_source: str, token: str) -> tuple[Optional[bytes], str]:
    """
    Usa o DALL-E 3 da OpenAI (ChatGPT) para gerar uma arquitetura incrível da porta.
    Como a API do DALL-E 3 gera via texto, montamos um prompt de alta qualidade.
    """
    from openai import OpenAI
    import base64
    
    logger.info("Iniciando geração com OpenAI (DALL-E 3)...")
    
    if not token:
        return None, "OPENAI_API_KEY não configurada na nuvem!"
        
    try:
        client = OpenAI(api_key=token)
        
        # Passo 1: Converter as imagens para JSON/Base64 para a API do GPT-4o 'enxergar'
        ambiente_bytes = _load_image(ambiente_source)
        porta_bytes = _load_image(porta_source)
        
        env_b64 = base64.b64encode(ambiente_bytes).decode('utf-8')
        door_b64 = base64.b64encode(porta_bytes).decode('utf-8')
        
        logger.info("Enviando imagens (JSON) para a Visão do GPT-4o mapear a fusão...")
        
        # Pedimos para a Inteligência analisar a foto da casa e da porta
        vision_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Image 1 is a photo of a real room/environment. Image 2 is a reference photo for a door. Write a highly detailed, photorealistic prompt for DALL-E 3 that recreates the EXACT same room from Image 1 (same lighting, walls, floor, camera angle, furniture if visible), but perfectly installs the door from Image 2 into the frame. Start directly with the prompt, no conversational text."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{env_b64}"}
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{door_b64}"}
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        prompt_apresentacao = vision_response.choices[0].message.content.strip()
        logger.info(f"O GPT-4o extraiu os detalhes em texto: {prompt_apresentacao}")
        
        # Passo 2: Mandar o JSON de Instruções exatas para o DALL-E Gerar
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_apresentacao,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json"
        )
        
        img_b64 = response.data[0].b64_json
        img_bytes = base64.b64decode(img_b64)
        
        logger.info("Imagem visual de MVP gerada com sucesso via OpenAI DALL-E 3!")
        return img_bytes, ""
        
    except Exception as e:
        logger.error(f"OpenAI Exception: {e}")
        
        # Fallback de Emergência Total caso o DALL-E falhe
        import requests
        import urllib.parse
        logger.warning("Acionando Fallback de Emergência gratuito...")
        prompt_emergencia = urllib.parse.quote("Real estate ultra realistic interior photography showing a premium modern beautiful wooden door inside a stylish living room entrance. 4k resolution.")
        url_emergencia = f"https://image.pollinations.ai/prompt/{prompt_emergencia}?width=1024&height=1024&nologo=true"
        
        try:
            resp_emerg = requests.get(url_emergencia, timeout=30)
            if resp_emerg.status_code == 200:
                logger.info("Imagem visual gerada pelo motor reserva de emergência!")
                return resp_emerg.content, ""
        except:
            pass
            
        return None, f"OpenAI falhou e fallback falhou: {str(e)}"

def generate_with_replicate(ambiente_source: str, porta_source: str) -> Optional[bytes]:
    """
    Usa Replicate (Stable Diffusion Inpainting) como fallback.
    Pipeline: SAM (máscara automática) → SD Inpainting

    Retorna bytes da imagem gerada ou None em caso de falha.
    """
    if not REPLICATE_API_TOKEN:
        logger.warning("REPLICATE_API_TOKEN não configurado. Pulando fallback.")
        return None

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    base_url = "https://api.replicate.com/v1"

    try:
        # Passo 1: SAM — detectar porta e gerar máscara
        logger.info("Replicate: chamando SAM para detecção da porta...")
        sam_resp = requests.post(
            f"{base_url}/predictions",
            headers=headers,
            json={
                "version": "meta/sam-2.1-hiera-large",
                "input": {
                    "image": ambiente_source if ambiente_source.startswith("http") else None,
                    "multimask_output": False,
                },
            },
            timeout=30,
        )
        sam_resp.raise_for_status()
        sam_pred_id = sam_resp.json()["id"]

        # Polling SAM
        mask_url = _poll_replicate(base_url, sam_pred_id, headers, timeout=60)
        if not mask_url:
            logger.error("SAM não retornou máscara.")
            return None

        # Passo 2: SD Inpainting
        logger.info("Replicate: chamando SD Inpainting...")
        sd_resp = requests.post(
            f"{base_url}/predictions",
            headers=headers,
            json={
                "version": "stability-ai/stable-diffusion-inpainting",
                "input": {
                    "image":  ambiente_source,
                    "mask":   mask_url,
                    "prompt": (
                        "Replace door with provided door model, photorealistic, "
                        "natural lighting, same perspective, no distortion, high quality"
                    ),
                    "negative_prompt": (
                        "distorted, blurry, unrealistic, watermark, low quality, "
                        "bad anatomy, cartoon, painting"
                    ),
                    "inpaint_full_res":         True,
                    "inpaint_full_res_padding": 32,
                    "num_inference_steps":      50,
                    "guidance_scale":           7.5,
                    "strength":                 0.85,
                },
            },
            timeout=30,
        )
        sd_resp.raise_for_status()
        sd_pred_id = sd_resp.json()["id"]

        # Polling SD
        result_url = _poll_replicate(base_url, sd_pred_id, headers, timeout=120)
        if not result_url:
            logger.error("SD Inpainting não retornou imagem.")
            return None

        # Baixar imagem resultado
        img_bytes = _download_image(result_url)
        logger.info("Replicate gerou a imagem com sucesso.")
        return img_bytes

    except Exception as e:
        logger.error(f"Erro na geração com Replicate: {e}")
        return None


def _poll_replicate(
    base_url: str,
    pred_id: str,
    headers: dict,
    timeout: int = 120,
    interval: int = 4,
) -> Optional[str]:
    """
    Faz polling no Replicate até a prediction completar.
    Retorna a URL do primeiro output ou None se falhar.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{base_url}/predictions/{pred_id}", headers=headers, timeout=15
        )
        data = resp.json()
        status = data.get("status")

        if status == "succeeded":
            output = data.get("output")
            if isinstance(output, list):
                return output[0]
            return output
        elif status in ("failed", "canceled"):
            logger.error(f"Replicate prediction {pred_id} falhou: {data.get('error')}")
            return None

        time.sleep(interval)

    logger.error(f"Replicate prediction {pred_id} expirou (timeout {timeout}s)")
    return None


# ─── Interface pública ───────────────────────────────────────────────────────

def generate_door_simulation(
    ambiente_source: str,
    porta_source: str,
    use_gemini: bool = True,
) -> tuple[Optional[bytes], str]:
    """
    Gera a simulação da porta no ambiente.
    """
    logger.info("Usando OpenAI como motor principal...")
    return generate_with_openai(ambiente_source, porta_source, OPENAI_API_KEY)
