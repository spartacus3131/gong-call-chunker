import { NextResponse } from "next/server";

export function GET() {
  const secret = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET || "";
  return NextResponse.json({
    has_AUTH_SECRET: !!process.env.AUTH_SECRET,
    AUTH_SECRET_length: (process.env.AUTH_SECRET || "").length,
    has_NEXTAUTH_SECRET: !!process.env.NEXTAUTH_SECRET,
    NEXTAUTH_SECRET_length: (process.env.NEXTAUTH_SECRET || "").length,
    has_AUTH_GOOGLE_ID: !!process.env.AUTH_GOOGLE_ID,
    has_AUTH_GOOGLE_SECRET: !!process.env.AUTH_GOOGLE_SECRET,
    has_GOOGLE_CLIENT_ID: !!process.env.GOOGLE_CLIENT_ID,
    has_GOOGLE_CLIENT_SECRET: !!process.env.GOOGLE_CLIENT_SECRET,
    has_NEXTAUTH_URL: !!process.env.NEXTAUTH_URL,
    NEXTAUTH_URL_value: process.env.NEXTAUTH_URL || "NOT SET",
    has_VERCEL_URL: !!process.env.VERCEL_URL,
    VERCEL_URL_value: process.env.VERCEL_URL || "NOT SET",
    resolved_secret_length: secret.length,
    node_env: process.env.NODE_ENV || "NOT SET",
  });
}
