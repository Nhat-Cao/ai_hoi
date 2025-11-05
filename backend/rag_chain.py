import os
from typing import Optional, List

from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone


load_dotenv()


class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        arr = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        return [v.tolist() for v in arr]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


def _select_embeddings() -> Embeddings:
    provider = os.getenv("RAG_PROVIDER", "auto")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-01-preview")
    azure_emb = os.getenv("AZURE_OPENAI_EMBEDDINGS_MODEL")
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
    local_model = os.getenv("LOCAL_EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    if provider == "auto":
        if endpoint and api_key and azure_emb:
            provider = "azure"
        elif openai_key:
            provider = "openai"
        else:
            provider = "local"

    if provider == "azure":
        return AzureOpenAIEmbeddings(
            azure_deployment=azure_emb,
            openai_api_version=api_version,
            api_key=api_key,
            azure_endpoint=endpoint,
        )
    if provider == "openai":
        return OpenAIEmbeddings(model=openai_model, api_key=openai_key)
    return LocalEmbeddings(local_model)


def _select_llm():
    provider = os.getenv("RAG_PROVIDER", "auto")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-01-preview")
    azure_chat = os.getenv("AZURE_OPENAI_MODEL_NAME")
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_chat = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    if provider == "auto":
        if endpoint and api_key and azure_chat:
            provider = "azure"
        elif openai_key:
            provider = "openai"
        else:
            # Default to local-like small OpenAI model name but will likely fail without key
            provider = "openai"

    if provider == "azure":
        return AzureChatOpenAI(
            azure_deployment=azure_chat,
            openai_api_version=api_version,
            api_key=api_key,
            azure_endpoint=endpoint,
            temperature=0.2,
        )
    return ChatOpenAI(model=openai_chat, api_key=openai_key, temperature=0.2)


def rag_chat(query: str, namespace: Optional[str] = None, k: int = 4) -> str:
    # Ensure Pinecone client
    if not os.getenv("PINECONE_INDEX"):
        raise RuntimeError("PINECONE_INDEX is not set")
    if not os.getenv("PINECONE_API_KEY"):
        raise RuntimeError("PINECONE_API_KEY is not set")
    Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    embeddings = _select_embeddings()
    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX"),
        embedding=embeddings,
        namespace=namespace,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    docs: List[Document] = retriever.invoke(query)
    context = "\n\n".join([d.page_content for d in docs])

    system_prompt = (
        "You are a helpful Vietnamese assistant. Use the provided context to answer. "
        "If the answer isn't in the context, say you don't know. Always answer in Vietnamese."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Context:\n{context}\n\nCâu hỏi: {question}"),
    ])
    messages = prompt.format_messages(context=context, question=query)

    llm = _select_llm()
    resp = llm.invoke(messages)
    return resp.content.strip()


