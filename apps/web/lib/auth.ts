export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string | null;
  auth_provider: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

const TOKEN_KEY = "finsight_access_token";
const REFRESH_KEY = "finsight_refresh_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredTokens(accessToken: string, refreshToken: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearStoredTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

/**
 * Safely extracts human-readable message from FastAPI errors (string, 422 list of error objects, dict).
 */
export function formatErrorDetail(detail: any): string {
  if (!detail) return "An unexpected error occurred.";
  if (typeof detail === "string") return detail;
  
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : "";
          const msg = item.msg || item.message || JSON.stringify(item);
          return field && field !== "body" ? `${field}: ${msg}` : msg;
        }
        return String(item);
      })
      .filter(Boolean)
      .join("; ");
  }

  if (typeof detail === "object") {
    if (detail.detail) return formatErrorDetail(detail.detail);
    if (detail.message) return String(detail.message);
    if (detail.msg) return String(detail.msg);
    if (detail.error) return String(detail.error);
    try {
      return JSON.stringify(detail);
    } catch {
      return "An unexpected error occurred.";
    }
  }

  return String(detail);
}

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    // When executing in user browser:
    // If NEXT_PUBLIC_API_URL is configured and not internal docker hostname 'api', use it.
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl && !envUrl.includes("://api:") && !envUrl.includes("://api/")) {
      return envUrl;
    }
    const host = window.location.hostname || "localhost";
    return `http://${host}:8000`;
  }
  // Server-side rendering inside node/docker
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(`${getApiBase()}${endpoint}`, {
    ...options,
    headers,
  });
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  let res: Response;
  const apiBase = getApiBase();

  try {
    res = await fetch(`${apiBase}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    });
  } catch (err: any) {
    throw new Error(
      `Unable to reach backend API at ${apiBase}. Please ensure the server is running.`
    );
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    const detail = errorData ? (errorData.detail ?? errorData.message ?? errorData) : null;
    throw new Error(formatErrorDetail(detail) || `Authentication failed (Status ${res.status})`);
  }

  const data: AuthResponse = await res.json();
  setStoredTokens(data.access_token, data.refresh_token);
  return data;
}

export async function signupUser(email: string, password: string, name: string): Promise<AuthResponse> {
  let res: Response;
  const apiBase = getApiBase();

  try {
    res = await fetch(`${apiBase}/api/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email.trim().toLowerCase(),
        password,
        name: name.trim(),
      }),
    });
  } catch (err: any) {
    throw new Error(
      `Unable to reach backend API at ${apiBase}. Please ensure the server is running.`
    );
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    const detail = errorData ? (errorData.detail ?? errorData.message ?? errorData) : null;
    throw new Error(formatErrorDetail(detail) || `Registration failed (Status ${res.status})`);
  }

  const data: AuthResponse = await res.json();
  setStoredTokens(data.access_token, data.refresh_token);
  return data;
}

export async function getCurrentUser(): Promise<User | null> {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const res = await fetchWithAuth("/api/v1/auth/me");
    if (!res.ok) {
      clearStoredTokens();
      return null;
    }
    return await res.json();
  } catch {
    return null;
  }
}

export async function logoutUser(): Promise<void> {
  try {
    await fetchWithAuth("/api/v1/auth/logout", { method: "POST" });
  } finally {
    clearStoredTokens();
  }
}
