from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ot_agent.config import load_app_settings

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

PLACEHOLDER_MODEL = "REPLACE_AFTER_OLLAMA_LIST"


class LLMError(RuntimeError):
    pass


def _llm_settings() -> dict[str, Any]:
    cfg = load_app_settings()
    llm = cfg.get("llm") if isinstance(cfg, dict) else None

    if not isinstance(llm, dict):
        raise LLMError("В конфигурации отсутствует раздел llm.")

    return llm


def _normalize_base_url(base_url: Any) -> str:
    url = str(base_url or "").strip().rstrip("/")

    if not url:
        raise LLMError("Не задан llm.base_url.")

    return url


def _assert_local_endpoint(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise LLMError(
            f"Недопустимая схема URL: {parsed.scheme}. Ожидается http или https."
        )

    host = parsed.hostname

    if host not in ALLOWED_HOSTS:
        raise LLMError(
            "Разрешены только локальные адреса: 127.0.0.1, localhost или ::1."
        )


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    _assert_local_endpoint(url)

    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}

    except HTTPError as exc:
        detail = ""

        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(exc.reason)

        raise LLMError(
            f"HTTP {exc.code} от {url}: {detail}"
        ) from exc

    except URLError as exc:
        raise LLMError(
            f"Не удалось подключиться к {url}: {exc.reason}. "
            "Проверьте, запущен ли Ollama и доступен ли порт 11434."
        ) from exc

    except TimeoutError as exc:
        raise LLMError(
            f"Таймаут запроса к {url}. "
            "Модель может долго загружаться в память. Попробуйте повторить тест."
        ) from exc

    except json.JSONDecodeError as exc:
        raise LLMError(f"Сервер вернул некорректный JSON: {exc}") from exc


def _validate_model_name(model: Any) -> str:
    name = str(model or "").strip()

    if not name:
        raise LLMError("Не задано имя модели.")

    if name == PLACEHOLDER_MODEL:
        raise LLMError(
            "В конфигурации осталось placeholder-значение модели. "
            "Замените его на точное имя из вывода ollama list."
        )

    return name


def get_primary_model() -> str:
    llm = _llm_settings()
    return _validate_model_name(llm.get("primary_model"))


def get_secondary_model() -> str | None:
    llm = _llm_settings()
    raw = llm.get("secondary_model")

    if not raw or str(raw).strip() == PLACEHOLDER_MODEL:
        return None

    return str(raw).strip()


def list_models() -> list[dict[str, Any]]:
    llm = _llm_settings()
    base_url = _normalize_base_url(llm.get("base_url"))
    url = base_url + "/api/tags"

    data = _request_json(url, method="GET", timeout=15)
    models = data.get("models") or []

    return [model for model in models if isinstance(model, dict)]


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if parsed < minimum:
        return default

    return parsed


def build_options() -> dict[str, Any]:
    llm = _llm_settings()

    return {
        "temperature": _as_float(llm.get("temperature"), 0.1),
        "top_p": _as_float(llm.get("top_p"), 0.9),
        "num_ctx": _as_int(llm.get("context_length"), 4096, minimum=256),
        "num_predict": _as_int(llm.get("max_new_tokens"), 1500, minimum=1),
    }


def generate_test_response(model: str | None = None) -> tuple[str, float]:
    llm = _llm_settings()
    base_url = _normalize_base_url(llm.get("base_url"))
    url = base_url + "/api/generate"

    selected_model = _validate_model_name(model or get_primary_model())

    prompt = (
        "Технический тест локального подключения. "
        "Ответь ровно одним словом: ОК. "
        "Не добавляй пояснений, пунктов, ссылок или юридического текста."
    )

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": build_options(),
    }

    started_at = time.perf_counter()

    data = _request_json(
        url,
        method="POST",
        payload=payload,
        timeout=300,
    )

    elapsed = time.perf_counter() - started_at
    response = str(data.get("response") or "").strip()

    if not response:
        raise LLMError("Модель вернула пустой ответ.")

    return response, elapsed