"""Privacy-preserving Langfuse observations for project AI operations."""

from contextlib import contextmanager, nullcontext
from functools import lru_cache
from typing import Iterator, Any

from app.config import settings


@lru_cache(maxsize=1)
def _client():
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    # Import after Settings loaded backend/.env so SDK initializes with credentials.
    from langfuse import Langfuse

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url,
        environment=settings.langfuse_environment,
    )


@contextmanager
def observation(name: str, *, as_type: str = "span", input: Any = None,
                metadata: dict | None = None, model: str | None = None) -> Iterator[Any]:
    """Create an observation; only caller-provided, non-content summaries are exported."""
    client = _client()
    if client is None:
        yield None
        return
    with client.start_as_current_observation(
        name=name, as_type=as_type, input=input, metadata=metadata, model=model,
    ) as current:
        yield current


def attributes(*, user_id: int | None = None, session_id: str | None = None,
               tags: list[str] | None = None):
    if _client() is None:
        return nullcontext()
    from langfuse import propagate_attributes

    return propagate_attributes(
        user_id=str(user_id) if user_id is not None else None,
        session_id=session_id,
        tags=tags,
    )


def flush() -> None:
    client = _client()
    if client is not None:
        client.flush()
