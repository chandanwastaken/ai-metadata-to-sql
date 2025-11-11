from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict
from utils import sanitize_identifier
CHROMA_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/data/chroma')
EMBED_MODEL_NAME = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
_chroma_client = None
_model = None
def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model
def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        settings = Settings(persist_directory=CHROMA_DIR)
        _chroma_client = chromadb.Client(settings=settings)
    return _chroma_client
def ensure_collection(schema: str):
    client = _get_chroma_client()
    col_name = sanitize_identifier(schema)
    try:
        return client.get_collection(col_name)
    except Exception:
        return client.create_collection(col_name)
def upsert_metadata_embeddings(schema: str, metadata_entries: List[Dict]):
    model = _get_model()
    client = _get_chroma_client()
    col = ensure_collection(schema)
    texts = [e.get('readable') or '' for e in metadata_entries]
    ids = [e.get('id') for e in metadata_entries]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    metadatas = [{k: v for k, v in e.items() if k != 'readable'} for e in metadata_entries]
    col.upsert(ids=ids, metadatas=metadatas, documents=texts, embeddings=embeddings.tolist())
    return True
def semantic_search(schema: str, query: str, k: int = 5):
    model = _get_model()
    client = _get_chroma_client()
    col = ensure_collection(schema)
    q_emb = model.encode([query], show_progress_bar=False, convert_to_numpy=True)[0].tolist()
    results = col.query(query_embeddings=[q_emb], n_results=k, include=['metadatas', 'distances', 'documents', 'ids'])
    out = []
    if results and 'ids' in results and len(results['ids'])>0:
        for i, _id in enumerate(results['ids'][0]):
            out.append({'id': _id, 'document': results['documents'][0][i], 'metadata': results['metadatas'][0][i], 'distance': results['distances'][0][i]})
    return out
