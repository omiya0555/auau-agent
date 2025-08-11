import asyncio
import logging
import os
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()
MODEL_ID = os.getenv("BEDROCK_MODEL_ID","")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Strands Agent Streaming API", version="0.1.0")

class PromptRequest(BaseModel):
    prompt: str

    
# Load system prompt from file
def load_system_prompt():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "system_prompt.txt")
    if not os.path.exists(prompt_path):
        logger.warning(f"System prompt file not found: {prompt_path}")
        return "You are a helpful assistant."
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

agent_instance = Agent(tools=[], callback_handler=None, model=MODEL_ID, system_prompt=load_system_prompt())

# 認証設定追加
security = HTTPBearer(auto_error=False)

def require_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    allowed = os.getenv("API_TOKENS")
    if not allowed:
        logging.warning("API_TOKENS not set; denying request.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth not configured",
        )
    if token != allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/stream")
async def stream_response(request: PromptRequest, _: None = Depends(require_bearer_token)):
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
async def stream_sse(request: PromptRequest, _: None = Depends(require_bearer_token)):
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
