/**
 * Session handling for the admin area.
 *
 * Ένας κοινός κωδικός (ADMIN_PASSWORD) ανταλλάσσεται με ένα υπογεγραμμένο,
 * httpOnly cookie. Το cookie δεν κρατάει τίποτα εκτός από τη λήξη του και την
 * HMAC υπογραφή της — δεν υπάρχει server-side session store να συγχρονιστεί.
 *
 * Χρησιμοποιεί μόνο Web Crypto ώστε το ίδιο module να δουλεύει και στο
 * `proxy.ts` και στα route handlers.
 */

export const ADMIN_SESSION_COOKIE = "masao_admin";

const SESSION_TTL_MS = 12 * 60 * 60 * 1000;

const encoder = new TextEncoder();

function sessionSecret(): string | null {
  // Ξεχωριστό secret αν έχει οριστεί· αλλιώς ο ίδιος ο κωδικός, ώστε το setup
  // να χρειάζεται μία μόνο μεταβλητή περιβάλλοντος.
  const secret = process.env.ADMIN_SESSION_SECRET?.trim() || process.env.ADMIN_PASSWORD?.trim();
  return secret ? secret : null;
}

export function adminPassword(): string | null {
  const password = process.env.ADMIN_PASSWORD?.trim();
  return password ? password : null;
}

export function isAdminPasswordConfigured(): boolean {
  return adminPassword() !== null;
}

function base64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function sign(payload: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return base64url(await crypto.subtle.sign("HMAC", key, encoder.encode(payload)));
}

/** Compare two strings without an early exit on the first differing character. */
export function timingSafeEqual(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

export function verifyAdminPassword(candidate: string): boolean {
  const expected = adminPassword();
  if (expected === null) return false;
  return timingSafeEqual(candidate, expected);
}

export async function createSessionToken(now: number = Date.now()): Promise<string | null> {
  const secret = sessionSecret();
  if (secret === null) return null;
  const expiresAt = String(now + SESSION_TTL_MS);
  return `${expiresAt}.${await sign(expiresAt, secret)}`;
}

export async function isValidSessionToken(
  token: string | undefined,
  now: number = Date.now(),
): Promise<boolean> {
  if (!token) return false;
  const secret = sessionSecret();
  if (secret === null) return false;

  const separator = token.indexOf(".");
  if (separator <= 0) return false;

  const expiresAt = token.slice(0, separator);
  const signature = token.slice(separator + 1);
  if (!/^\d+$/.test(expiresAt)) return false;

  if (!timingSafeEqual(signature, await sign(expiresAt, secret))) return false;
  return Number(expiresAt) > now;
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_MS / 1000,
  };
}

/**
 * Keep post-login redirects inside the admin area, so a crafted `?next=`
 * cannot bounce the user to another site.
 */
export function safeNextPath(value: string | null | undefined): string {
  if (!value) return "/admin";
  if (!value.startsWith("/admin")) return "/admin";
  if (value.startsWith("//")) return "/admin";
  return value;
}
