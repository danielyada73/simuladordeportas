import json
import os
from typing import Any, Dict


def _gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _extract_text_from_gemini(response: Any) -> str:
    text = getattr(response, "text", "") or ""
    if text:
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    parts = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", "")
            if part_text:
                parts.append(part_text)
    return "\n".join(parts).strip()


def complete_json(prompt: str) -> Dict[str, Any]:
    prompt = str(prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt vazio.")

    gemini_key = _gemini_key()
    if gemini_key:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content(prompt)
        text = _extract_text_from_gemini(response)
        if not text:
            raise RuntimeError("Gemini nao retornou texto.")
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)

    openai_key = _openai_key()
    if openai_key:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        text = getattr(response, "output_text", "").strip()
        if not text:
            raise RuntimeError("OpenAI nao retornou texto.")
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)

    raise RuntimeError("Missing GEMINI_API_KEY or OPENAI_API_KEY.")


def complete_text(prompt: str) -> str:
    prompt = str(prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt vazio.")

    gemini_key = _gemini_key()
    if gemini_key:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content(prompt)
        text = _extract_text_from_gemini(response)
        if text:
            return text.strip()
        raise RuntimeError("Gemini nao retornou texto.")

    openai_key = _openai_key()
    if openai_key:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        text = getattr(response, "output_text", "").strip()
        if text:
            return text
        raise RuntimeError("OpenAI nao retornou texto.")

    raise RuntimeError("Missing GEMINI_API_KEY or OPENAI_API_KEY.")
