const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

/**
 * Derives a URL-safe slug from a company name for use as a run ID.
 *
 * NOTE: The backend does not yet have a POST /api/runs endpoint.
 * Right now the slug is generated client-side and company + ticker
 * are passed as query params. In M3 this will POST to /api/runs and
 * receive a real run_id from the backend.
 */
export function createRunSlug(company: string): string {
  return company
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

/** URL of the backend SSE stream for a given company + ticker. */
export function buildStreamUrl(company: string, ticker: string): string {
  const params = new URLSearchParams({ company, ticker });
  return `${BACKEND_URL}/api/runs/stream?${params}`;
}

export { BACKEND_URL };
