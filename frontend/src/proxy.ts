import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { ADMIN_SESSION_COOKIE, isValidSessionToken } from "@/lib/admin-auth";

/** Routes that must stay reachable without a session, or nobody could log in. */
const PUBLIC_PATHS = new Set(["/admin/login", "/api/admin/login", "/api/admin/logout"]);

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isAuthenticated = await isValidSessionToken(
    request.cookies.get(ADMIN_SESSION_COOKIE)?.value,
  );

  if (PUBLIC_PATHS.has(pathname)) {
    if (pathname === "/admin/login" && isAuthenticated) {
      return NextResponse.redirect(new URL("/admin", request.url));
    }
    return NextResponse.next();
  }

  if (isAuthenticated) return NextResponse.next();

  // Το UI κάνει fetch στο /api/admin/*: απάντησε με 401 αντί για redirect,
  // ώστε ο client να δείξει καθαρό μήνυμα και να στείλει στο login.
  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ detail: "Admin session required" }, { status: 401 });
  }

  const loginUrl = new URL("/admin/login", request.url);
  if (pathname !== "/admin") loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/admin/:path*", "/api/admin/:path*"],
};
