import os
import boto3
import json
from PyPDF2 import PdfReader

REGION = os.getenv("AWS_REGION", "us-west-2")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
VECTOR_BUCKET = os.getenv("VECTOR_BUCKET_NAME", "tollder-vector-bucket")
VECTOR_INDEX = os.getenv("VECTOR_INDEX_NAME", "tollder-index")
CHUNK_SIZE = os.getenv("CHUNK_SIZE", 500)
MAX_METADATA_BYTES = os.getenv("MAX_METADATA_BYTES", 1800)
MAX_CHARS_PER_SPLIT = os.getenv("MAX_CHARS_PER_SPLIT", 2000)

region = REGION
pdf_path = "./src/agents/toddler-rag/pdf/sample.pdf"
vector_bucket_name = VECTOR_BUCKET
vector_index_name = VECTOR_INDEX
chunk_size = CHUNK_SIZE
max_metadata_bytes = MAX_METADATA_BYTES

def split_text_by_length(text, max_chars=MAX_CHARS_PER_SPLIT):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def trim_to_max_bytes(s, max_bytes):
    """指定されたUTF-8バイト数以内に文字列を収める"""
    encoded = s.encode("utf-8")
    if len(encoded) <= max_bytes:
        return s

    trimmed = encoded[:max_bytes]

    while True:
        try:
            return trimmed.decode("utf-8")
        except UnicodeDecodeError:
            trimmed = trimmed[:-1]

def extract_chunks_from_pdf(pdf_path, chunk_size=chunk_size):
    reader = PdfReader(pdf_path)
    chunks = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            split_chunks = split_text_by_length(text.strip(), chunk_size)
            for chunk_index, chunk in enumerate(split_chunks):
                chunks.append({
                    "text": chunk,
                    "page": page_number,
                    "chunk": chunk_index + 1
                })
    return chunks

bedrock = boto3.client("bedrock-runtime", region_name=region)
s3vectors = boto3.client("s3vectors", region_name=region)

chunks = extract_chunks_from_pdf(pdf_path, chunk_size)

vectors = []
for i, chunk in enumerate(chunks):
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=json.dumps({"inputText": chunk["text"]})
    )

    response_body = json.loads(response["body"].read())
    embedding = response_body["embedding"]

    source_text_trimmed = trim_to_max_bytes(chunk["text"], max_metadata_bytes)

    vector = {
        "key": f"page-{chunk['page']}-chunk-{chunk['chunk']}",
        "data": {"float32": embedding},
        "metadata": {
            "source_text": source_text_trimmed,
            "page_number": chunk["page"],
            "chunk_number": chunk["chunk"]
        }
    }
    vectors.append(vector)

s3vectors.put_vectors(
    vectorBucketName=vector_bucket_name,
    indexName=vector_index_name,
    vectors=vectors
)

print(f"{len(vectors)} 個のベクトルを S3 Vectors に登録しました。")