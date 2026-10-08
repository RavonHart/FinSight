import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.core.logging import logger


async def generate_llm_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2500,
) -> Optional[str]:
    """
    Direct asynchronous LLM completion supporting OpenAI and Gemini.
    Uses httpx so zero additional C/binary dependencies are required.
    Falls back gracefully to None if credentials are mock or if an error occurs.
    """
    api_key = settings.effective_llm_api_key
    if not api_key or api_key.startswith("mock"):
        return None

    provider = (settings.LLM_PROVIDER or "openai").lower()
    model = settings.LLM_MODEL or "gpt-4o"

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        if provider == "openai" or api_key.startswith("sk-"):
            url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content")
                        if content:
                            logger.info(f"OpenAI live completion succeeded (model={model}, length={len(content)})")
                            return content.strip()
                else:
                    logger.warning(
                        f"OpenAI API returned HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                    return None

        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            full_prompt = (system_prompt + "\n\n" if system_prompt else "") + prompt
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text")
                            if text:
                                logger.info(f"Gemini live completion succeeded (model={model}, length={len(text)})")
                                return text.strip()
                else:
                    logger.warning(
                        f"Gemini API returned HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                    return None

    except Exception as e:
        logger.error(f"Live LLM completion exception: {e}")
        return None

    return None
