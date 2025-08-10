import asyncio
import json
import logging
import os
from typing import AsyncGenerator

import boto3
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent, tool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Strands Agent Streaming API", version="0.1.0")

REGION = os.getenv("AWS_REGION", "us-west-2")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
VECTOR_BUCKET = os.getenv("VECTOR_BUCKET_NAME", "tollder-vector-bucket")
VECTOR_INDEX = os.getenv("VECTOR_INDEX_NAME", "tollder-index")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3vectors = boto3.client("s3vectors", region_name=REGION)


class PromptRequest(BaseModel):
    prompt: str


@tool
def search_toddler_index(prompt: str, top_k: int = 3) -> str:
    """
    Convert natural language prompt to an embedding (Titan) and query S3 Vector index
    for similar content. Returns a newline-delimited summary of results.
    """
    try:
        embed_resp = bedrock.invoke_model(
            modelId=EMBED_MODEL_ID,
            body=json.dumps({"inputText": prompt}),
        )
        model_payload = json.loads(embed_resp["body"].read())
        embedding = model_payload["embedding"]

        query_resp = s3vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=VECTOR_INDEX,
            queryVector={"float32": embedding},
            topK=top_k,
            returnDistance=True,
            returnMetadata=True,
        )
        vectors = query_resp.get("vectors", [])
        if not vectors:
            return "No similar content found."

        lines = []
        for v in vectors:
            vid = v.get("id")
            dist = v.get("distance")
            meta = v.get("metadata", {})
            try:
                dist_fmt = f"{dist:.4f}"
            except Exception:
                dist_fmt = str(dist)
            lines.append(f"id={vid} distance={dist_fmt} metadata={meta}")
        return "\n".join(lines)

    except Exception as e:
        logger.exception("Vector search failed")
        return f"Vector search error: {type(e).__name__}: {e}"


agent_instance = Agent(
                    tools=[search_toddler_index],
                    callback_handler=None,
                    system_prompt="あなたは入力された幼児言葉を理解し、<入力された幼児言葉：推測される言葉>だけを出力するエージェントです。search_toddler_indexツールを使用して幼児言葉に関する情報を検索して結果を出力してください。",
                    )

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/stream")
async def stream_response(request: PromptRequest):
    """Plain text streaming endpoint (newline delimited)."""

    async def generate() -> AsyncGenerator[bytes, None]:
        try:
            async for event in agent_instance.stream_async(request.prompt):
                chunk = event.get("data") if isinstance(event, dict) else None
                if chunk:
                    yield (chunk + "\n").encode("utf-8")
        except Exception as e:
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
                    yield f"data: {chunk}\n\n".encode("utf-8")
            yield b"event: end\ndata: done\n\n"
        except Exception as e:
            logger.exception("sse stream error")
            yield f"event: error\ndata: {type(e).__name__}: {e}\n\n".encode("utf-8")

    return StreamingResponse(event_source(), media_type="text/event-stream")


@app.get("/")
async def root():
    return {"message": "Use POST /stream or /stream_sse with {'prompt':'...'}"}
