# Security & Authorization Model

## Multi-Tenancy Isolation
1. **Application Layer**: FastAPI dependencies extract `current_user` from the verified JWT. Repositories enforce ownership `WHERE user_id = :current_user_id`.
2. **Database Layer (RLS)**: Row-Level Security policies filter rows by session user variable `app.current_user_id`.
3. **AI Security**:
   - Untrusted documents and external web pages are sanitized.
   - LLMs and Agents cannot invoke arbitrary tools or write to financial ledgers directly.
   - Bounded tool execution budgets (`MAX_TOOL_CALLS`, `MAX_RESEARCH_ITERATIONS`).
   - Hard cost ceilings per user and per run.
