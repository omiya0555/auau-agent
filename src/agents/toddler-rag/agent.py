import json
import logging
import os

import boto3
from pydantic import BaseModel
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


REGION = os.getenv("AWS_REGION", "us-west-2")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
VECTOR_BUCKET = os.getenv("VECTOR_BUCKET_NAME", "tollder-vector-bucket")
VECTOR_INDEX = os.getenv("VECTOR_INDEX_NAME", "tollder-index")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3vectors = boto3.client("s3vectors", region_name=REGION)


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
                    description="幼児言葉を理解し推測する言葉を出力するエージェント",
                    tools=[search_toddler_index],
                    callback_handler=None,
                    system_prompt=load_system_prompt(),
                    )

server = A2AServer(
    agent=agent_instance, 
    port=9001,
)

server.serve()
