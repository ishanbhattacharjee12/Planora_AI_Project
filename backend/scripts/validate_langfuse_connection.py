"""Send a safe gateway embedding probe and print its Langfuse trace ID."""

import asyncio

from app.ai.gateway import ai_gateway
from app.services.tracing import _client, attributes, observation, flush


async def main() -> None:
    client = _client()
    if client is None:
        raise SystemExit("Langfuse credentials are not configured")
    if not client.auth_check():
        raise SystemExit("Langfuse rejected the configured credentials")

    with observation(
        "validate-tracing-connection",
        input={"probe": "connection-check"},
    ) as root:
        with attributes(tags=["connection-check"]):
            trace_id = client.get_current_trace_id()
            vectors = await ai_gateway.embed(["Langfuse connection check"])
            root.update(output={"connected": True, "vector_count": len(vectors)})

    flush()
    print(f"authenticated=True trace_id={trace_id}")


if __name__ == "__main__":
    asyncio.run(main())
