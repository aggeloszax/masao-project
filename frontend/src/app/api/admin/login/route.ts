import { NextResponse } from "next/server";
import {
  ADMIN_SESSION_COOKIE,
  createSessionToken,
  isAdminPasswordConfigured,
  sessionCookieOptions,
  verifyAdminPassword,
} from "@/lib/admin-auth";

const ATTEMPT_LIMIT = 10;
const ATTEMPT_WINDOW_MS = 15 * 60 * 1000;

// Best effort ανά instance: δεν αντικαθιστά σωστό WAF, αλλά κόβει το απλό
// brute force πάνω σε έναν κοινό κωδικό.
const attempts = new Map<string, { count: number; resetAt: number }>();

function clientKey(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  return forwarded?.split(",")[0]?.trim() || "unknown";
}

function isRateLimited(key: string, now: number): boolean {
  const entry = attempts.get(key);
  if (entry === undefined || entry.resetAt <= now) return false;
  return entry.count >= ATTEMPT_LIMIT;
}

function recordFailure(key: string, now: number): void {
  const entry = attempts.get(key);
  if (entry === undefined || entry.resetAt <= now) {
    attempts.set(key, { count: 1, resetAt: now + ATTEMPT_WINDOW_MS });
    return;
  }
  entry.count += 1;
}

export async function POST(request: Request): Promise<Response> {
  if (!isAdminPasswordConfigured()) {
    return NextResponse.json(
      { detail: "Ο διαχειριστικός κωδικός δεν έχει ρυθμιστεί (ADMIN_PASSWORD)" },
      { status: 503 },
    );
  }

  const now = Date.now();
  const key = clientKey(request);
  if (isRateLimited(key, now)) {
    return NextResponse.json(
      { detail: "Πολλές αποτυχημένες προσπάθειες. Δοκιμάστε ξανά σε λίγο." },
      { status: 429 },
    );
  }

  let password = "";
  try {
    const body: unknown = await request.json();
    if (body !== null && typeof body === "object" && "password" in body) {
      const value = (body as { password: unknown }).password;
      if (typeof value === "string") password = value;
    }
  } catch {
    password = "";
  }

  if (!verifyAdminPassword(password)) {
    recordFailure(key, now);
    return NextResponse.json({ detail: "Λάθος κωδικός" }, { status: 401 });
  }

  const token = await createSessionToken(now);
  if (token === null) {
    return NextResponse.json({ detail: "Δεν ήταν δυνατή η δημιουργία συνεδρίας" }, { status: 503 });
  }

  attempts.delete(key);
  const response = NextResponse.json({ ok: true });
  response.cookies.set(ADMIN_SESSION_COOKIE, token, sessionCookieOptions());
  return response;
}
