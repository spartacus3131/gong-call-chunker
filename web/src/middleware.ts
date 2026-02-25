import { NextRequest, NextResponse } from "next/server";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Allow auth routes, static files, and health checks
  if (
    pathname.startsWith("/api/auth") ||
    pathname.startsWith("/api/debug") ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api/v1") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  // Check for the session cookie (next-auth v5 uses authjs prefix)
  const hasSession =
    req.cookies.has("authjs.session-token") ||
    req.cookies.has("__Secure-authjs.session-token") ||
    req.cookies.has("next-auth.session-token") ||
    req.cookies.has("__Secure-next-auth.session-token");

  // If not authenticated, redirect to sign-in
  if (!hasSession) {
    const signInUrl = new URL("/api/auth/signin", req.url);
    signInUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
