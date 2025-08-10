import boto3 
import json 

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
s3vectors = boto3.client("s3vectors", region_name="us-west-2") 

input_text = "adventures in space"

response = bedrock.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({
        "inputText": input_text,
    })
) 

model_response = json.loads(response["body"].read())
embedding = model_response["embedding"]

response = s3vectors.query_vectors(
    vectorBucketName="tollder-vector-bucket",
    indexName="tollder-index",
    queryVector={"float32": embedding}, 
    topK=3, 
    returnDistance=True,
    returnMetadata=True
)
print(json.dumps(response["vectors"], indent=2))

response = s3vectors.query_vectors(
    vectorBucketName="tollder-vector-bucket",
    indexName="tollder-index",
    queryVector={"float32": embedding}, 
    topK=3, 
    filter={"genre": "scifi"},
    returnDistance=True,
    returnMetadata=True
)
print(json.dumps(response["vectors"], indent=2))
    