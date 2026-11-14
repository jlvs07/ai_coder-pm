from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODEL = "inclusionai/ling-3.2-flash:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 30


class OpenRouterError(Exception):
    pass


def request_completion(api_key: str, prompt: str) -> str:
    request = Request(
        OPENROUTER_URL,
        data=json.dumps(
            {
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
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
        raise OpenRouterError(
            f"OpenRouter returned HTTP {error.code}"
        ) from error
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise OpenRouterError("OpenRouter request timed out") from error
        raise OpenRouterError("Could not connect to OpenRouter") from error
    except TimeoutError as error:
        raise OpenRouterError("OpenRouter request timed out") from error
    except json.JSONDecodeError as error:
        raise OpenRouterError("OpenRouter returned invalid JSON") from error

    choices = data.get("choices") if isinstance(data, dict) else None
    first_choice = choices[0] if isinstance(choices, list) and choices else None
    message = first_choice.get("message") if isinstance(first_choice, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("OpenRouter returned an empty response")
    return content.strip()
