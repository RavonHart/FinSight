# Frontend Architecture

FinSight frontend is built using Next.js App Router, TypeScript, React Hook Form, Zod, and Tailwind CSS with shadcn/ui.

## Principles
1. **Pure Presentation**: No financial calculations or business logic in React components.
2. **Real-Time Visibility**: Server-Sent Events (SSE) stream agent execution progress and structured assessment generation.
3. **Resilience & State Management**: TanStack Query handles caching, stale-while-revalidate, and offline reconnection.
4. **UX States**: Every screen implements Loading, Empty, Error, Success, and Partial Result states.
