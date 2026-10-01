import { NextResponse } from "next/server";
import { ADMIN_SESSION_COOKIE, sessionCookieOptions } from "@/lib/admin-auth";

export async function POST(): Promise<Response> {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(ADMIN_SESSION_COOKIE, "", { ...sessionCookieOptions(), maxAge: 0 });
  return response;
}
