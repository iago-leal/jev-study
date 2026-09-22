# Interface: Internet Archive (Wayback availability)

- **Request:** `GET https://archive.org/wayback/available?url=<url codificada>`.
- **Response:** `{"archived_snapshots": {"closest": {"available": true, "url": "http://web.archive.org/web/<ts>/<url>", "timestamp": "..."}}}`; objeto vazio quando não há snapshot.
- **Coleta do snapshot:** reescrever para `https://web.archive.org/web/<ts>id_/<url>` (conteúdo bruto, sem a barra do Wayback).
- **Erros:** timeout 30 s ou HTTP ≠ 200 → fonte `falhou` com "sem snapshot" ou o erro.
- **Idempotência:** sim.
