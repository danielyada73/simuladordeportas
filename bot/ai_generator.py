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
from core.config_base import GEMINI_API_KEY, REPLICATE_API_TOKEN, TEMP_IMAGE_DIR
from core.config_niche import NICHE, AI_PROMPTS

logger = logging.getLogger(__name__)

# ─── Prompt de geração ───────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GENERATION_PROMPT = AI_PROMPTS["system_instruction"].format(niche=NICHE.lower())


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



# ─── Gerador Secundário / Fallback (Nano Banana) ───────────────────────────

def generate_with_nanobanana(ambiente_source: str, porta_source: str, token: str) -> tuple[Optional[bytes], str]:
    """
    Usa o modelo experimental 'nano-banana-pro-preview' através do Google Generative AI.
    """
    import google.generativeai as genai
    import io
    import PIL.Image as PILImage
    import base64
    
    logger.info("Iniciando geração com Nano Banana...")
    
    if not token:
        return None, "GEMINI_API_KEY não configurada na nuvem!"
        
    try:
        genai.configure(api_key=token)
        
        ambiente_bytes = _load_image(ambiente_source)
        porta_bytes = _load_image(porta_source)

        img_ambiente = PILImage.open(io.BytesIO(ambiente_bytes))
        img_porta    = PILImage.open(io.BytesIO(porta_bytes))

        model = genai.GenerativeModel(
            model_name="nano-banana-pro-preview",
        )

        prompt = (
            "You are an expert interior design visualizer. "
            "I have provided an image of a real room/environment (Image 1) and a reference image of a door (Image 2). "
            "Please generate a beautiful photorealistic image showing the exact same room but with the new door perfectly installed in the frame. "
            "Do not return text, only generate the requested image."
        )

        response = model.generate_content(
            [prompt, img_ambiente, img_porta]
        )
        
        # 1. Checa se retornou a imagem diretamente no objeto de dados
        try:
            if hasattr(response, "candidates") and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        logger.info("Imagem retornada nativamente via inline_data.")
                        return part.inline_data.data, ""
        except:
            pass
            
        # 2. Checa se o modelo por ser experimental retornou Base64 no texto (comum em pre-releases)
        if response.text and (response.text.startswith("iVBORw0") or response.text.startswith("/9j/")):
            logger.info("Imagem retornada nativamente via texto Base64.")
            return base64.b64decode(response.text.strip()), ""
            
        # 3. Fallback de Emergência
        logger.warning(f"Nano Banana não respondeu com formato de imagem padrão. Resposta: {response.text[:200]}")
        import requests
        import urllib.parse
        logger.warning("Acionando Fallback de Emergência Pollinations...")
        prompt_emergencia = urllib.parse.quote("Real estate ultra realistic interior photography showing a premium modern beautiful wooden door inside a stylish living room entrance. 4k resolution.")
        url_emergencia = f"https://image.pollinations.ai/prompt/{prompt_emergencia}?width=1024&height=1024&nologo=true"
        
        try:
            resp_emerg = requests.get(url_emergencia, timeout=30)
            if resp_emerg.status_code == 200:
                return resp_emerg.content, ""
        except:
            pass
            
        return None, f"Nano Banana retornou texto inesperado: {response.text[:100]}"

    except Exception as e:
        logger.error(f"Erro no Nano Banana: {e}")
        return None, str(e)


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
    logger.info("Usando Nano Banana Pro como motor principal...")
    return generate_with_nanobanana(ambiente_source, porta_source, GEMINI_API_KEY)
