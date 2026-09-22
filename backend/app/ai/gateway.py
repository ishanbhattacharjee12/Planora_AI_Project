import asyncio
import hashlib
import json
import logging
import math
import re
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.validators.sensitive_data import scan_sensitive_data
from app.config import settings
from app.models import AIRequest, AIResponse, ClassificationLevel
from app.services.tracing import attributes, observation

logger = logging.getLogger("app.ai.gateway")


class AIGatewayError(Exception):
    pass


class SensitiveDataError(AIGatewayError):
    pass


GEMINI_MODEL_CANDIDATES = [
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.6-flash",
]


def select_model_candidates(classification: ClassificationLevel = ClassificationLevel.INTERNAL) -> list[str]:
    candidates: list[str] = []
    if settings.gemini_model:
        candidates.append(settings.gemini_model)
    for m in GEMINI_MODEL_CANDIDATES:
        if m not in candidates:
            candidates.append(m)
    return candidates


def select_model(classification: ClassificationLevel = ClassificationLevel.INTERNAL) -> str:
    candidates = select_model_candidates(classification)
    return candidates[0] if candidates else "gemini-flash-latest"


def _rate_limit_retry_delay(exc: Exception) -> float | None:
    message = str(exc).lower()
    if "429" not in message and "rate_limit" not in message and "resource_exhausted" not in message:
        return None
    match = re.search(r"(?:try again in|retry in|retrydelay':\s*')([\d.]+)", str(exc), re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.0
    return 5.0


def _json_retry_delay(exc: Exception) -> float | None:
    message = str(exc).lower()
    if "json_validate_failed" not in message and "failed to validate json" not in message:
        return None
    return 2.0


def _connection_retry_delay(exc: Exception, attempt: int) -> float | None:
    """Retry transient transport/provider failures with a short backoff."""
    if isinstance(exc, (APIConnectionError, APITimeoutError, InternalServerError)):
        return min(2.0 * (attempt + 1), 8.0)
    message = str(exc).lower()
    if any(marker in message for marker in ("connection error", "connection reset", "timed out", "temporarily unavailable")):
        return min(2.0 * (attempt + 1), 8.0)
    return None


def _build_json_response_format(
    schema_name: str | None,
    json_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    if json_schema:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name or "response",
                "strict": False,
                "schema": json_schema,
            },
        }
    return {"type": "json_object"}


