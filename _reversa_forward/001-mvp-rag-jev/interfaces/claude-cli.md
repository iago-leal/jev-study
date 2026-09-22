# Interface: Claude Code CLI (processo)

- **Invocação:** `claude -p --tools "" --no-session-persistence --output-format text --model <alias> --system-prompt <instruções>`; contexto e pergunta pela entrada padrão; cwd = diretório temporário.
- **Resposta:** texto em stdout; código 0 em sucesso.
- **Erros:** `FileNotFoundError` → CLI ausente; código ≠ 0 → stderr resumido (limite de uso da assinatura é detectado por "limit" no stderr/stdout); timeout de 180 s.
- **Autenticação:** a do usuário (OAuth da assinatura); nenhuma chave de API.
- **Idempotência:** não (geração estocástica); cada chamada consome cota.
