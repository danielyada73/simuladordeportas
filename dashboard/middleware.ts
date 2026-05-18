import { NextRequest, NextResponse } from "next/server";

// Auth basica simples: cookie "alpha_auth" tem que bater com hash do DASHBOARD_PASSWORD.
// Em /login, o usuario insere senha; se bater, seta cookie.
// Tudo fora de /login e /api/login exige cookie.

const PUBLIC_PATHS = ["/login", "/api/login", "/_next", "/favicon.ico"];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) return NextResponse.next();

  // Acesso individual do cliente via token na URL: /cliente/[token]
  if (pathname.startsWith("/cliente/")) return NextResponse.next();

  const auth = req.cookies.get("alpha_auth")?.value;
  const expected = process.env.DASHBOARD_PASSWORD;
  if (!expected || auth !== expected) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
