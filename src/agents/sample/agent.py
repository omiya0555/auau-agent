import asyncio
import logging
import os
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Strands Agent Streaming API", version="0.1.0")

class PromptRequest(BaseModel):
    prompt: str

agent_instance = Agent(tools=[], callback_handler=None)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/stream")
async def stream_response(request: PromptRequest):
    """Plain text streaming endpoint (newline delimited)."""

    async def generate() -> AsyncGenerator[bytes, None]:
        try:
            async for event in agent_instance.stream_async(request.prompt):
                # Strands event objects typically contain 'data' for incremental text
                chunk = event.get("data") if isinstance(event, dict) else None
                if chunk:
                    yield (chunk + "\n").encode("utf-8")
        except Exception as e:  # Broad catch to ensure stream closes cleanly
            logger.exception("stream error")
            yield f"Error: {type(e).__name__}: {e}\n".encode("utf-8")

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")

@app.post("/stream_sse")
async def stream_sse(request: PromptRequest):
    """Server-Sent Events (SSE) style streaming endpoint."""

    async def event_source() -> AsyncGenerator[bytes, None]:
        try:
            async for event in agent_instance.stream_async(request.prompt):
                chunk = event.get("data") if isinstance(event, dict) else None
                if chunk:
                    # SSE format: data: <payload> \n\n
                    yield f"data: {chunk}\n\n".encode("utf-8")
            # Signal end of stream
            yield b"event: end\ndata: done\n\n"
        except Exception as e:
            logger.exception("sse stream error")
            yield f"event: error\ndata: {type(e).__name__}: {e}\n\n".encode("utf-8")

    return StreamingResponse(event_source(), media_type="text/event-stream")

@app.get("/")
async def root():
    return {"message": "Use POST /stream or /stream_sse with {'prompt':'...'}"}

# Optional: graceful shutdown hook (if future cleanup needed)
@app.on_event("shutdown")
async def shutdown_event():
    # Placeholder for any async cleanup if required later
    await asyncio.sleep(0)
