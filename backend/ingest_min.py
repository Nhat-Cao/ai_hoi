import argparse
import json
import os
from typing import List, Dict, Any, Optional
import time

from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone


def read_jsonl(
    file_path: str,
    text_fields: Optional[List[str]] = None,
    text_field: str = "text",
    metadata_field: str = "metadata",
) -> (List[str], List[Dict[str, Any]]):
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            text: Optional[str] = None
            if text_fields:
                parts: List[str] = []
                for k in text_fields:
                    v = obj.get(k)
                    if isinstance(v, (str, int, float)):
                        parts.append(f"{k}: {v}")
                if parts:
                    text = "\n".join(parts)
            if text is None:
                text = obj.get(text_field) or obj.get("content") or obj.get("page_content")
            if not text:
                continue
            meta = obj.get(metadata_field)
            if not isinstance(meta, dict):
                meta = {}
                exclude = set(text_fields or []) | {text_field}
                for k, v in obj.items():
                    if k in exclude:
                        continue
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        meta[k] = v
            texts.append(str(text))
            metadatas.append(meta)
    return texts, metadatas


def chunk(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest JSONL -> Embeddings (Azure | OpenAI | Local) -> Pinecone")
    parser.add_argument("--file", required=True, help="Path to .jsonl file")
    parser.add_argument(
        "--text-fields",
        required=False,
        help="Comma-separated fields to compose text (e.g., 'ten_mon,dac_diem,khau_vi')",
    )
    parser.add_argument("--namespace", required=False, default=None, help="Pinecone namespace")
    parser.add_argument("--provider", required=False, choices=["auto", "azure", "openai", "local"], default="auto", help="Embedding provider (default: auto)")
    parser.add_argument("--local-model", required=False, default="sentence-transformers/all-MiniLM-L6-v2", help="Local sentence-transformers model (default: all-MiniLM-L6-v2)")
    parser.add_argument("--batch-size", required=False, type=int, default=32, help="Batch size for embedding requests (default: 32)")
    args = parser.parse_args()

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-01-preview")
    emb_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_MODEL")
    # OpenAI fallback
    oai_key = os.getenv("OPENAI_API_KEY")
    oai_model = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX")

    # Determine provider
    provider = args.provider
    if provider == "auto":
        provider = "azure" if (endpoint and api_key and emb_deployment) else ("openai" if oai_key else "local")
    if provider is None:
        raise RuntimeError("No embedding provider configured. Set Azure vars or OPENAI_API_KEY.")

    if not pinecone_key or not index_name:
        raise RuntimeError("Missing Pinecone config. Set PINECONE_API_KEY and PINECONE_INDEX.")

    text_fields = None
    if args.text_fields:
        text_fields = [s.strip() for s in args.text_fields.split(",") if s.strip()]

    texts, metas = read_jsonl(args.file, text_fields=text_fields)
    if not texts:
        print("No records found in the file.")
        return

    # Init embedding client per provider
    azure_client = None
    oai_client = None
    local_model = None
    if provider == "azure":
        azure_client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version=api_version)
    elif provider == "openai":
        oai_client = OpenAI(api_key=oai_key)
    else:
        # Local sentence-transformers
        local_model = SentenceTransformer(args.local_model)
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(index_name)

    batch_size = max(1, int(args.batch_size))
    total = 0
    pairs = list(zip(texts, metas))
    for i, b in enumerate(chunk(pairs, batch_size)):
        batch_texts = [t for t, _ in b]
        batch_meta = [m for _, m in b]
        vectors = []
        if provider == "azure":
            # Simple retry for throttling
            for attempt in range(5):
                try:
                    emb = azure_client.embeddings.create(model=emb_deployment, input=batch_texts)
                    break
                except Exception as e:
                    if attempt == 4:
                        raise
                    time.sleep(2 * (attempt + 1))
            for j, d in enumerate(emb.data):
                vectors.append({
                    "id": f"doc-{total+j}",
                    "values": d.embedding,
                    "metadata": batch_meta[j]
                })
        elif provider == "openai":
            for attempt in range(5):
                try:
                    emb = oai_client.embeddings.create(model=oai_model, input=batch_texts)
                    break
                except Exception as e:
                    if attempt == 4:
                        raise
                    time.sleep(2 * (attempt + 1))
            for j, d in enumerate(emb.data):
                vectors.append({
                    "id": f"doc-{total+j}",
                    "values": d.embedding,
                    "metadata": batch_meta[j]
                })
        else:
            # Local embeddings
            arr = local_model.encode(batch_texts, convert_to_numpy=True, normalize_embeddings=False)
            for j in range(arr.shape[0]):
                vectors.append({
                    "id": f"doc-{total+j}",
                    "values": arr[j].tolist(),
                    "metadata": batch_meta[j]
                })
        index.upsert(vectors=vectors, namespace=args.namespace)
        total += len(b)
        print(f"Upserted batch {i+1} with {len(b)} records")

    print(f"Done. Total upserted: {total}")


if __name__ == "__main__":
    main()


