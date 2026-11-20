from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODEL = "inclusionai/ling-3.2-flash:free"
FALLBACK_MODELS = (
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
)
MODELS = (MODEL, *FALLBACK_MODELS)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 30


class OpenRouterError(Exception):
    pass


def request_completion(
    api_key: str, messages: list[dict[str, str]]
) -> str:
    request = Request(
        OPENROUTER_URL,
        data=json.dumps(
            {
                "model": MODEL,
                "models": list(MODELS),
                "route": "fallback",
                "messages": messages,
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read())
    except HTTPError as error:
        if error.code == 429:
            raise OpenRouterError(
                "El asistente está saturado en este momento. "
                "Inténtalo de nuevo en unos minutos."
            ) from error
        raise OpenRouterError(
            f"OpenRouter devolvió HTTP {error.code}"
        ) from error
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise OpenRouterError(
                "El asistente agotó el tiempo de espera."
            ) from error
        raise OpenRouterError(
            "No se pudo conectar con el asistente."
        ) from error
    except TimeoutError as error:
        raise OpenRouterError(
            "El asistente agotó el tiempo de espera."
        ) from error
    except json.JSONDecodeError as error:
        raise OpenRouterError(
            "El asistente devolvió una respuesta no válida."
        ) from error

    choices = data.get("choices") if isinstance(data, dict) else None
    first_choice = choices[0] if isinstance(choices, list) and choices else None
    message = first_choice.get("message") if isinstance(first_choice, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("El asistente devolvió una respuesta vacía.")
    return content.strip()