class AIGateway:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.gemini_api_key or "not-set",
            base_url=settings.gemini_base_url,
            timeout=90.0,
            max_retries=0,
        )

    async def complete(
        self,
        db: AsyncSession,
        *,
        messages: list[dict[str, str]],
        request_type: str,
        user_id: int | None = None,
        project_id: int | None = None,
        classification: ClassificationLevel = ClassificationLevel.INTERNAL,
        response_format: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if not settings.gemini_api_key:
            raise AIGatewayError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in environment or .env."
            )

        combined = "\n".join(m.get("content", "") for m in messages)
        scan = scan_sensitive_data(combined)
        if scan.has_sensitive:
            if settings.sensitive_data_action == "block":
                raise SensitiveDataError(f"Sensitive data detected: {', '.join(scan.findings)}")
            messages = [{"role": m["role"], "content": scan.redacted_text} for m in messages]

        model_candidates = select_model_candidates(classification)
        last_exc: Exception | None = None

        for model in model_candidates:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens or settings.max_ai_tokens_per_request,
            }
            if response_format:
                kwargs["response_format"] = response_format

            ai_request = AIRequest(
                user_id=user_id,
                project_id=project_id,
                request_type=request_type,
                model=model,
                status="pending",
            )
            db.add(ai_request)
            await db.flush()

            model_succeeded = False
            for attempt in range(3):
                try:
                    logger.info(
                        "Calling Gemini API: type=%s, model=%s, attempt=%d",
                        request_type,
                        model,
                        attempt + 1,
                    )
                    with attributes(user_id=user_id, tags=[request_type.split("_")[0]]):
                        with observation(
                            "generate-response", as_type="generation", model=model,
                            input={"request_type": request_type, "message_count": len(messages)},
                            metadata={"project_id": project_id, "classification": classification.value,
                                      "attempt": attempt + 1, "schema": bool(response_format)},
                        ) as generation:
                            try:
                                response = await self.client.chat.completions.create(**kwargs)
                                if generation is not None:
                                    usage = response.usage
                                    generation.update(
                                        output={"completed": True, "response_chars": len(response.choices[0].message.content or "")},
                                        usage_details={
                                            "input_tokens": usage.prompt_tokens,
                                            "output_tokens": usage.completion_tokens,
                                        } if usage else None,
                                    )
                            except Exception as exc:
                                if generation is not None:
                                    generation.update(level="ERROR", status_message=type(exc).__name__)
                                raise
                    content = response.choices[0].message.content or ""
                    ai_request.status = "success"
                    ai_request.prompt_tokens = response.usage.prompt_tokens if response.usage else None
                    ai_request.completion_tokens = response.usage.completion_tokens if response.usage else None
                    db.add(AIResponse(request_id=ai_request.id, content=content))
                    await db.flush()
                    logger.info(
                        "Gemini response success: type=%s, model=%s, prompt_tokens=%s, completion_tokens=%s",
                        request_type,
                        model,
                        ai_request.prompt_tokens,
                        ai_request.completion_tokens,
                    )
                    return content
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "Gemini request attempt %d failed for %s (model=%s): %s: %s",
                        attempt + 1,
                        request_type,
                        model,
                        type(exc).__name__,
                        str(exc),
                    )
                    delay = (
                        _rate_limit_retry_delay(exc)
                        or _json_retry_delay(exc)
                        or _connection_retry_delay(exc, attempt)
                    )
                    if delay is None or attempt == 2:
                        break
                    logger.info("Retrying Gemini request after %.1fs delay...", delay)
                    await asyncio.sleep(delay)

            ai_request.status = "error"
            db.add(AIResponse(request_id=ai_request.id, content=str(last_exc)))
            await db.flush()

            # If the failure is specific to this model (e.g. 404, unavailable, not found, 503), try next candidate
            err_str = str(last_exc).lower()
            if "404" in err_str or "not found" in err_str or "unavailable" in err_str or "503" in err_str:
                logger.info("Model %s unavailable; trying next Gemini candidate...", model)
                continue
            else:
                # Other error (e.g. auth failure on key itself, invalid schema)
                break

        raise AIGatewayError(
            f"Gemini API request failed: {last_exc}"
        ) from last_exc

    async def complete_json(
        self,
        db: AsyncSession,
        *,
        messages: list[dict[str, str]],
        request_type: str,
        user_id: int | None = None,
        project_id: int | None = None,
        classification: ClassificationLevel = ClassificationLevel.INTERNAL,
        schema_name: str | None = None,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        content = await self.complete(
            db,
            messages=messages,
            request_type=request_type,
            user_id=user_id,
            project_id=project_id,
            classification=classification,
            response_format=_build_json_response_format(schema_name, json_schema),
            max_tokens=max_tokens,
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL | re.IGNORECASE)
            if fenced:
                return json.loads(fenced.group(1))
            raise

    def _local_embed(self, texts: list[str], dim: int = 384) -> list[list[float]]:
        """Generate deterministic local vectors for embeddings."""
        vectors: list[list[float]] = []
        for text in texts:
            seed = hashlib.sha256(text.encode()).digest()
            vec = [((seed[i % len(seed)] / 127.5) - 1.0) for i in range(dim)]
            magnitude = math.sqrt(sum(x * x for x in vec)) or 1.0
            vectors.append([x / magnitude for x in vec])
        return vectors

    async def embed(self, texts: list[str]) -> list[list[float]]:
        with observation(
            "embed-text", as_type="embedding", model="local-feature-hash-v1",
            input={"text_count": len(texts), "total_chars": sum(len(t) for t in texts)},
        ) as embedding:
            vectors = self._local_embed(texts)
            if embedding is not None:
                embedding.update(output={"vector_count": len(vectors), "provider": "local"})
            return vectors


ai_gateway = AIGateway()
