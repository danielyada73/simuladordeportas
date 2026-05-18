import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const password = String(form.get("password") || "");
  const expected = process.env.DASHBOARD_PASSWORD || "";
  const from = String(form.get("from") || "/");

  if (!expected) {
    return NextResponse.json({ ok: false, error: "DASHBOARD_PASSWORD nao configurada" }, { status: 500 });
  }
  if (password !== expected) {
    const url = new URL("/login", req.url);
    url.searchParams.set("error", "1");
    if (from) url.searchParams.set("from", from);
    return NextResponse.redirect(url, { status: 303 });
  }

  const res = NextResponse.redirect(new URL(from || "/", req.url), { status: 303 });
  res.cookies.set("alpha_auth", expected, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30, // 30 dias
  });
  return res;
}
