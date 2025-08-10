import os
import boto3

REGION = os.getenv("AWS_REGION", "us-west-2")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
VECTOR_BUCKET = os.getenv("VECTOR_BUCKET_NAME", "tollder-vector-bucket")
VECTOR_INDEX = os.getenv("VECTOR_INDEX_NAME", "tollder-index")

s3vectors = boto3.client("s3vectors", region_name=REGION)

bucket_name = VECTOR_BUCKET
index_name = VECTOR_INDEX

paginator = s3vectors.get_paginator("list_vectors")
pages = paginator.paginate(vectorBucketName=bucket_name, indexName=index_name)

all_keys = []
for page in pages:
    for vector in page.get("vectors", []):
        all_keys.append(vector["key"])

for key in all_keys:
    print(f"Deleting vector: {key}")
    s3vectors.delete_vectors(
        vectorBucketName=bucket_name,
        indexName=index_name,
        keys=[key]  
    )
