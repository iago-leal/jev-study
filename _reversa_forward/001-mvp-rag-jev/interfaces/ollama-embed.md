# Interface: Ollama embed

- **Request:** `POST http://localhost:11434/api/embed` com `{"model": "nomic-embed-text", "input": ["search_document: ...", ...]}` (até 32 itens).
- **Response:** `{"embeddings": [[float, ...], ...]}` na ordem da entrada; dimensão 768.
- **Erros:** conexão recusada → Ollama parado; HTTP 404 com "not found" → modelo ausente; outros 4xx/5xx → erro com o corpo resumido.
- **Idempotência:** sim (função pura do texto).
- **Timeout:** 60 s por lote.
