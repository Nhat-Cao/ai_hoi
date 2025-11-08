from openai import AzureOpenAI
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import os

load_dotenv()
def is_env_missing(var):
    v = os.getenv(var)
    return v is None or v.strip() == ""

if (
    is_env_missing("AZURE_OPENAI_ENDPOINT") or
    is_env_missing("AZURE_OPENAI_EMBEDDING_API_KEY") or
    is_env_missing("AZURE_OPENAI_EMBEDDING_MODEL_NAME") or
    is_env_missing("PINECONE_DB_API_KEY")
):
    raise ValueError("Please set your environment variables.")

embedding_client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
)
pc = Pinecone(api_key=os.getenv("PINECONE_DB_API_KEY"))

index_name = "ai-hoi"

# Create index if it doesn't exist
if index_name not in [index["name"] for index in pc.list_indexes()]:
    pc.create_index(name=index_name, dimension=1536, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))

index = pc.Index(index_name)

def get_embedding(text):
    response = embedding_client.embeddings.create(
        input=text,
        model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")
    )
    return response.data[0].embedding

# Upsert embeddings into Pinecone
def upsert_data(text, namespace):
    try:
        embedding = get_embedding(text)
        # Create vector with ID and metadata
        vector = {
            'id': str(hash(text)),  # Create a unique ID for the vector
            'values': embedding,
            'metadata': {'text': text}
        }
        # Upsert to specified namespace
        index.upsert(vectors=[vector], namespace=namespace)
        return True
    except Exception as e:
        print(f"Error upserting data: {e}")
        return False
    
def query_data(query_text, top_k=5, namespace=None):
    try:
        query_embedding = get_embedding(query_text)
        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )
        # Extract and return only the text from metadata
        results = []
        for match in response['matches']:
            if match['metadata'] and 'text' in match['metadata']:
                results.append(match['metadata']['text'])
        return results
    except Exception as e:
        print(f"Error querying data: {e}")
        return []