import os
import requests
from typing import List
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'sqlcoder-34b')
def build_prompt(context_entries: List[dict], user_question: str) -> str:
    ctx_texts = []
    for e in context_entries:
        ctx_texts.append(f"- {e.get('document')}")
    ctx_block = "\n".join(ctx_texts)
    prompt = f"Schema Context:\n{ctx_block}\n\nQuestion:\n{user_question}\n\nGenerate a correct ANSI SQL query for PostgreSQL that answers the question using the schema context. Return only the SQL statement, without backticks or explanation. Use explicit schema.table references when possible. Limit results to reasonable rows if applicable (e.g., LIMIT 100). Do not run destructive statements."
    return prompt
def call_ollama_generate(prompt: str, model: str = None, max_tokens: int = 512) -> str:
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_URL}/api/generate"
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": 0.0}
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and 'choices' in data:
        content = data['choices'][0].get('message', {}).get('content')
        if content:
            return content.strip()
    if isinstance(data, dict) and 'text' in data:
        return data['text'].strip()
    return str(data)
def generate_sql_from_context(context_entries: List[dict], user_question: str) -> str:
    prompt = build_prompt(context_entries, user_question)
    sql = call_ollama_generate(prompt)
    if '\n' in sql:
        s = sql.strip()
        for keyword in ['SELECT', 'WITH', 'SHOW', 'EXPLAIN', 'INSERT']:
            idx = s.upper().find(keyword)
            if idx >= 0:
                return s[idx:]
    return sql
